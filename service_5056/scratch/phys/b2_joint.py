"""Шаг B2: может ли ОДНА камера объяснить несколько снимков сразу.

Позы шлема НЕ подгоняются - они берутся из меток ICP, которые проверены
отдельно (b1c_check.py: метка переводит линию реза v1 в линию нужного варианта
с точностью 0.52-0.65 мм). Подгоняется только камера: 7 чисел на вид.

Чем это отличается от прошлой попытки. Там камера искалась по одному снимку и
могла впитать в себя расхождение CAD с деталью - получалось сочетание «неверная
камера + неверная поза», хорошо описывающее ровно один кадр. Здесь такой свободы
нет: одна камера обязана объяснить несколько разных поз шлема сразу, а позы
заданы извне и не двигаются.

Критерий: остаток совместной подгонки не должен быть заметно хуже, чем у
подгонок по одному снимку (они лежат в b0_cams.json). Если хуже в разы - виды
не согласуются, и путь закрыт.
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

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

COARSE = 0.20
MM_PER_PX = 0.10 / COARSE
VARIANTS = ['v1', 'v8', 'v12', 'v16']
VIEWS = ('back', 'left', 'top')

MODEL = json.load(open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8'))
LIB, PIVOT = MODEL['library'], np.array(MODEL['pivot'])
xf = json.load(open(os.path.join(HERE, 'robot_to_mesh.json'), encoding='utf-8'))
Rrm, trm = np.array(xf['R']), np.array(xf['t'])
solo = json.load(open(os.path.join(HERE, 'b0_cams.json'), encoding='utf-8'))
MC = R.VERTS.mean(0)


def motion_in_mesh(v):
    """Движение шлема v1 -> v, в системе меша. Проверено в b1c_check.py."""
    a, b = LIB['v1']['pose_vs_anchor'], LIB[v]['pose_vs_anchor']
    Ra = lsgeom.rot_from_ypr(a[5], a[4], a[3]).as_matrix()
    Rb = lsgeom.rot_from_ypr(b[5], b[4], b[3]).as_matrix()
    Rab = Rb @ Ra.T
    tab = np.array(b[:3]) - Rab @ np.array(a[:3]) + PIVOT - Rab @ PIVOT
    Rm = Rrm @ Rab @ Rrm.T
    return Rm, Rrm @ tab + trm - Rm @ trm


MOTION = {v: motion_in_mesh(v) for v in VARIANTS}


def make_cam(p):
    Rc = Rot.from_rotvec(p[:3]).as_matrix()
    dist, f = np.exp(p[3]), np.exp(p[4])
    eye = MC - Rc.T @ np.array([0.0, 0.0, dist])
    mm_px = dist / (f * COARSE)
    return R.Camera(f, Rc, -Rc @ eye + np.array([p[5] * mm_px, p[6] * mm_px, 0]),
                    scale=COARSE)


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


def center(m):
    M = cv2.moments(m)
    return (M['m10'] / M['m00'], M['m01'] / M['m00']) if M['m00'] else (0, 0)


def run_view(view):
    photos, cuts = {}, {}
    for v in VARIANTS:
        photos[v], cuts[v] = R.load_mask(v, view, COARSE)
    have = [v for v in VARIANTS if photos[v] is not None]

    def render(p, v):
        Rm, tm = MOTION[v]
        return make_cam(p).silhouette(pose_R=Rm, pose_t=tm, cutoff_row=cuts[v])

    def cost(p):
        try:
            vals = [gap(render(p, v), photos[v]) for v in have]
        except Exception:
            return 1e3
        if any(x >= 1e3 for x in vals):
            return 1e3
        return float(np.mean(vals))

    p_solo = np.array(solo[f'v1_{view}']['p'])
    cx1, cy1 = center(photos['v1'])

    def recenter(p):
        p = p.copy()
        c0 = center(render(p, 'v1'))
        p[5] += cx1 - c0[0]; p[6] += cy1 - c0[1]
        return p

    cands = [recenter(p_solo)]
    for spin in np.linspace(-np.pi, np.pi, 12, endpoint=False):
        for ax in ((1, 0, 0), (0, 1, 0)):
            for t in (-0.3, 0.0, 0.3):
                dR = (Rot.from_rotvec([0, 0, spin]) *
                      Rot.from_rotvec(np.asarray(ax, float) * t))
                p = p_solo.copy()
                p[:3] = (dR * Rot.from_rotvec(p_solo[:3])).as_rotvec()
                cands.append(recenter(p))
    rng = np.random.default_rng(3)
    for _ in range(30):
        p = p_solo.copy()
        p[:3] = Rot.random(random_state=int(rng.integers(1 << 30))).as_rotvec()
        p[3] += rng.normal(0, 0.15)
        cands.append(recenter(p))

    scored = sorted(((cost(p), i) for i, p in enumerate(cands)))
    best = (scored[0][0], cands[scored[0][1]])
    for _, i in scored[:4]:
        r = minimize(cost, cands[i], method='Nelder-Mead',
                     options=dict(maxiter=600, xatol=1e-3, fatol=1e-3))
        if r.fun < best[0]:
            best = (r.fun, r.x)
    for _ in range(3):
        r = minimize(cost, best[1], method='Nelder-Mead',
                     options=dict(maxiter=1200, xatol=1e-4, fatol=1e-4))
        if r.fun >= best[0] - 1e-4:
            break
        best = (r.fun, r.x)
    return best[1], have, photos, cuts, render


def crop(*ms):
    u = ms[0].copy()
    for m in ms[1:]:
        u = cv2.bitwise_or(u, m)
    ys, xs = np.where(u > 0)
    if not len(ys):
        return list(ms)
    y0, y1 = max(ys.min() - 6, 0), min(ys.max() + 6, u.shape[0])
    x0, x1 = max(xs.min() - 6, 0), min(xs.max() + 6, u.shape[1])
    return [m[y0:y1, x0:x1] for m in ms]


print("Одна камера на вид, позы шлема взяты из меток и НЕ подгоняются.")
print(f"Варианты: {', '.join(VARIANTS)}")
print()
print(f"{'вид':<7}{'вар':<6}{'совместно':>13}{'по одному кадру':>18}{'цена':>9}")
print("-" * 54)

summary = []
saved = {}
for view in VIEWS:
    par, have, photos, cuts, render = run_view(view)
    saved[view] = {'p': [float(x) for x in par], 'variants': have}
    json.dump(saved, open(os.path.join(HERE, 'b2_cams.json'), 'w', encoding='utf-8'))
    panels = []
    for v in have:
        m = render(par, v)
        g = gap(m, photos[v]) * MM_PER_PX
        s = solo.get(f'{v}_{view}', {}).get('val')
        s = s * MM_PER_PX if s else float('nan')
        summary.append((view, v, g, s))
        print(f"{view:<7}{v:<6}{g:>10.2f} мм{s:>15.2f} мм{g - s:>+8.2f}")
        a, b = crop(m, photos[v])
        h, w = a.shape
        vis = np.zeros((h, w, 3), np.uint8)
        vis[:, :, 2] = a; vis[:, :, 1] = b
        vis[cv2.bitwise_and(a, b) > 0] = (0, 255, 255)
        vis = cv2.copyMakeBorder(vis, 24, 4, 4, 4, cv2.BORDER_CONSTANT, value=0)
        cv2.putText(vis, f"{v}  {g:.2f}mm", (6, 17),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        panels.append(vis)
    hm = max(p.shape[0] for p in panels)
    panels = [cv2.copyMakeBorder(p, 0, hm - p.shape[0], 0, 6,
                                 cv2.BORDER_CONSTANT, value=(40, 40, 40)) for p in panels]
    cv2.imwrite(os.path.join(HERE, f'b2_{view}.png'), np.hstack(panels))
    d = np.exp(par[3]); f = np.exp(par[4])
    print(f"{'':7}камера: дистанция {d:.0f} мм, фокус {f:.0f}")
    print()

j = np.array([s[2] for s in summary]); s1 = np.array([s[3] for s in summary])
print(f"совместно в среднем {j.mean():.2f} мм, по одному кадру {s1.mean():.2f} мм")
print()
print("КРАСНЫЙ - модель, ЗЕЛЁНЫЙ - фото, ЖЁЛТЫЙ - совпало.")
print("Если совместная подгонка недалеко от одиночной - виды согласуются позой")
print("из .LS, и общая калибровка оправдана.")
