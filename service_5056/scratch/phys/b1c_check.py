"""Настоящая самопроверка переноса координат.

Прошлая проверяла только, что метка самого v1 нулевая - а это верно при любой
путанице осей и знаков. Здесь проверяется то, что обязано выполняться:

  метка варианта v, применённая к линии реза v1, должна лечь НА линию реза v.

Обе линии известны из записанных программ, ничего подгонять не надо. Проверка
делается дважды: в координатах станка (проверяет саму метку) и в системе меша
(проверяет мой перенос). Если первая проходит, а вторая нет - виноват перенос.
"""
import os
import sys
import json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import lsgeom  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MODEL = json.load(open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8'))
LIB, PIVOT = MODEL['library'], np.array(MODEL['pivot'])
xf = json.load(open(os.path.join(HERE, 'robot_to_mesh.json'), encoding='utf-8'))
Rrm, trm = np.array(xf['R']), np.array(xf['t'])

REF, _ = lsgeom.cut_surface(
    lsgeom.load(os.path.join(BASE, 'input', 'archive', 'v1', 'ground_truth.ls')),
    lsgeom.NOMINAL_STANDOFF)


def ring(v):
    p = lsgeom.load(os.path.join(BASE, 'input', 'archive', v, 'ground_truth.ls'))
    so, _ = lsgeom.fit_standoff(p, REF)
    return lsgeom.cut_surface(p, so)[0]


def label_xf(v):
    """Поворот+сдвиг в координатах станка, переводящие позу v1 в позу v."""
    a, b = LIB['v1']['pose_vs_anchor'], LIB[v]['pose_vs_anchor']
    Ra = lsgeom.rot_from_ypr(a[5], a[4], a[3]).as_matrix()
    Rb = lsgeom.rot_from_ypr(b[5], b[4], b[3]).as_matrix()
    Rab = Rb @ Ra.T
    tab = np.array(b[:3]) - Rab @ np.array(a[:3]) + PIVOT - Rab @ PIVOT
    return Rab, tab


V1 = ring('v1')
print("Проверка 1. В координатах станка: метка переводит линию реза v1 в линию v?")
print(f"{'вар':<6}{'до метки':>12}{'после метки':>14}{'сдвиг метки':>14}")
print("-" * 48)
ok_robot = {}
for v in ('v8', 'v11', 'v12', 'v16', 'v10'):
    Rv = ring(v)
    d0 = lsgeom.curve_distance(V1, Rv).mean()
    Rab, tab = label_xf(v)
    moved = V1 @ Rab.T + tab
    d1 = lsgeom.curve_distance(moved, Rv).mean()
    ok_robot[v] = d1
    print(f"{v:<6}{d0:>9.2f} мм{d1:>11.2f} мм"
          f"{np.linalg.norm(moved.mean(0) - V1.mean(0)):>11.2f} мм")

print()
print("Проверка 2. В системе меша: тот же перенос, что использует рендер.")
print(f"{'вар':<6}{'после метки':>14}{'должно совпасть с проверкой 1':>32}")
print("-" * 54)
for v in ('v8', 'v11', 'v12', 'v16', 'v10'):
    Rv = ring(v)
    Rab, tab = label_xf(v)
    Rm = Rrm @ Rab @ Rrm.T
    tm = Rrm @ tab + trm - Rm @ trm
    v1m = V1 @ Rrm.T + trm
    movedm = v1m @ Rm.T + tm
    rvm = Rv @ Rrm.T + trm
    d = lsgeom.curve_distance(movedm, rvm).mean()
    flag = "OK" if abs(d - ok_robot[v]) < 0.05 else "<<< РАСХОДИТСЯ"
    print(f"{v:<6}{d:>11.2f} мм{ok_robot[v]:>20.2f} мм   {flag}")

print()
print("Проверка 1 показывает, работает ли метка вообще.")
print("Проверка 2 - не сломал ли я её при переносе в систему меша.")
