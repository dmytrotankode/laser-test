"""А если опустить отсечку маски и захватить уши?

Сейчас у боковых видов маска обрезается на 58 % высоты силуэта, и линия сгиба
лежит целиком ниже - в признаки не попадает вообще. Заказчик заметил, что на
`back` до бахромы юбки ещё далеко, то есть опустить есть куда.

Подвох в самом правиле: 58 % считаются от высоты силуэта, а низ силуэта - это
край необрезанной юбки, который гуляет между шлемами на 27-153 px. Чем ниже
опускаем, тем сильнее сама граница пляшет от того, как обрезали. Поэтому здесь
проверяется не «доля побольше», а `abs_y` - фиксированная СТРОКА КАДРА. Камеры
прикручены, строка кадра есть фиксированная плоскость в пространстве, и юбка её
не двигает.

Опыт ничего не ломает: признаки считаются своей копией кода, кэш лежит в
service_3030/data, кэш и константы 5056 не трогаются. Базовая линия считается
ТЕМ ЖЕ кодом с нынешним правилом - иначе разница мерила бы разницу кода.
"""
import os
import sys
import json
import types
import numpy as np
import cv2

BASE = os.path.dirname(os.path.abspath(__file__))
S5056 = os.path.abspath(os.path.join(BASE, '..', 'service_5056'))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(S5056, 'scripts'))

import dataset                                           # noqa: E402
import features as feat5056                              # noqa: E402
import fit_model                                         # noqa: E402
from step03_segment_monochrome import segment_image      # noqa: E402
from shots import img_path                               # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

N_BINS = 48
CACHE = os.path.join(BASE, 'data', 'feat_cutoff.json')
# строки кадра для отсечки; None = нынешнее правило (58 % высоты силуэта)
LEVELS = [
    ('нынешнее правило 58%', None, None),
    ('строка 1290 / 1610 (та же высота)', 1290, 1610),
    ('строка 1400 / 1750', 1400, 1750),
    ('строка 1550 / 1900', 1550, 1900),
    ('строка 1700 / 2050', 1700, 2050),
]


def measure(variant, ab, al):
    prof = []
    for name, is_top in (("back", False), ("left", False), ("top", True)):
        cut = None if is_top else (ab if name == 'back' else al)
        mask, _, _, _, _ = segment_image(img_path(variant, name), is_top, abs_y=cut)
        M = cv2.moments(mask)
        cx, cy = M["m10"] / M["m00"], M["m01"] / M["m00"]
        c = max(cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0],
                key=cv2.contourArea)[:, 0, :].astype(float)
        ang = np.arctan2(c[:, 1] - cy, c[:, 0] - cx)
        rad = np.hypot(c[:, 0] - cx, c[:, 1] - cy)
        o = np.argsort(ang)
        grid = np.linspace(-np.pi, np.pi, N_BINS, endpoint=False)
        prof.append([cx, cy] + list(np.interp(grid, ang[o], rad[o], period=2 * np.pi)))
    return prof


def main():
    names = [v for v in dataset.guard_training(dataset.TRAIN)]
    cache = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}
    piv = np.array([1170.98, 785.15, -191.86])
    ref = names[0]
    for v in names:
        fit_model.transform_from_ref(v, ref)
    POSE = {(x, y): fit_model.pose_between(x, y, piv, ref)
            for x in names for y in names if x != y}
    fit_model.features = types.SimpleNamespace(
        vec=lambda e, k: np.array([x for row in e["prof"] for x in row], float),
        load=feat5056.load)

    print(f"{'отсечка':<24}{'LOO ближ.':>11}{'LOO худш.':>11}")
    for label, ab, al in LEVELS:
        F = {}
        for v in names:
            key = f'{v}|{ab}|{al}'
            if key not in cache:
                cache[key] = measure(v, ab, al)
                json.dump(cache, open(CACHE, 'w'))
            F[v] = {"prof": cache[key]}
        best = None
        for lam in (10, 100, 1000):
            per = fit_model.loo_error(names, F, 'prof', lam, POSE, piv)
            m = float(np.mean([r['nearest'] for r in per.values()]))
            w = float(np.max([r['nearest'] for r in per.values()]))
            if best is None or m < best[0]:
                best = (m, w, lam)
        print(f'{label:<24}{best[0]:>11.2f}{best[1]:>11.2f}   (lambda {best[2]})',
              flush=True)


if __name__ == '__main__':
    main()
