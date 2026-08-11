"""Лазерная проба, шаг 4: калибровка без предположения об отступе.

В шаге 3 точка пятна строилась как "сопло минус общий отступ d". Контроль это
предположение не подтвердил: подогнанный d вышел 1.2 мм для back и 17.4 для
left вместо рабочих ~10, а проверка исключением по одной точке дала 71-231 px.
Скорее всего отступ у каждой точки свой - сопло подводили джогом, а не по
программе.

Здесь отступ не нужен вовсе. Используется только то, что известно точно:

    пятно лежит ГДЕ-ТО на луче робота,
    и камера видит его в известном пикселе.

Значит луч робота и луч зрения камеры обязаны ПЕРЕСЕКАТЬСЯ. Мерой служит
кратчайшее расстояние между этими двумя прямыми - и оно сразу в миллиметрах,
что куда честнее пикселей: видно, попадаем ли мы в требуемую десятую долю
миллиметра или мажем на сантиметр.

Неизвестных шесть (поза камеры), уравнений - по одному на точку. При семи
точках запас всего один, поэтому одного лишь малого остатка недостаточно:
обязательна проверка исключением по одной точке, и именно она здесь главная.
"""
import os
import sys
import csv
import json
import numpy as np
import cv2
from scipy.optimize import least_squares

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
INIT = json.load(open(os.path.join(HERE, 'L3_cameras.json')))
ROWS = [r for r in csv.DictReader(
    l for l in open(os.path.join(DATA, 'positions.csv'), encoding='utf-8')
    if not l.startswith('#'))]
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
        out.append((key, pos, -axis, np.array([s['x'], s['y']])))   # -axis: к детали
    return out


def gap_mm(params, obs, focus):
    """Кратчайшее расстояние между лучом робота и лучом зрения, мм, для каждой точки."""
    Rm = cv2.Rodrigues(params[:3].reshape(3, 1))[0]
    C = params[3:6]                       # центр камеры в координатах станка
    out = []
    for _, pos, dirn, uv in obs:
        # луч зрения: из центра камеры через пиксель
        ray = Rm.T @ np.array([(uv[0] - W / 2.0) / focus,
                               (uv[1] - H / 2.0) / focus, 1.0])
        ray /= np.linalg.norm(ray)
        u, v = dirn / np.linalg.norm(dirn), ray
        w0 = pos - C
        a, b, c = u @ u, u @ v, v @ v
        d, e = u @ w0, v @ w0
        den = a * c - b * b
        if abs(den) < 1e-12:
            out.append(1e3)
            continue
        s = (b * e - c * d) / den
        t = (a * e - b * d) / den
        out.append(float(np.linalg.norm((pos + s * u) - (C + t * v))))
    return np.array(out)


def fit(view, obs, x0):
    """При исключении точки уравнений может стать меньше, чем неизвестных (6),
    и 'lm' на это не рассчитан - тогда берётся 'trf'. Решение в таком случае
    недоопределено, о чём и говорит вывод."""
    f = FOCUS[view]
    method = 'lm' if len(obs) >= 6 else 'trf'
    r = least_squares(lambda p: gap_mm(p, obs, f), x0, method=method,
                      xtol=1e-12, ftol=1e-12, max_nfev=20000)
    return r.x, gap_mm(r.x, obs, f)


print()
print("Калибровка по условию «лучи пересекаются». Остаток — в МИЛЛИМЕТРАХ")
print("=" * 76)

out = {}
for view in ('back', 'left'):
    obs = observations(view)
    Rm0 = cv2.Rodrigues(np.array(INIT[view]['rvec']))[0]
    C0 = -Rm0.T @ np.array(INIT[view]['tvec'])
    x0 = np.concatenate([np.array(INIT[view]['rvec']), C0])

    x, g = fit(view, obs, x0)
    print(f"\n--- {view}: {len(obs)} точек, неизвестных 6 ---")
    print(f"  остаток по точкам, мм: {np.round(g, 2)}")
    print(f"  RMS {np.sqrt((g ** 2).mean()):.2f} мм, худший {g.max():.2f} мм")
    C = x[3:6]
    print(f"  камера в {np.round(C, 0)} мм, до сцены "
          f"{np.linalg.norm(C - np.mean([p for _, p, *_ in obs], 0)):.0f} мм")

    hold = []
    for i in range(len(obs)):
        tr = obs[:i] + obs[i + 1:]
        xi, _ = fit(view, tr, x0)
        hold.append(float(gap_mm(xi, [obs[i]], FOCUS[view])[0]))
    note = "" if len(obs) - 1 >= 6 else "  (недоопределено: уравнений меньше шести)"
    print(f"  ПРОВЕРКА исключением по одной: медиана {np.median(hold):.2f} мм, "
          f"худшая {max(hold):.2f} мм{note}")
    for (k, *_), h in zip(obs, hold):
        print(f"    {k:<14}{h:>8.2f} мм")
    out[view] = dict(x=x.tolist(), gap=g.tolist(), holdout=hold,
                     points=[k for k, *_ in obs], focus=FOCUS[view])

json.dump(out, open(os.path.join(HERE, 'L4_cameras.json'), 'w'), indent=1)
print()
print("Как читать: остаток на обучающих точках при шести неизвестных и шести-семи")
print("уравнениях мал почти автоматически - смотреть надо на строку ПРОВЕРКА.")
print("Она показывает, что предсказывает калибровка для точки, которой не видела.")
