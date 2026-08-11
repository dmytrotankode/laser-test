"""Тест A2: видит ли силуэт высоту на НАСТОЯЩИХ фотографиях.

Синтетика (t1) показала верхнюю границу: высота восстанавливается с точностью
0.01 мм, то есть сигнал в силуэте есть и он сильный. Здесь добавляется то, чего
в синтетике не было - расхождение CAD-меша с реальной деталью (~1.2 мм по
прошлым замерам). Вопрос: переживает ли сигнал этот фон.

Оптимизатор с ЯВНЫМ стартовым симплексом и посевом, расширенным по Z: на штатных
настройках (b3_pose.py:135) высота искалась бы только в коробке библиотеки
[0, 1.25] мм, а истинные значения доходят до 3.24.

Правильная мера успеха здесь - НЕ абсолютная точность. Постоянное смещение
(если CAD systematically выше или ниже детали) снимается одной константой и
ничему не мешает. Мера - СЛЕДУЕТ ЛИ найденная высота за истинной: наклон
регрессии найденный~истинный. Наклон около 1 означает, что метод меряет высоту;
наклон около 0 - что он её не видит, как бы близко ни лежали абсолютные числа.

Обязательный контроль - разброс найденных поз. В прошлой сессии подгонка
сползала в одно и то же место независимо от снимка (v6 и цех дали почти
одинаковый ответ), и это выглядело как работающий метод.
"""
import os
import sys
import json
import numpy as np
import cv2
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
PHYS = os.path.join(BASE, 'scratch', 'phys')
sys.path.insert(0, HERE)
sys.path.insert(0, PHYS)
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import render as R      # noqa: E402
import fit_model        # noqa: E402
import dataset          # noqa: E402
from t1_zsense import (CAM, VIEWS, COARSE, MM_PER_PX, gap, render,   # noqa: E402
                       lo, hi, STEP, simplex, A1, LIB)
from step03_segment_monochrome import segment_image                  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MODEL = json.load(open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8'))
PIVOT, ANCHOR = np.array(MODEL['pivot']), MODEL['anchor']
MASKDIR = os.path.join(HERE, 't2_masks')
os.makedirs(MASKDIR, exist_ok=True)
CASES = dataset.BLIND + ['v6', 'v13']


def masks_of(v):
    out = {}
    for view in VIEWS:
        cache = os.path.join(MASKDIR, f'{v}_{view}.png')
        if not os.path.exists(cache):
            m, _, _, _, b = segment_image(
                os.path.join(BASE, 'input', 'archive', v, f'{view}.png'),
                view == 'top')
            assert b != 'otsu', f'{v}/{view}'
            cv2.imwrite(cache, m)
        m = cv2.imread(cache, cv2.IMREAD_GRAYSCALE)
        w, h = int(4096 * COARSE), int(3000 * COARSE)
        m = cv2.resize(m, (w, h), interpolation=cv2.INTER_NEAREST)
        rows = np.where(m.max(1) > 0)[0]
        cut = int(rows.max()) + 1 if len(rows) else None
        out[view] = (m, cut if cut and cut < h - 1 else None)
    return out


def cost_photo(mk):
    def f(v6):
        Rm, tm = None, None
        from t1_zsense import pose_to_mesh
        Rm, tm = pose_to_mesh(v6)
        tot = []
        for view in VIEWS:
            m, cut = mk[view]
            s = CAM[view].silhouette(pose_R=Rm, pose_t=tm, cutoff_row=cut)
            if np.count_nonzero(s) < 50:
                return 1e3
            tot.append(gap(s, m))
        return float(np.mean(tot))
    return f


def fit_photo(mk, seed=11):
    f = cost_photo(mk)
    best = (f(A1), A1.copy())
    rng = np.random.default_rng(seed)
    for _ in range(30):
        s = lo + rng.random(6) * (hi - lo)
        v = f(s)
        if v < best[0]:
            best = (v, s)
    for _ in range(6):
        r = minimize(f, best[1], method='Nelder-Mead',
                     options=dict(maxiter=2500, xatol=1e-3, fatol=1e-4,
                                  initial_simplex=simplex(best[1])))
        if r.fun >= best[0] - 1e-5:
            break
        best = (r.fun, r.x)
    return best


for v in CASES:
    fit_model.transform_from_ref(v, ANCHOR)
TRUE = {v: fit_model.pose_between(ANCHOR, v, PIVOT, ANCHOR) for v in CASES}

print()
print("Подгонка силуэта по трём фото, высота против истинной (мм)")
print("=" * 78)
print(f"{'':<7}{'истинный Z':>12}{'найденный Z':>13}{'промах':>9}"
      f"{'невязка':>10}{'найденный X':>13}{'истинный X':>12}")
print("-" * 78)
rows = {}
for v in CASES:
    res, vec = fit_photo(masks_of(v))
    rows[v] = dict(vec=[float(x) for x in vec], res=float(res * MM_PER_PX))
    t = TRUE[v]
    print(f"{v:<7}{t[2]:>12.2f}{vec[2]:>13.2f}{vec[2] - t[2]:>9.2f}"
          f"{res * MM_PER_PX:>10.3f}{vec[0]:>13.2f}{t[0]:>12.2f}", flush=True)

json.dump(rows, open(os.path.join(HERE, 't2_results.json'), 'w'), indent=1)

zt = np.array([TRUE[v][2] for v in CASES])
zf = np.array([rows[v]['vec'][2] for v in CASES])
k, b = np.polyfit(zt, zf, 1)
print("-" * 78)
print(f"наклон регрессии найденный~истинный: {k:+.2f}  (1.0 = меряет высоту, "
      f"0.0 = слепа)")
print(f"корреляция: {np.corrcoef(zt, zf)[0, 1]:+.2f}")
print(f"остаток после снятия постоянного смещения: "
      f"{np.std(zf - (k * zt + b)):.2f} мм")
print(f"систематическое смещение: {np.mean(zf - zt):+.2f} мм")

print()
print("Контроль сползания: разброс найденных поз против истинного")
for k2, name in enumerate(('X', 'Y', 'Z', 'roll', 'pitch', 'yaw')):
    tf = np.array([TRUE[v][k2] for v in CASES])
    ff = np.array([rows[v]['vec'][k2] for v in CASES])
    print(f"  {name:<6} истинный разброс {tf.std():>6.2f}, найденный {ff.std():>6.2f}, "
          f"корреляция {np.corrcoef(tf, ff)[0, 1]:+.2f}")
