"""Лазерная проба, шаг 2: согласуются ли камеры с координатами робота?

Ничего не подгоняется. Берутся камеры, найденные в 3D-ветке (b2_cams.json), и
связка станок<->меш (robot_to_mesh.json), и проверяется предсказание:

  1. КОНТРОЛЬ НА ИЗВЕСТНОМ ОТВЕТЕ. Позиция сопла известна из пульта. Её проекция
     обязана лечь на изображение сопла в кадре. Если не ложится - дальше идти
     незачем, ошибка в связке координат, а не в пятне;

  2. ОСНОВНАЯ ПРОВЕРКА. Луч идёт из сопла вдоль оси инструмента (Fanuc W/P/R ->
     tool +Z, направлен ОТ детали, значит к детали это -Z). Спроецированный в
     кадр, он обязан пройти ЧЕРЕЗ найденное пятно. Мерой служит расстояние от
     пятна до этой линии в пикселях.

Почему именно расстояние до линии, а не до точки: положение пятна вдоль луча
зависит от того, где поверхность, а этого мы пока не знаем. Поперёк луча -
знаем, и это честная проверка.
"""
import os
import sys
import csv
import json
import numpy as np
import cv2
from scipy.spatial.transform import Rotation as Rot

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
ROOT = os.path.abspath(os.path.join(BASE, '..'))
PHYS = os.path.join(BASE, 'scratch', 'phys')
DATA = os.path.join(ROOT, 'laserdot_1')
sys.path.insert(0, PHYS)
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import render as R      # noqa: E402
import lsgeom           # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CAMS = json.load(open(os.path.join(PHYS, 'b2_cams.json'), encoding='utf-8'))
xf = json.load(open(os.path.join(PHYS, 'robot_to_mesh.json'), encoding='utf-8'))
Rrm, trm = np.array(xf['R']), np.array(xf['t'])
MC = R.VERTS.mean(0)
SPOTS = json.load(open(os.path.join(HERE, 'L1_candidates.json')))
ROWS = [r for r in csv.DictReader(
    l for l in open(os.path.join(DATA, 'positions.csv'), encoding='utf-8')
    if not l.startswith('#'))]


def make_cam(view, scale=1.0):
    p = np.array(CAMS[view]['p'])
    Rc = Rot.from_rotvec(p[:3]).as_matrix()
    dist, f = np.exp(p[3]), np.exp(p[4])
    eye = MC - Rc.T @ np.array([0.0, 0.0, dist])
    mm_px = dist / (f * scale)
    return R.Camera(f, Rc, -Rc @ eye + np.array([p[5] * mm_px, p[6] * mm_px, 0]),
                    scale=scale)


CAM = {v: make_cam(v) for v in ('back', 'left', 'top')}


def to_mesh(p):
    """Точка в координатах станка -> координаты меша (та же связка, что в c1/b3)."""
    return Rrm @ np.asarray(p, float) + trm


def tool_axis(w, p, r):
    """Ось инструмента +Z в координатах станка. Смотрит ОТ детали."""
    return lsgeom.rot_from_ypr(r, p, w).apply([0.0, 0.0, 1.0])


print()
print("Проекция известных величин в кадр, пиксели полного кадра 4096x3000")
print("=" * 78)
print(f"{'кадр':<15}{'сопло -> (u, v)':>22}{'пятно (u, v)':>20}"
      f"{'до луча':>10}{'вдоль':>9}")
print("-" * 78)

rows = []
for rec in ROWS:
    pos = np.array([float(rec[k]) for k in 'xyz'])
    w, p, r = (float(rec[k]) for k in ('w', 'p', 'r'))
    ax = tool_axis(w, p, r)
    for view in rec['frames'].split('+'):
        key = f"pos{rec['pos']}_{view}"
        if key not in SPOTS or not SPOTS[key]:
            continue
        spot = np.array([SPOTS[key][0]['x'], SPOTS[key][0]['y']])
        cam = CAM[view]
        # две точки луча: сопло и точка в 60 мм по направлению к детали
        A = to_mesh(pos)
        B = to_mesh(pos - 60.0 * ax)
        (uv, bad) = cam.project(np.array([A, B]))
        if bad.any():
            print(f"{key:<15}{'за камерой':>22}")
            continue
        a, b = uv[0], uv[1]
        d = b - a
        n = np.linalg.norm(d)
        t = float((spot - a) @ d / (n * n))
        perp = float(np.linalg.norm(spot - (a + t * d)))
        rows.append(dict(key=key, view=view, perp=perp, along=t * n,
                         nozzle=a.tolist(), spot=spot.tolist()))
        print(f"{key:<15}{a[0]:>13.0f},{a[1]:>7.0f}"
              f"{spot[0]:>13.0f},{spot[1]:>6.0f}{perp:>10.0f}{t * n:>9.0f}")

print("-" * 78)
for view in ('back', 'left', 'top'):
    v = [x['perp'] for x in rows if x['view'] == view]
    if v:
        print(f"  {view:<6} отклонение пятна от луча: медиана {np.median(v):>7.0f} px, "
              f"диапазон {min(v):.0f}-{max(v):.0f}")

print()
print("Как читать: если бы камеры и робот были согласованы, отклонение пятна от")
print("спроецированного луча измерялось бы десятками пикселей (пятно само ~40 px).")
print("Колонка «вдоль» показывает, на каком расстоянии по лучу лежит пятно —")
print("физически это должно быть около отступа сопла, то есть порядка 10 мм.")

# картинка: луч и пятно на кадре
os.makedirs(os.path.join(HERE, 'L2_out'), exist_ok=True)
for rec in ROWS[:6]:
    pos = np.array([float(rec[k]) for k in 'xyz'])
    ax = tool_axis(*(float(rec[k]) for k in ('w', 'p', 'r')))
    for view in rec['frames'].split('+'):
        key = f"pos{rec['pos']}_{view}"
        f = os.path.join(DATA, f'{key}.raw')
        if not os.path.exists(f) or key not in SPOTS or not SPOTS[key]:
            continue
        img = np.fromfile(f, dtype=np.uint8).reshape(3000, 4096)
        vis = cv2.cvtColor(cv2.resize(img, (1024, 750)), cv2.COLOR_GRAY2BGR)
        uv, bad = CAM[view].project(np.array([to_mesh(pos), to_mesh(pos - 60 * ax)]))
        if not bad.any():
            cv2.line(vis, tuple((uv[0] / 4).astype(int)), tuple((uv[1] / 4).astype(int)),
                     (255, 128, 0), 2)
            cv2.circle(vis, tuple((uv[0] / 4).astype(int)), 8, (255, 0, 0), 2)
        s = SPOTS[key][0]
        cv2.circle(vis, (int(s['x'] / 4), int(s['y'] / 4)), 16, (0, 0, 255), 2)
        cv2.imwrite(os.path.join(HERE, 'L2_out', f'{key}.png'), vis)
print("\nкартинки с лучом: L2_out/*.png (синий - сопло и луч, красный - пятно)")
