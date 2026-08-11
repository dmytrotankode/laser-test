"""Шаг 9: проверка диагноза - если добрать библиотеку по высоте, станет ли лучше?

Диагноз из s13: все шесть шлемов подняты выше всего, что есть в библиотеке
(Z до 3.24 мм при библиотечном диапазоне 0-1.25, sigma 0.32), и модель, не умея
выразить высоту, выливает её в X и Y. Если это верно, то добавление в библиотеку
поз с настоящей высотой обязано резко улучшить предсказание остальных.

Разбиение задано ФОРМАЛЬНО и до просмотра результата - через один, по порядку
съёмки: в библиотеку v20, v22, v24, на проверку v21, v23, v25. Так обе формы
попадают и туда и туда (форма 4 - это v22 и v23), и обе половины покрывают весь
день съёмки. Выбирать по величине ошибки было бы подгонкой.

Сравниваются на ОДНИХ И ТЕХ ЖЕ трёх проверочных вариантах:
  нынешняя библиотека        14 обучающих;
  + три новых               17, из них три с высотой 1.6-2.5 мм.

Оценка - тем же способом, что LOO в fit_model: контур выбранного соседа двигается
предсказанной поправкой и меряется до истинной линии реза.
"""
import os
import sys
import json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import fit_model   # noqa: E402
import features    # noqa: E402
import lsgeom      # noqa: E402
import dataset     # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MODEL = json.load(open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8'))
PIVOT, LAM, KIND = np.array(MODEL['pivot']), MODEL['lam'], MODEL['feature_kind']
ANCHOR = MODEL['anchor']

ADD = ['v20', 'v22', 'v24']
TEST = ['v21', 'v23', 'v25']
BASE_TR = list(dataset.TRAIN)

F = features.load(BASE_TR + ADD + TEST)
for v in BASE_TR + ADD + TEST:
    fit_model.transform_from_ref(v, ANCHOR)


def poses(names):
    return {(x, y): fit_model.pose_between(x, y, PIVOT, ANCHOR)
            for x in names for y in names if x != y}


def run(train, tests):
    P = poses(train)
    W, sx = fit_pairs_cached(train, P)
    out = {}
    for v in tests:
        nb = fit_model.nearest(v, train, F, KIND)
        p = fit_model.predict(W, sx, F, KIND, nb, v)
        G = fit_model.contour(v)
        moved = fit_model.apply_pose(fit_model.contour(nb), p, PIVOT)
        d = lsgeom.curve_distance(moved, G)
        raw = lsgeom.curve_distance(fit_model.contour(nb), G)
        out[v] = dict(nb=nb, mean=float(d.mean()), mx=float(d.max()),
                      within=float((d <= 2.0).mean() * 100),
                      raw_mean=float(raw.mean()),
                      pred_z=float(p[2]),
                      true_z=float(fit_model.pose_between(nb, v, PIVOT, ANCHOR)[2]))
    return out


_cache = {}


def fit_pairs_cached(train, P):
    k = tuple(train)
    if k not in _cache:
        _cache[k] = fit_model.fit_pairs(train, F, KIND, LAM, P)
    return _cache[k]


base = run(BASE_TR, TEST)
aug = run(BASE_TR + ADD, TEST)

print()
print("Проверка на v21, v23, v25 (в обучении не участвуют ни в одном из вариантов)")
print("=" * 80)
print(f"{'':<7}{'опора':>7}{'сосед как есть':>17}{'модель на 14':>15}"
      f"{'модель на 17':>15}{'≤2мм 14→17':>14}")
print("-" * 80)
for v in TEST:
    b, a = base[v], aug[v]
    print(f"{v:<7}{b['nb']:>7}{b['raw_mean']:>17.2f}{b['mean']:>15.2f}"
          f"{a['mean']:>15.2f}{b['within']:>8.0f}%→{a['within']:.0f}%")
print("-" * 80)
print(f"{'среднее':<7}{'':>7}{np.mean([base[v]['raw_mean'] for v in TEST]):>17.2f}"
      f"{np.mean([base[v]['mean'] for v in TEST]):>15.2f}"
      f"{np.mean([aug[v]['mean'] for v in TEST]):>15.2f}")
print(f"{'худший':<7}{'':>7}{max(base[v]['raw_mean'] for v in TEST):>17.2f}"
      f"{max(base[v]['mx'] for v in TEST):>15.2f}"
      f"{max(aug[v]['mx'] for v in TEST):>15.2f}")

print()
print("Высота: научилась ли модель её видеть (мм)")
print(f"{'':<7}{'истина':>9}{'на 14':>9}{'на 17':>9}")
for v in TEST:
    print(f"{v:<7}{base[v]['true_z']:>9.2f}{base[v]['pred_z']:>9.2f}"
          f"{aug[v]['pred_z']:>9.2f}")

print()
print("Контроль: не испортилось ли на прежних данных (LOO внутри TRAIN)")
P14 = poses(BASE_TR)
per = fit_model.loo_error(BASE_TR, F, KIND, LAM, P14, PIVOT)
print(f"  библиотека 14, LOO = {np.mean([per[v]['nearest'] for v in BASE_TR]):.2f} мм "
      f"(эталон 1.23)")
P17 = poses(BASE_TR + ADD)
per17 = fit_model.loo_error(BASE_TR + ADD, F, KIND, LAM, P17, PIVOT)
old = [per17[v]['nearest'] for v in BASE_TR]
print(f"  библиотека 17, LOO на тех же 14 = {np.mean(old):.2f} мм")
