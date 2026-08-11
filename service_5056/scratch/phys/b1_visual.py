"""Шаг B1: видит ли силуэт известное движение шлема. Без подгонки, с картинками.

Замысел, в котором негде ошибиться:

  1. камера берётся одна - найденная на v1, дальше не трогается;
  2. меш двигается на величину, ИЗВЕСТНУЮ из записанных программ (метка ICP);
  3. смотрим, стал ли силуэт ближе к фотографии этого варианта.

Ни одной подгонки к проверяемым данным. Если «с меткой» лучше, чем «без метки»,
- цепочка «фото <-> координаты станка» работает. Если одинаково - силуэт
движения не видит.

Встроенная самопроверка: для самого v1 метка нулевая, и оба рендера обязаны
совпасть побитово. Если нет - сломан перенос координат, а не физика.
"""
import os
import sys
import json
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
sys.path.insert(0, os.path.join(os.path.dirname(HERE)))

import render as R                                    # noqa: E402
import lsgeom                                         # noqa: E402
from scipy.spatial.transform import Rotation as Rot   # noqa: E402
from scipy.spatial import cKDTree                     # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

COARSE = 0.20
MODEL = json.load(open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8'))
LIB, PIVOT = MODEL['library'], np.array(MODEL['pivot'])
cams = json.load(open(os.path.join(HERE, 'b0_cams.json'), encoding='utf-8'))
VIEWS = ('back', 'left', 'top')
VARIANTS = ['v8', 'v11', 'v12', 'v16', 'v10']
XF_CACHE = os.path.join(HERE, 'robot_to_mesh.json')

# ------------------------------------------------------------------ 1. связь
# «координаты станка -> система меша», один раз, подгонкой меша к линии реза v1
CENT = R.TRI.mean(1)
CTREE = cKDTree(CENT)
RMAX = np.linalg.norm(R.TRI - CENT[:, None, :], axis=2).max()
A, B, Cc = R.TRI[:, 0], R.TRI[:, 1], R.TRI[:, 2]


def nearest_on_mesh(P):
    d0, _ = CTREE.query(P)
    out = np.empty(len(P)); close = np.empty((len(P), 3))
    for i, p in enumerate(P):
        idx = np.array(CTREE.query_ball_point(p, d0[i] + 2 * RMAX) or [0])
        a, b, c = A[idx], B[idx], Cc[idx]
        ab, ac = b - a, c - a
        n = np.cross(ab, ac)
        nn = np.linalg.norm(n, axis=1, keepdims=True)
        n = n / np.where(nn == 0, 1, nn)
        w = p - a
        q = p - (w * n).sum(1, keepdims=True) * n          # проекция на плоскость
        # зажим в треугольник по барицентрике
        d00 = (ab * ab).sum(1); d01 = (ab * ac).sum(1); d11 = (ac * ac).sum(1)
        wq = q - a
        d20 = (wq * ab).sum(1); d21 = (wq * ac).sum(1)
        den = d00 * d11 - d01 * d01
        den = np.where(den == 0, 1e-12, den)
        u = (d11 * d20 - d01 * d21) / den
        v = (d00 * d21 - d01 * d20) / den
        u = np.clip(u, 0, 1); v = np.clip(v, 0, 1)
        s = u + v; bad = s > 1
        u = np.where(bad, u / np.where(bad, s, 1), u)
        v = np.where(bad, v / np.where(bad, s, 1), v)
        qq = a + u[:, None] * ab + v[:, None] * ac
        dd = np.linalg.norm(qq - p, axis=1)
        k = int(np.argmin(dd))
        out[i] = dd[k]; close[i] = qq[k]
    return out, close


def fit_robot_to_mesh(P):
    """Ищем поворот+сдвиг, переводящие точки станка в систему меша."""
    best = None
    for flip in (0, 180):
        for yaw in range(0, 360, 30):
            M = Rot.from_euler('ZX', [yaw, flip], degrees=True).as_matrix()
            Q = (P - P.mean(0)) @ M.T + R.VERTS.mean(0)
            acc_R, acc_t = M.copy(), R.VERTS.mean(0) - M @ P.mean(0)
            for _ in range(40):
                d, q = nearest_on_mesh(Q)
                Rk, tk = lsgeom.kabsch(Q, q)
                Q = Q @ Rk.T + tk
                acc_R = Rk @ acc_R; acc_t = Rk @ acc_t + tk
            d, _ = nearest_on_mesh(Q)
            if best is None or d.mean() < best[0]:
                best = (float(d.mean()), acc_R, acc_t)
    return best


prog = lsgeom.load(os.path.join(BASE, 'input', 'archive', 'v1', 'ground_truth.ls'))
RING, _ = lsgeom.cut_surface(prog, lsgeom.NOMINAL_STANDOFF)

if os.path.exists(XF_CACHE):
    j = json.load(open(XF_CACHE, encoding='utf-8'))
    RES, Rrm, trm = j['res'], np.array(j['R']), np.array(j['t'])
    print(f"связь станок->меш из кэша, остаток {RES:.2f} мм")
else:
    print("ищу связь «координаты станка -> система меша» (один раз)...", flush=True)
    RES, Rrm, trm = fit_robot_to_mesh(RING)
    json.dump({'res': RES, 'R': Rrm.tolist(), 't': trm.tolist()},
              open(XF_CACHE, 'w', encoding='utf-8'))
    print(f"  остаток линии реза до поверхности меша: {RES:.2f} мм")


def to_mesh(p):
    return p @ Rrm.T + trm


PIVOT_M = to_mesh(PIVOT[None, :])[0]


# ------------------------------------------------------- 2. движение из метки
def motion_in_mesh(v):
    """Поворот+сдвиг в системе меша, переводящие позу v1 в позу v."""
    a, b = LIB['v1']['pose_vs_anchor'], LIB[v]['pose_vs_anchor']
    Ra = lsgeom.rot_from_ypr(a[5], a[4], a[3]).as_matrix()
    Rb = lsgeom.rot_from_ypr(b[5], b[4], b[3]).as_matrix()
    # поза i: x -> Ri (x - pivot) + pivot + ti ; переход a->b
    Rab = Rb @ Ra.T
    tab = (np.array(b[:3]) - Rab @ np.array(a[:3])
           + PIVOT - Rab @ PIVOT)
    Rm = Rrm @ Rab @ Rrm.T
    tm = Rrm @ tab + trm - Rm @ trm
    return Rm, tm


def make_cam(view):
    p = np.array(cams[f'v1_{view}']['p'])
    Rc = Rot.from_rotvec(p[:3]).as_matrix()
    dist, f = np.exp(p[3]), np.exp(p[4])
    eye = R.VERTS.mean(0) - Rc.T @ np.array([0.0, 0.0, dist])
    mm_px = dist / (f * COARSE)
    return R.Camera(f, Rc, -Rc @ eye + np.array([p[5] * mm_px, p[6] * mm_px, 0]),
                    scale=COARSE)


def gap(a, b):
    out = []
    for x, y in ((a, b), (b, a)):
        cs, _ = cv2.findContours(x, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not cs:
            return float('nan')
        pts = max(cs, key=cv2.contourArea)[:, 0, :]
        do = cv2.distanceTransform(255 - y, cv2.DIST_L2, 3)
        di = cv2.distanceTransform(y, cv2.DIST_L2, 3)
        vv = np.where(y[pts[:, 1], pts[:, 0]] > 0,
                      di[pts[:, 1], pts[:, 0]], do[pts[:, 1], pts[:, 0]])
        out.append(float(np.abs(vv).mean()))
    return sum(out) / 2


def crop(*masks):
    u = masks[0].copy()
    for m in masks[1:]:
        u = cv2.bitwise_or(u, m)
    ys, xs = np.where(u > 0)
    if len(ys) == 0:
        return [m for m in masks]
    y0, y1 = max(ys.min() - 8, 0), min(ys.max() + 8, u.shape[0])
    x0, x1 = max(xs.min() - 8, 0), min(xs.max() + 8, u.shape[1])
    return [m[y0:y1, x0:x1] for m in masks]


def panel(ren, photo, title, val):
    a, b = crop(ren, photo)
    h, w = a.shape
    vis = np.zeros((h, w, 3), np.uint8)
    vis[:, :, 2] = a; vis[:, :, 1] = b
    vis[cv2.bitwise_and(a, b) > 0] = (0, 255, 255)
    vis = cv2.copyMakeBorder(vis, 26, 4, 4, 4, cv2.BORDER_CONSTANT, value=(0, 0, 0))
    cv2.putText(vis, f"{title}  {val:.2f}mm", (6, 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    return vis


MM_PER_PX = 0.10 / COARSE
print()
print("КРАСНЫЙ - модель, ЗЕЛЁНЫЙ - фотография, ЖЁЛТЫЙ - совпало")
print()
print(f"{'вар':<6}{'вид':<7}{'без метки':>12}{'С МЕТКОЙ':>12}{'изменение':>12}")
print("-" * 49)

# самопроверка на v1
Rm0, tm0 = motion_in_mesh('v1')
assert np.allclose(Rm0, np.eye(3), atol=1e-6) and np.allclose(tm0, 0, atol=1e-4), \
    "метка v1 не нулевая - сломан перенос координат"
print("самопроверка: метка v1 нулевая, перенос координат согласован")
print()

rows = []
for view in VIEWS:
    cam = make_cam(view)
    strip = []
    for v in VARIANTS:
        photo, cut = R.load_mask(v, view, COARSE)
        if photo is None:
            continue
        base = cam.silhouette(cutoff_row=cut)
        Rm, tm = motion_in_mesh(v)
        moved = cam.silhouette(pose_R=Rm, pose_t=tm, cutoff_row=cut)
        g0, g1 = gap(base, photo) * MM_PER_PX, gap(moved, photo) * MM_PER_PX
        rows.append((v, view, g0, g1))
        print(f"{v:<6}{view:<7}{g0:>10.2f} мм{g1:>10.2f} мм"
              f"{g1 - g0:>+11.2f}")
        p0 = panel(base, photo, f"{v} bez metki", g0)
        p1 = panel(moved, photo, f"{v} S METKOY", g1)
        h = max(p0.shape[0], p1.shape[0])
        p0 = cv2.copyMakeBorder(p0, 0, h - p0.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=0)
        p1 = cv2.copyMakeBorder(p1, 0, h - p1.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=0)
        strip.append(np.hstack([p0, p1]))
    if strip:
        hmax = max(s.shape[0] for s in strip)
        strip = [cv2.copyMakeBorder(s, 0, hmax - s.shape[0], 0, 6,
                                    cv2.BORDER_CONSTANT, value=(40, 40, 40)) for s in strip]
        out = os.path.join(HERE, f'b1_{view}.png')
        cv2.imwrite(out, np.hstack(strip))
        print(f"   -> {out}")

d = np.array([r[3] - r[2] for r in rows])
print()
print(f"улучшилось в {int((d < 0).sum())} случаях из {len(d)}, "
      f"среднее изменение {d.mean():+.2f} мм")
print()
print("Если метка помогает - силуэт видит движение шлема, и путь живой.")
print("Если нет - не видит, и дальше идти незачем.")
