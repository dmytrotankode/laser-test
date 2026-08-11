"""Шаг B0, вторая поправка: сравнивать надо движение КУПОЛА, а не колонку сдвига.

Метка ICP это 6 чисел - поворот вокруг точки, лежащей на 190 мм НИЖЕ шлема, плюс
сдвиг. Камера видит не эти числа, а то, куда физически уехал купол. Наклон на
4.5° вокруг далёкой точки двигает купол на ~15 мм, хотя в колонке «сдвиг» стоит
3 мм. Поэтому прошлое сравнение (силуэт против трёх первых чисел метки) было
неверным по построению.

Здесь метка применяется целиком - к реальной точке купола в координатах станка,
- и сравнивается уже перемещение с перемещением.
"""
import os
import sys
import json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import lsgeom  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

COARSE = 0.20
MODEL = json.load(open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8'))
LIB, PIVOT = MODEL['library'], np.array(MODEL['pivot'])
cams = json.load(open(os.path.join(HERE, 'b0_cams.json'), encoding='utf-8'))

VARIANTS = ['v1', 'v8', 'v11', 'v12', 'v16', 'v10']
VIEWS = ('back', 'left', 'top')

# точка купола в координатах станка: центр кольца реза плюс высота до макушки
prog = lsgeom.load(os.path.join(BASE, 'input', 'archive', 'v1', 'ground_truth.ls'))
ring, _ = lsgeom.cut_surface(prog, lsgeom.NOMINAL_STANDOFF)
RING_C = ring.mean(0)
DOME = RING_C + np.array([0.0, 0.0, 90.0])       # ~середина видимого купола
print(f"центр кольца реза: {RING_C.round(1)}")
print(f"точка поворота:    {PIVOT.round(1)}   (ниже кольца на "
      f"{RING_C[2] - PIVOT[2]:.0f} мм)")
print()


def icp_move(v, p):
    """Куда уедет точка p под меткой варианта v."""
    a = LIB['v1']['pose_vs_anchor']
    b = LIB[v]['pose_vs_anchor']
    Ra = lsgeom.rot_from_ypr(a[5], a[4], a[3]).as_matrix()
    Rb = lsgeom.rot_from_ypr(b[5], b[4], b[3]).as_matrix()
    pa = Ra @ (p - PIVOT) + PIVOT + np.array(a[:3])
    pb = Rb @ (p - PIVOT) + PIVOT + np.array(b[:3])
    return float(np.linalg.norm(pb - pa))


def seen(v, view):
    p = np.array(cams[f'{v}_{view}']['p'])
    q = np.array(cams[f'v1_{view}']['p'])
    mm = np.exp(p[3]) / (np.exp(p[4]) * COARSE)
    return float(np.linalg.norm((p[5:7] - q[5:7]) * mm))


print("Перемещение купола относительно v1, мм")
print(f"{'вар':<6}{'только сдвиг':>14}{'ПОЛНАЯ метка':>15}"
      + "".join(f"{v:>9}" for v in VIEWS))
print("-" * 62)
tr, full, per_view = [], [], {v: [] for v in VIEWS}
for v in VARIANTS[1:]:
    t = float(np.linalg.norm(np.array(LIB[v]['pose_vs_anchor'][:3])
                             - np.array(LIB['v1']['pose_vs_anchor'][:3])))
    f = icp_move(v, DOME)
    s = [seen(v, view) for view in VIEWS]
    for view, x in zip(VIEWS, s):
        per_view[view].append(x)
    tr.append(t); full.append(f)
    print(f"{v:<6}{t:>11.2f} мм{f:>12.2f} мм" + "".join(f"{x:>9.2f}" for x in s))

full = np.array(full)
print()
for view in VIEWS:
    a = np.array(per_view[view])
    r = np.corrcoef(full, a)[0, 1]
    print(f"  {view:<5} связь с полной меткой: {r:+.2f}   "
          f"типичное расхождение {np.abs(a - full).mean():.1f} мм")
print()
print("Камера видит проекцию, поэтому её число должно быть НЕ БОЛЬШЕ полной метки")
print("и меняться вместе с ней.")
