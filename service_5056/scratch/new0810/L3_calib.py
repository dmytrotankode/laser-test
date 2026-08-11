"""Лазерная проба, шаг 3: калибровка камер ПРЯМО в координатах станка.

Шаг 2 показал, что связка станок<->меш из 3D-ветки (robot_to_mesh.json) с
реальностью не сходится: проекция сопла промахивается мимо самого сопла на
сотни пикселей. Здесь она не используется вовсе - камеры ищутся сразу в
координатах станка, по парам "координата робота <-> пиксель пятна".

Идея, которая делает задачу разрешимой. Точка пятна известна почти полностью:
она лежит на оси инструмента, на расстоянии отступа от сопла. Отступ - рабочий,
порядка 10 мм, и он общий для съёмки. Значит:

    P_i(d) = позиция_сопла_i - d * ось_инструмента_i

и задача превращается в обычную PnP: известны трёхмерные точки и их пиксели,
ищется поза камеры. Отступ d уточняется снаружи, по минимуму ошибки перепроекции.

Проверки, без которых результату верить нельзя:

  * ОСТАТОК ПЕРЕПРОЕКЦИИ. Должен опуститься до величины порядка размера пятна
    (~40 px). Если останется сотни - модель неверна;
  * КОНТРОЛЬ НА ИЗВЕСТНОМ ОТВЕТЕ. Найденный отступ обязан выйти около 10 мм.
    Это число ниоткуда в расчёт не подставляется, оно получается из подгонки, и
    совпадение с рабочим отступом - независимое подтверждение;
  * ИСКЛЮЧЕНИЕ ПО ОДНОЙ ТОЧКЕ. Калибровка по N-1 точкам и проверка на оставшейся
    показывает, не подогнались ли мы под шум.

top не калибруется: на него всего два кадра, а нужно минимум четыре.
"""
import os
import sys
import csv
import json
import numpy as np
import cv2
from scipy.optimize import minimize_scalar
from scipy.spatial.transform import Rotation as Rot

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
ROOT = os.path.abspath(os.path.join(BASE, '..'))
PHYS = os.path.join(BASE, 'scratch', 'phys')
DATA = os.path.join(ROOT, 'laserdot_1')
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import lsgeom   # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

W, H = 4096, 3000
CAMS = json.load(open(os.path.join(PHYS, 'b2_cams.json'), encoding='utf-8'))
SPOTS = json.load(open(os.path.join(HERE, 'L1_candidates.json')))
ROWS = [r for r in csv.DictReader(
    l for l in open(os.path.join(DATA, 'positions.csv'), encoding='utf-8')
    if not l.startswith('#'))]

# Фокусы берутся из 3D-ветки: там они сошлись на 1 % по независимым подгонкам и
# совпали с калибровкой по ChArUco-доске на 1-3 %. Это единственное, что из той
# ветки переносится - позы камер и связка координат не используются.
FOCUS = {v: float(np.exp(CAMS[v]['p'][4])) for v in CAMS}


def observations(view):
    out = []
    for rec in ROWS:
        if view not in rec['frames'].split('+'):
            continue
        key = f"pos{rec['pos']}_{view}"
        if key not in SPOTS or not SPOTS[key]:
            continue
        pos = np.array([float(rec[k]) for k in 'xyz'])
        w, p, r = (float(rec[k]) for k in ('w', 'p', 'r'))
        axis = lsgeom.rot_from_ypr(r, p, w).apply([0.0, 0.0, 1.0])
        s = SPOTS[key][0]
        out.append((key, pos, axis, np.array([s['x'], s['y']])))
    return out


def K_of(view):
    f = FOCUS[view]
    return np.array([[f, 0, W / 2.0], [0, f, H / 2.0], [0, 0, 1.0]])


def solve(view, obs, d):
    """Поза камеры при заданном отступе d. Возвращает (rvec, tvec, ошибки)."""
    P = np.array([pos - d * axis for _, pos, axis, _ in obs], dtype=np.float64)
    uv = np.array([s for *_, s in obs], dtype=np.float64)
    K = K_of(view)
    ok, rvec, tvec = cv2.solvePnP(P, uv, K, None, flags=cv2.SOLVEPNP_EPNP)
    if not ok:
        return None
    rvec, tvec = cv2.solvePnPRefineLM(P, uv, K, None, rvec, tvec)
    proj, _ = cv2.projectPoints(P, rvec, tvec, K, None)
    err = np.linalg.norm(proj.reshape(-1, 2) - uv, axis=1)
    return rvec, tvec, err


def best_d(view, obs, lo=0.0, hi=60.0):
    def cost(d):
        r = solve(view, obs, float(d))
        return 1e6 if r is None else float(np.sqrt((r[2] ** 2).mean()))
    res = minimize_scalar(cost, bounds=(lo, hi), method='bounded',
                          options=dict(xatol=1e-3))
    return float(res.x), float(res.fun)


print()
print("Калибровка камер по лазерным точкам, в координатах станка")
print("=" * 76)

result = {}
for view in ('back', 'left', 'top'):
    obs = observations(view)
    print(f"\n--- {view}: {len(obs)} точек "
          f"({', '.join(k.split('_')[0] for k, *_ in obs)}) ---")
    if len(obs) < 4:
        print("  меньше четырёх точек - калибровать нечем, пропуск")
        continue

    d, rms = best_d(view, obs)
    rvec, tvec, err = solve(view, obs, d)
    Rm = cv2.Rodrigues(rvec)[0]
    eye = -Rm.T @ tvec.ravel()
    print(f"  подобранный отступ: {d:.1f} мм   (рабочий - около 10 мм)")
    print(f"  остаток перепроекции: RMS {rms:.0f} px, "
          f"по точкам {np.round(err, 0)}")
    print(f"  камера стоит в {np.round(eye, 0)} мм, "
          f"расстояние до сцены {np.linalg.norm(eye - np.mean([p for _, p, *_ in obs], 0)):.0f} мм")

    # исключение по одной точке: подогнались ли мы под шум
    hold = []
    for i in range(len(obs)):
        tr = obs[:i] + obs[i + 1:]
        if len(tr) < 4:
            continue
        dd, _ = best_d(view, tr)
        rr = solve(view, tr, dd)
        if rr is None:
            continue
        P = np.array([obs[i][1] - dd * obs[i][2]])
        proj, _ = cv2.projectPoints(P, rr[0], rr[1], K_of(view), None)
        hold.append(float(np.linalg.norm(proj.reshape(2) - obs[i][3])))
    if hold:
        print(f"  проверка исключением по одной: медиана {np.median(hold):.0f} px, "
              f"худшая {max(hold):.0f} px")
    result[view] = dict(d=d, rms=rms, rvec=rvec.ravel().tolist(),
                        tvec=tvec.ravel().tolist(), focus=FOCUS[view],
                        err=err.tolist(), holdout=hold,
                        points=[k for k, *_ in obs])

json.dump(result, open(os.path.join(HERE, 'L3_cameras.json'), 'w'), indent=1)
print()
print("Как читать: пятно на снимке около 40 px в поперечнике, поэтому остаток")
print("того же порядка означает, что геометрия сошлась. Отдельно смотреть на")
print("подобранный отступ - он нигде не задаётся и обязан выйти около 10 мм.")
