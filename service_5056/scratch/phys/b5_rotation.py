"""Шаг B5: видит ли силуэт ПОВОРОТ шлема. Единственная непроверенная дыра.

В замере чувствительности (b4) вращения были обнулены - мерились только сдвиги.
А шлем на гладкой болванке в основном качается, а не съезжает: по библиотеке
размах наклона 3-5 градусов при сдвиге 4 мм. Наклон меняет обвод иначе, чем
сдвиг, и мог бы быть виден лучше.

Меряется две вещи, и различать их важно:

  ЧИСТАЯ чувствительность - силуэт модели против силуэта той же модели,
      повёрнутой на известный угол. Показывает, виден ли поворот В ПРИНЦИПЕ.
  ЗАМАСКИРОВАННАЯ - то же самое, но против настоящей фотографии, где уже сидит
      расхождение CAD с деталью ~1.2 мм. Показывает, виден ли он НАМ.

Ключевая колонка - «на 1 мм реза»: сколько силуэта приходится на миллиметр
ошибки линии реза. У сдвига вышло 0.6-0.9. Если у поворота заметно больше,
вывод ветки надо пересматривать.
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


def delta_to_mesh(v6):
    Ra, ta = robot_xf(A1)
    Rb, tb = robot_xf(v6)
    Rab = Rb @ Ra.T
    tab = tb - Rab @ ta
    Rm = Rrm @ Rab @ Rrm.T
    return Rm, Rrm @ tab + trm - Rm @ trm, Rab, tab


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


photos, cuts = {}, {}
for view in VIEWS:
    photos[view], cuts[view] = R.load_mask('v1', view, COARSE)

BASE_REN = {v: CAMOBJ[v].silhouette(cutoff_row=cuts[v]) for v in VIEWS}
BASE_PHOTO = {v: gap(BASE_REN[v], photos[v]) * MM_PER_PX for v in VIEWS}
print("расхождение CAD с фотографией в исходной позе, мм: "
      + ", ".join(f"{v} {BASE_PHOTO[v]:.2f}" for v in VIEWS))
print()


def probe(dv6, n=8, rot=True):
    """Средние по n случайным направлениям: ошибка реза, чистый и маскированный силуэт."""
    rng = np.random.default_rng(21)
    er, cl, msk = [], [], []
    for _ in range(n):
        d = np.zeros(6)
        u = rng.normal(size=3); u /= np.linalg.norm(u)
        if rot:
            d[3:] = u * dv6
        else:
            d[:3] = u * dv6
        p = np.array(A1) + d
        Rm, tm, Rab, tab = delta_to_mesh(p)
        moved = REF @ Rab.T + tab
        er.append(lsgeom.curve_distance(moved, REF).mean())
        c, m = [], []
        for view in VIEWS:
            s = CAMOBJ[view].silhouette(pose_R=Rm, pose_t=tm, cutoff_row=cuts[view])
            c.append(gap(s, BASE_REN[view]) * MM_PER_PX)
            m.append(gap(s, photos[view]) * MM_PER_PX - BASE_PHOTO[view])
        cl.append(np.mean(c)); msk.append(np.mean(m))
    return np.mean(er), np.mean(cl), np.mean(msk)


for label, rot, steps in (("ПОВОРОТ, градусов", True, (0.5, 1.0, 2.0, 4.0)),
                          ("СДВИГ, мм", False, (1.0, 2.0, 4.0, 8.0))):
    print(label)
    print(f"{'':>8}{'ошибка реза':>14}{'чистый силуэт':>16}"
          f"{'на фоне CAD':>14}{'на 1 мм реза':>15}")
    for s in steps:
        er, cl, msk = probe(s, rot=rot)
        print(f"{s:>8.1f}{er:>11.2f} мм{cl:>13.2f} мм{msk:>+13.2f}"
              f"{cl / max(er, 1e-9):>14.2f}")
    print()

print("«чистый силуэт» - модель против самой себя, видно ли изменение в принципе.")
print("«на фоне CAD» - прирост расхождения с настоящей фотографией; это то,")
print("     что реально видит подгонка.")
print("«на 1 мм реза» - главное число: сколько сигнала приходится на миллиметр")
print("     ошибки, которая важна заказчику.")
