"""Шаг B4: насколько силуэт вообще чувствителен к позе.

B3 показал странное: подгонка находит позы, уводящие рез на 5-6 мм, и силуэт при
этом совпадает НЕ ХУЖЕ, чем в лучшем случае. Если так, то дело не в подгонке, а
в самой задаче: разные позы неразличимы по силуэту.

Проверяется прямо. Для каждого варианта берём ИСТИННУЮ позу (из его .LS) и
найденную подгонкой, считаем для обеих две величины:

  * ошибку по линии реза - то, что важно заказчику;
  * остаток силуэта - то, что видит подгонка.

Если истинная поза лучше по резу, но НЕ лучше по силуэту, значит силуэт не
содержит нужной информации, и никакой оптимизатор её оттуда не достанет.

Заодно замер чувствительности: на сколько меняется силуэт, если увести позу на
1 мм в каждую сторону. Сравниваем с шумом (расхождение CAD с деталью ~1 мм).
"""
import os
import sys
import json
import numpy as np
import cv2
from scipy.spatial.transform import Rotation as Rot

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import render as R   # noqa: E402
import lsgeom        # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

COARSE = 0.20
MM_PER_PX = 0.10 / COARSE
VIEWS = ('back', 'left', 'top')
MODEL = json.load(open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8'))
LIB, PIVOT = MODEL['library'], np.array(MODEL['pivot'])
xf = json.load(open(os.path.join(HERE, 'robot_to_mesh.json'), encoding='utf-8'))
Rrm, trm = np.array(xf['R']), np.array(xf['t'])
CAMS = json.load(open(os.path.join(HERE, 'b2_cams.json'), encoding='utf-8'))
MC = R.VERTS.mean(0)
A1 = LIB['v1']['pose_vs_anchor']

REF, _ = lsgeom.cut_surface(
    lsgeom.load(os.path.join(BASE, 'input', 'archive', 'v1', 'ground_truth.ls')),
    lsgeom.NOMINAL_STANDOFF)


def robot_xf(v6):
    Rm = lsgeom.rot_from_ypr(v6[5], v6[4], v6[3]).as_matrix()
    return Rm, np.array(v6[:3]) + PIVOT - Rm @ PIVOT


def pose_to_mesh(v6):
    Ra, ta = robot_xf(A1)
    Rb, tb = robot_xf(v6)
    Rab = Rb @ Ra.T
    tab = tb - Rab @ ta
    Rm = Rrm @ Rab @ Rrm.T
    return Rm, Rrm @ tab + trm - Rm @ trm


def cutline_err(v6, target):
    Ra, ta = robot_xf(A1)
    Rb, tb = robot_xf(v6)
    Rab = Rb @ Ra.T
    moved = REF @ Rab.T + (tb - Rab @ ta)
    return lsgeom.curve_distance(moved, target)


def make_cam(view):
    p = np.array(CAMS[view]['p'])
    Rc = Rot.from_rotvec(p[:3]).as_matrix()
    dist, f = np.exp(p[3]), np.exp(p[4])
    eye = MC - Rc.T @ np.array([0.0, 0.0, dist])
    mm_px = dist / (f * COARSE)
    return R.Camera(f, Rc, -Rc @ eye + np.array([p[5] * mm_px, p[6] * mm_px, 0]),
                    scale=COARSE)


CAMOBJ = {v: make_cam(v) for v in VIEWS}


def gap(a, b):
    out = []
    for x, y in ((a, b), (b, a)):
        cs, _ = cv2.findContours(x, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not cs:
            return 1e3
        pts = max(cs, key=cv2.contourArea)[:, 0, :]
        do = cv2.distanceTransform(255 - y, cv2.DIST_L2, 3)
        di = cv2.distanceTransform(y, cv2.DIST_L2, 3)
        vv = np.where(y[pts[:, 1], pts[:, 0]] > 0,
                      di[pts[:, 1], pts[:, 0]], do[pts[:, 1], pts[:, 0]])
        out.append(float(np.abs(vv).mean()))
    return sum(out) / 2


def sil_cost(v6, photos, cuts):
    Rm, tm = pose_to_mesh(v6)
    tot = []
    for view in VIEWS:
        if photos[view] is None:
            continue
        m = CAMOBJ[view].silhouette(pose_R=Rm, pose_t=tm, cutoff_row=cuts[view])
        tot.append(gap(m, photos[view]))
    return float(np.mean(tot)) * MM_PER_PX


print("Чувствительность силуэта к позе")
print()
print("Уводим позу от истинной на N мм и смотрим, насколько ухудшается силуэт.")
print("Для сравнения: расхождение CAD с деталью около 1 мм - это шум, ниже")
print("которого сигнал неразличим.")
print()
print(f"{'вар':<6}{'сдвиг позы':>12}{'ошибка реза':>14}{'силуэт':>10}{'прирост':>10}")
print("-" * 54)

rng = np.random.default_rng(11)
for v in ('v2', 'v5'):
    photos, cuts = {}, {}
    for view in VIEWS:
        photos[view], cuts[view] = R.load_mask(v, view, COARSE)
    if photos['back'] is None:
        continue
    true6 = np.array(LIB[v]['pose_vs_anchor'])
    target = lsgeom.cut_surface(
        lsgeom.load(os.path.join(BASE, 'input', 'archive', v, 'ground_truth.ls')),
        lsgeom.fit_standoff(lsgeom.load(os.path.join(
            BASE, 'input', 'archive', v, 'ground_truth.ls')), REF)[0])[0]
    c0 = sil_cost(true6, photos, cuts)
    e0 = cutline_err(true6, target).mean()
    print(f"{v:<6}{'истинная':>12}{e0:>11.2f} мм{c0:>10.2f}{'':>10}")
    for mag in (1.0, 2.0, 4.0, 8.0):
        cs, es = [], []
        for _ in range(6):
            d = rng.normal(size=6)
            d[:3] *= mag / max(np.linalg.norm(d[:3]), 1e-9)
            d[3:] *= 0.0                       # только сдвиг, без поворота
            p = true6 + d
            cs.append(sil_cost(p, photos, cuts))
            es.append(cutline_err(p, target).mean())
        print(f"{'':<6}{mag:>9.0f} мм{np.mean(es):>11.2f} мм"
              f"{np.mean(cs):>10.2f}{np.mean(cs) - c0:>+10.2f}")
    print()

print("Читать так: если увод позы на 4-8 мм ухудшает силуэт меньше чем на ~1 мм,")
print("то на фоне расхождения CAD с деталью эти позы неразличимы, и подгонка")
print("выберет любую из них. Это предел метода, а не качество оптимизатора.")
