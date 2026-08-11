"""Шаг C1: сгенерировать настоящие .LS по 3D-методу и сравнить с программами оператора.

Всё, что можно, берётся из проекта, чтобы цифры были сопоставимы с остальными:

  * сегментация - штатная step03 (rembg, без отката на Otsu);
  * запись .LS - штатный step05, вместе с его проверкой на валидность
    (файл удаляется, если меньше 90 команд движения или другой набор точек);
  * линия реза и метрика - штатные lsgeom.cut_surface / curve_distance,
    точка врезки исключается так же, как в evaluate.py.

Своё здесь только одно: поза берётся не из k-NN по признакам, а подгонкой
силуэта CAD к трём фотографиям при камерах, найденных в b2 (по v1/v8/v12/v16).

Источник контура - v1: 3D-метод даёт АБСОЛЮТНУЮ позу, поэтому ближайший сосед
ему не нужен, и якорь библиотеки тут естественный выбор.

Проверочные случаи: v6, v13 (held-out проекта - здесь они используются по
назначению, для оценки, и в подгонку камер не входили) и цеховая съёмка 05.08.
"""
import os
import sys
import json
import subprocess
import numpy as np
import cv2
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation as Rot

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
ROOT = os.path.abspath(os.path.join(BASE, '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import render as R   # noqa: E402
import lsgeom        # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

COARSE = 0.20
MM_PER_PX = 0.10 / COARSE
VIEWS = ('back', 'left', 'top')
MASKDIR = os.path.join(HERE, 'masks')
os.makedirs(MASKDIR, exist_ok=True)

MODEL = json.load(open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8'))
LIB, PIVOT = MODEL['library'], np.array(MODEL['pivot'])
NOMINAL = float(MODEL.get('nominal_standoff', lsgeom.NOMINAL_STANDOFF))
xf = json.load(open(os.path.join(HERE, 'robot_to_mesh.json'), encoding='utf-8'))
Rrm, trm = np.array(xf['R']), np.array(xf['t'])
CAMS = json.load(open(os.path.join(HERE, 'b2_cams.json'), encoding='utf-8'))
MC = R.VERTS.mean(0)
A1 = np.array(LIB['v1']['pose_vs_anchor'])

CASES = {
    'v6':   dict(photos=os.path.join(BASE, 'input', 'archive', 'v6'),
                 real=os.path.join(BASE, 'input', 'archive', 'v6', 'ground_truth.ls')),
    'v13':  dict(photos=os.path.join(BASE, 'input', 'archive', 'v13'),
                 real=os.path.join(BASE, 'input', 'archive', 'v13', 'ground_truth.ls')),
    'shop': dict(photos=os.path.join(HERE, 'shop_png'),
                 real=os.path.join(ROOT, '05082026_test1', 'TOR_XL_LEARN_V6_2.LS'),
                 current=os.path.join(ROOT, '05082026_test1', 'TOR_XL_LEARN_V6.ls')),
}

# ------------------------------------------------------- цеховая съёмка: raw -> png
sp = CASES['shop']['photos']
if not os.path.exists(os.path.join(sp, 'back.png')):
    os.makedirs(sp, exist_ok=True)
    for v in VIEWS:
        d = np.fromfile(os.path.join(ROOT, '05082026_test1', f'{v}.raw'), dtype=np.uint8)
        assert d.size == 4096 * 3000, f'{v}.raw: {d.size}'
        cv2.imwrite(os.path.join(sp, f'{v}.png'), d.reshape(3000, 4096))
    print("цеховая съёмка сконвертирована в png")


def masks_of(case):
    """Штатная сегментация, с кэшем. Откат на Otsu запрещён - падаем."""
    from step03_segment_monochrome import segment_image
    out = {}
    for view in VIEWS:
        cache = os.path.join(MASKDIR, f'{case}_{view}.png')
        if not os.path.exists(cache):
            src = os.path.join(CASES[case]['photos'], f'{view}.png')
            m, _, _, _, backend = segment_image(src, view == 'top')
            assert backend != 'otsu', f'{case}/{view}: сегментация ушла на Otsu'
            cv2.imwrite(cache, m)
            print(f"  сегментирован {case}/{view}")
        m = cv2.imread(cache, cv2.IMREAD_GRAYSCALE)
        w, h = int(4096 * COARSE), int(3000 * COARSE)
        m = cv2.resize(m, (w, h), interpolation=cv2.INTER_NEAREST)
        rows = np.where(m.max(1) > 0)[0]
        cut = int(rows.max()) + 1 if len(rows) else None
        out[view] = (m, cut if cut and cut < h - 1 else None)
    return out


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


def fit_pose(mk):
    def cost(v6):
        Rm, tm = pose_to_mesh(v6)
        tot = []
        for view in VIEWS:
            m, cut = mk[view]
            s = CAMOBJ[view].silhouette(pose_R=Rm, pose_t=tm, cutoff_row=cut)
            if np.count_nonzero(s) < 50:
                return 1e3
            tot.append(gap(s, m))
        return float(np.mean(tot))

    P = np.array([LIB[k]['pose_vs_anchor'] for k in LIB])
    lo, hi = P.min(0) - 1.0, P.max(0) + 1.0
    best = (cost(A1), A1.copy())
    rng = np.random.default_rng(5)
    for _ in range(30):
        s = lo + rng.random(6) * (hi - lo)
        c = cost(s)
        if c < best[0]:
            best = (c, s)
    for _ in range(5):
        r = minimize(cost, best[1], method='Nelder-Mead',
                     options=dict(maxiter=1200, xatol=1e-3, fatol=1e-3))
        if r.fun >= best[0] - 1e-4:
            break
        best = (r.fun, r.x)
    return best


REF, _ = lsgeom.cut_surface(
    lsgeom.load(os.path.join(BASE, 'input', 'archive', 'v1', 'ground_truth.ls')), NOMINAL)


def cutline_of(path):
    p = lsgeom.load(path)
    so, _ = lsgeom.fit_standoff(p, REF)
    return lsgeom.cut_surface(p, so)[0]


def stat(pred, target):
    d = lsgeom.curve_distance(pred, target)
    return d.mean(), np.percentile(d, 90), d.max()


print()
print("Генерация .LS по 3D-методу и сравнение с программой оператора")
print("=" * 72)

results = {}
for case, cfg in CASES.items():
    print(f"\n--- {case} ---")
    mk = masks_of(case)
    sil, vec = fit_pose(mk)
    print(f"  поза найдена, остаток силуэта {sil * MM_PER_PX:.2f} мм")
    print(f"  поза: сдвиг {np.round(vec[:3], 2)} мм, углы {np.round(vec[3:], 2)}°")

    sess = f'phys3d_{case}'
    sdir = os.path.join(BASE, 'results', sess)
    os.makedirs(sdir, exist_ok=True)
    json.dump({'tx': float(PIVOT[0]), 'ty': float(PIVOT[1]), 'tz': float(PIVOT[2])},
              open(os.path.join(sdir, 'step02_result.json'), 'w', encoding='utf-8'))
    json.dump({
        'etalon': 'v1', 'selected_neighbors': ['v1'], 'neighbor_weights': [1.0],
        'pivot': [float(x) for x in PIVOT],
        'delta_rel_to_etalon': {
            'x_mm': float(vec[0]), 'y_mm': float(vec[1]), 'z_mm': float(vec[2]),
            'roll_deg': float(vec[3]), 'pitch_deg': float(vec[4]), 'yaw_deg': float(vec[5])},
        'delta_3d': {
            'x_mm': float(vec[0]), 'y_mm': float(vec[1]), 'z_mm': float(vec[2]),
            'roll_deg': float(vec[3]), 'pitch_deg': float(vec[4]), 'yaw_deg': float(vec[5])},
    }, open(os.path.join(sdir, 'step04_result.json'), 'w', encoding='utf-8'))

    r = subprocess.run([sys.executable, os.path.join(BASE, 'scripts',
                                                     'step05_visualize_export.py'),
                        '--session', sess], cwd=BASE, capture_output=True, text=True)
    out = lsgeom.export_path(sdir)
    if r.returncode != 0 or not out:
        print(f"  ЭКСПОРТ НЕ УДАЛСЯ:\n{r.stdout[-800:]}\n{r.stderr[-400:]}")
        continue
    print(f"  записан {os.path.basename(out)}")

    ours = lsgeom.cut_surface(lsgeom.load(out), NOMINAL)[0]
    target = cutline_of(cfg['real'])
    results[case] = {'3d': stat(ours, target), 'nothing': stat(REF, target)}
    if 'current' in cfg:
        results[case]['current'] = stat(cutline_of(cfg['current']), target)

print()
print("=" * 72)
print("Ошибка против программы оператора, по линии реза, мм")
print(f"{'случай':<8}{'метод':<22}{'среднее':>10}{'p90':>8}{'макс':>8}")
print("-" * 58)
NAMES = {'nothing': 'ничего не делать', 'current': 'нынешний пайплайн',
         '3d': '3D по фотографиям'}
for case in CASES:
    if case not in results:
        continue
    for k in ('nothing', 'current', '3d'):
        if k not in results[case]:
            continue
        m, p9, mx = results[case][k]
        print(f"{case:<8}{NAMES[k]:<22}{m:>10.2f}{p9:>8.2f}{mx:>8.2f}")
    print("-" * 58)
