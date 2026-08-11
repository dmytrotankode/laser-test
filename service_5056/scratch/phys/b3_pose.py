"""Шаг B3: измерить позу нового шлема по фотографиям и сверить с его .LS.

Здесь впервые делается то, ради чего всё затевалось: поза берётся ТОЛЬКО из
трёх фотографий, а записанная программа используется исключительно как ответ
для сверки.

Чистота выборки. Камеры зафиксированы по вариантам v1/v8/v12/v16 (шаг B2).
Проверочные варианты в этой четвёрке НЕ участвовали, их фотографии камеры не
видели. Held-out проекта (v6, v13) здесь тоже не трогается - он остаётся на
самый конец, когда всё остальное сойдётся.

Мера - в миллиметрах ПО ЛИНИИ РЕЗА, а не в пикселях: берём линию реза v1,
двигаем восстановленной позой и меряем расстояние до настоящей линии реза
проверяемого варианта. Это те же единицы, в которых считается весь проект.
Рядом всегда «ничего не делать» - линия v1 без всякой коррекции.
"""
import os
import sys
import json
import numpy as np
import cv2
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation as Rot

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import render as R   # noqa: E402
import lsgeom        # noqa: E402
import dataset       # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

COARSE = 0.20
MM_PER_PX = 0.10 / COARSE
VIEWS = ('back', 'left', 'top')

MODEL = json.load(open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8'))
LIB, PIVOT = MODEL['library'], np.array(MODEL['pivot'])
xf = json.load(open(os.path.join(HERE, 'robot_to_mesh.json'), encoding='utf-8'))
Rrm, trm = np.array(xf['R']), np.array(xf['t'])
CAMS = json.load(open(os.path.join(HERE, 'b2_cams.json'), encoding='utf-8'))
FIT_ON = CAMS['back']['variants']
MC = R.VERTS.mean(0)

TEST = [v for v in dataset.TRAIN if v not in FIT_ON][:5]
assert not (set(TEST) & set(dataset.HELDOUT)), "held-out проекта сюда попадать не должен"
print(f"камеры зафиксированы по: {', '.join(FIT_ON)}")
print(f"проверяем на:            {', '.join(TEST)}")
print()

REF, _ = lsgeom.cut_surface(
    lsgeom.load(os.path.join(BASE, 'input', 'archive', 'v1', 'ground_truth.ls')),
    lsgeom.NOMINAL_STANDOFF)


def ring(v):
    p = lsgeom.load(os.path.join(BASE, 'input', 'archive', v, 'ground_truth.ls'))
    so, _ = lsgeom.fit_standoff(p, REF)
    return lsgeom.cut_surface(p, so)[0]


def robot_xf(vec6):
    """6 чисел (сдвиг мм + углы) -> поворот и сдвиг в координатах станка."""
    Rm = lsgeom.rot_from_ypr(vec6[5], vec6[4], vec6[3]).as_matrix()
    return Rm, np.array(vec6[:3]) + PIVOT - Rm @ PIVOT


def to_mesh_xf(Rr, tr):
    Rm = Rrm @ Rr @ Rrm.T
    return Rm, Rrm @ tr + trm - Rm @ trm


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


# базовая поза - поза v1 в системе меша (меш туда и подгонялся)
A1 = LIB['v1']['pose_vs_anchor']


def pose_to_mesh(vec6):
    """Абсолютная поза варианта -> движение меша относительно его исходного места."""
    Ra, ta = robot_xf(A1)
    Rb, tb = robot_xf(vec6)
    Rab = Rb @ Ra.T
    tab = tb - Rab @ ta
    return to_mesh_xf(Rab, tab)


def fit_pose(v):
    photos, cuts = {}, {}
    for view in VIEWS:
        photos[view], cuts[view] = R.load_mask(v, view, COARSE)

    def cost(vec6):
        Rm, tm = pose_to_mesh(vec6)
        tot = []
        for view in VIEWS:
            if photos[view] is None:
                continue
            m = CAMOBJ[view].silhouette(pose_R=Rm, pose_t=tm, cutoff_row=cuts[view])
            if np.count_nonzero(m) < 50:
                return 1e3
            tot.append(gap(m, photos[view]))
        return float(np.mean(tot))

    # старт - поза якоря; ищем в тех же пределах, в каких вообще гуляет библиотека
    P = np.array([LIB[k]['pose_vs_anchor'] for k in LIB])
    lo, hi = P.min(0), P.max(0)
    best = (cost(np.array(A1)), np.array(A1))
    rng = np.random.default_rng(7)
    for _ in range(25):
        s = lo + rng.random(6) * (hi - lo)
        c = cost(s)
        if c < best[0]:
            best = (c, s)
    for _ in range(4):
        r = minimize(cost, best[1], method='Nelder-Mead',
                     options=dict(maxiter=900, xatol=1e-3, fatol=1e-3))
        if r.fun >= best[0] - 1e-4:
            break
        best = (r.fun, r.x)
    return best


print("Ошибка по ЛИНИИ РЕЗА, мм (среднее / максимум)")
print(f"{'вар':<6}{'ничего не делать':>22}{'по фотографиям':>20}{'силуэт':>10}")
print("-" * 60)

rows = []
for v in TEST:
    if R.load_mask(v, 'back', COARSE)[0] is None:
        continue
    val, vec = fit_pose(v)
    target = ring(v)
    base = REF
    d0 = lsgeom.curve_distance(base, target)
    Rr, tr = robot_xf(vec)
    Ra, ta = robot_xf(A1)
    moved = (base - 0) @ (Rr @ Ra.T).T + (tr - (Rr @ Ra.T) @ ta)
    d1 = lsgeom.curve_distance(moved, target)
    rows.append((v, d0.mean(), d0.max(), d1.mean(), d1.max(), val * MM_PER_PX))
    print(f"{v:<6}{d0.mean():>10.2f} /{d0.max():>7.2f}"
          f"{d1.mean():>12.2f} /{d1.max():>7.2f}{val * MM_PER_PX:>10.2f}")

if rows:
    a = np.array([[r[1], r[3]] for r in rows])
    print("-" * 60)
    print(f"{'сред':<6}{a[:, 0].mean():>10.2f}{'':>8}{a[:, 1].mean():>12.2f}")
    print()
    better = int((a[:, 1] < a[:, 0]).sum())
    print(f"лучше, чем ничего не делать: {better} из {len(rows)}")
print()
print("Колонка «силуэт» - остаток подгонки в мм, для справки.")
print("Решает вторая колонка против первой: если поза, снятая с фотографий,")
print("не приближает линию реза к настоящей - метод не работает.")
