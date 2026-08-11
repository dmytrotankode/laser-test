"""Тест C: какая ось на самом деле держит ошибку.

Гибрид (t3) починил высоту и почти ничего не дал: 5.26 -> 5.13. Значит Z не был
главным вкладом, хотя промах по нему и достигал 2 мм. Дальше гадать не нужно -
вклад каждой оси измеряется прямо.

Способ: берём предсказание пайплайна и заменяем ОДНУ компоненту на истинную,
оставляя остальные как есть. Насколько упала ошибка - таков вклад этой оси. С
подсматриванием ответа, поэтому это диагностика, а не метод.

Рядом обратная величина: что будет, если ВСЁ истинное, кроме одной оси. Первая
таблица отвечает "сколько выиграем, починив ось", вторая - "сколько теряем,
испортив только её".
"""
import os
import sys
import json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import fit_model   # noqa: E402
import lsgeom      # noqa: E402
import dataset     # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MODEL = json.load(open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8'))
PIVOT, ANCHOR = np.array(MODEL['pivot']), MODEL['anchor']
SESS = json.load(open(os.path.join(HERE, 's6_sessions.json')))
SESS['v20'] = 'run_20260810_125404'
AXES = ('X', 'Y', 'Z', 'roll', 'pitch', 'yaw')

for v in dataset.BLIND + list(MODEL['library']):
    fit_model.transform_from_ref(v, ANCHOR)


def err(pred, nb, v):
    return float(lsgeom.curve_distance(
        fit_model.apply_pose(fit_model.contour(nb), pred, PIVOT),
        fit_model.contour(v)).mean())


fix, spoil, base, ceil = {}, {}, {}, {}
for v in dataset.BLIND:
    d = json.load(open(os.path.join(BASE, 'results', SESS[v], 'step04_result.json'),
                       encoding='utf-8'))
    nb = d['etalon']
    pred = np.array([d['delta_rel_to_etalon'][k] for k in
                     ('x_mm', 'y_mm', 'z_mm', 'roll_deg', 'pitch_deg', 'yaw_deg')])
    true = fit_model.pose_between(nb, v, PIVOT, ANCHOR)
    base[v] = err(pred, nb, v)
    ceil[v] = err(true, nb, v)
    fix[v], spoil[v] = [], []
    for k in range(6):
        p = pred.copy(); p[k] = true[k]
        fix[v].append(err(p, nb, v))
        q = true.copy(); q[k] = pred[k]
        spoil[v].append(err(q, nb, v))

print()
print("Починили ОДНУ ось (остальные как предсказано) — во что превращается ошибка")
print("=" * 84)
print(f"{'':<7}{'как есть':>10}" + "".join(f"{a:>10}" for a in AXES) + f"{'всё точно':>11}")
print("-" * 84)
for v in dataset.BLIND:
    print(f"{v:<7}{base[v]:>10.2f}" + "".join(f"{x:>10.2f}" for x in fix[v])
          + f"{ceil[v]:>11.2f}")
m = np.array([fix[v] for v in dataset.BLIND]).mean(0)
print("-" * 84)
print(f"{'среднее':<7}{np.mean(list(base.values())):>10.2f}"
      + "".join(f"{x:>10.2f}" for x in m)
      + f"{np.mean(list(ceil.values())):>11.2f}")

print()
print("Испортили ОДНУ ось (остальные истинные) — сколько стоит промах по ней")
print("=" * 84)
print(f"{'':<7}{'всё точно':>10}" + "".join(f"{a:>10}" for a in AXES))
print("-" * 84)
for v in dataset.BLIND:
    print(f"{v:<7}{ceil[v]:>10.2f}" + "".join(f"{x:>10.2f}" for x in spoil[v]))
s = np.array([spoil[v] for v in dataset.BLIND]).mean(0)
print("-" * 84)
print(f"{'среднее':<7}{np.mean(list(ceil.values())):>10.2f}"
      + "".join(f"{x:>10.2f}" for x in s))
