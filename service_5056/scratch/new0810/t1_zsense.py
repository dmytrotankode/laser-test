"""Тест A1: видит ли силуэтная подгонка ВЫСОТУ - на синтетике, где формы нет.

Зачем синтетика. На реальных фото у 3D две беды сразу: расхождение CAD с деталью
(~1.2 мм) и вопрос чувствительности. Если сразу мерить на фото, они смешаются, и
отрицательный результат ничего не скажет - именно так в прошлой сессии дважды
пришлось отзывать вывод. Здесь "деталь" - сам меш, поэтому ошибка формы ровно
ноль, и остаётся чистый вопрос: несёт ли силуэт информацию о высоте.

Это ВЕРХНЯЯ граница возможностей метода. Хуже - может быть, лучше - нет.

Два замера:

  1. чувствительность: насколько растёт невязка силуэта при сдвиге по Z на
     известную величину. Сравнивается со сдвигом по X той же величины - X
     заведомо виден (в прошлой сессии 2 мм сдвига давали 1.04 мм в силуэте);

  2. восстановление: рендерим силуэт при известной высоте и просим подгонку её
     найти. Посев НАМЕРЕННО расширен по Z: штатный посев ограничен коробкой
     библиотеки (b3_pose.py:135), то есть Z в [0, 1.25] мм, а реальные высоты
     доходят до 3.24 - на штатном посеве метод "не увидел" бы высоту просто
     потому, что её негде искать.
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
PHYS = os.path.join(BASE, 'scratch', 'phys')
sys.path.insert(0, PHYS)
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import render as R   # noqa: E402
import lsgeom        # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

COARSE = 0.20
MM_PER_PX = 0.10 / COARSE
VIEWS = ('back', 'left', 'top')

MODEL = json.load(open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8'))
LIB, PIVOT = MODEL['library'], np.array(MODEL['pivot'])
xf = json.load(open(os.path.join(PHYS, 'robot_to_mesh.json'), encoding='utf-8'))
Rrm, trm = np.array(xf['R']), np.array(xf['t'])
CAMS = json.load(open(os.path.join(PHYS, 'b2_cams.json'), encoding='utf-8'))
MC = R.VERTS.mean(0)
A1 = np.array(LIB['v1']['pose_vs_anchor'])


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


def make_cam(view):
    p = np.array(CAMS[view]['p'])
    Rc = Rot.from_rotvec(p[:3]).as_matrix()
    dist, f = np.exp(p[3]), np.exp(p[4])
    eye = MC - Rc.T @ np.array([0.0, 0.0, dist])
    mm_px = dist / (f * COARSE)
    return R.Camera(f, Rc, -Rc @ eye + np.array([p[5] * mm_px, p[6] * mm_px, 0]),
                    scale=COARSE)


CAM = {v: make_cam(v) for v in VIEWS}
CUT = {}
for view in VIEWS:
    m, c = R.load_mask('v1', view, COARSE)
    CUT[view] = c


def render(v6):
    Rm, tm = pose_to_mesh(v6)
    return {v: CAM[v].silhouette(pose_R=Rm, pose_t=tm, cutoff_row=CUT[v])
            for v in VIEWS}


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


def cost_against(target):
    def f(v6):
        s = render(v6)
        tot = []
        for view in VIEWS:
            if np.count_nonzero(s[view]) < 50:
                return 1e3
            tot.append(gap(s[view], target[view]))
        return float(np.mean(tot))
    return f


# ------------------------------------------------------------------ 1. чувствительность
print()
print("1. ЧУВСТВИТЕЛЬНОСТЬ: во что превращается известный сдвиг, мм невязки силуэта")
print("=" * 76)
base = A1.copy()
target = render(base)
c = cost_against(target)
print(f"   невязка при точном совпадении: {c(base) * MM_PER_PX:.3f} мм (обязана быть ~0)")
print()
print(f"{'сдвиг':>8}{'по Z (высота)':>18}{'по X':>12}{'наклон pitch':>16}")
for d in (0.5, 1.0, 2.0, 3.0):
    z = base.copy(); z[2] += d
    x = base.copy(); x[0] += d
    p = base.copy(); p[4] += d
    print(f"{d:>6.1f}мм{c(z) * MM_PER_PX:>18.3f}{c(x) * MM_PER_PX:>12.3f}"
          f"{c(p) * MM_PER_PX:>16.3f}   (наклон в градусах)")

# ------------------------------------------------------------------ 2. восстановление
print()
print("2. ВОССТАНОВЛЕНИЕ высоты из силуэта (посев расширен по Z до ±6 мм)")
print("=" * 76)
P = np.array([LIB[k]['pose_vs_anchor'] for k in LIB])
lo, hi = P.min(0) - 1.0, P.max(0) + 1.0
lo[2], hi[2] = -6.0, 6.0


# Шаг стартового симплекса задаётся ЯВНО. По умолчанию Nelder-Mead берёт 5% от
# значения параметра, а Z у нас стартует с нуля - шаг выходит 0.00025 мм, и
# координата не двигается вовсе: подгонка возвращает Z=0 даже там, где истинная
# поза даёт заметно меньшую невязку. Ровно эта ошибка уже была в прошлой сессии
# (HANDOFF 8, "сдвиг, парализованный масштабом параметра").
STEP = np.array([0.6, 0.6, 0.6, 0.6, 0.6, 0.6])


def simplex(x0):
    S = [x0] + [x0 + STEP[i] * np.eye(6)[i] for i in range(6)]
    return np.array(S)


def fit(target, seed=11):
    f = cost_against(target)
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


print(f"{'истинный Z':>12}{'найденный Z':>14}{'промах':>10}{'невязка, мм':>14}")
for ztrue in (0.0, 1.0, 2.0, 3.0):
    truth = base.copy(); truth[2] += ztrue
    res, vec = fit(render(truth))
    print(f"{truth[2]:>12.2f}{vec[2]:>14.2f}{vec[2] - truth[2]:>10.2f}"
          f"{res * MM_PER_PX:>14.3f}")
