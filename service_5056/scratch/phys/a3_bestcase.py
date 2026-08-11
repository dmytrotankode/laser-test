"""Шаг A3: лучшее, на что CAD способен в принципе.

Вопрос один: может ли силуэт CAD совпасть с фотографией так же хорошо, как
совпадают две фотографии одного шлема между собой? Ракурс, дистанция, фокус,
доворот и сдвиг ищутся свободно, на одном варианте. Это верхняя граница
качества CAD - калибровка её улучшить не может.

Три предыдущие версии этого замера давали разные ответы, и каждый раз причиной
был поиск, а не модель. Что здесь сделано против этого:

  * грубый перебор ракурса по сетке И случайные старты - берём лучшее из обоих,
    потому что поодиночке каждый проигрывал другому на каком-нибудь виде;
  * полировка на вдвое большем разрешении: при сильном уменьшении кадра мелкий
    шаг параметра часто не меняет маску вовсе, у функции появляются плоские
    полки, и Nelder-Mead на них встаёт;
  * лучший результат хранится в bestcase.json и берётся стартом при следующем
    запуске - так число может только улучшаться, а не прыгать от прогона
    к прогону.
"""
import os
import sys
import json
import numpy as np
import cv2
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation as Rot

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render as R  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Одно разрешение. Двухступенчатость была нужна, пока рендер сыпался на
# крупном кадре (россыпь точек редела, силуэт распадался). После перехода на
# честную растеризацию треугольников по одному он корректен на любом масштабе
# и вчетверо быстрее, так что просто берём разрешение повыше.
COARSE = FINE = 0.20

# Полный кадр даёт ~0.08-0.12 мм/px в зависимости от камеры; берём 0.10.
MM_PER_PX = 0.10 / COARSE
STORE = os.path.join(HERE, 'bestcase.json')

# Ручки объёма поиска. Полная подгонка одного вида - это сотни стартов плюс
# полировки, около 30-40 мс на пробу, то есть единицы минут. Для замеров, где
# видов много, объём режется отсюда, а не правкой кода.
N_RANDOM = 60
N_POLISH = 12
MAXITER = 1500
C = R.VERTS.mean(0)
START = {
    'back': ((0, -1, 0), 2700.0, 21928.0),
    'left': ((-1, 0, 0), 1700.0, 22354.0),
    'top':  ((0, 0, 1), 2000.0, 23410.0),
}


def make_cam(p, scale):
    """p = [rx, ry, rz, log_dist, log_f, px, py]

    Поворот камеры задан ВЕКТОРОМ ВРАЩЕНИЯ, а не парой «азимут-наклон» плюс
    доворот. Прежняя схема строила матрицу через «смотреть из точки в точку» с
    вертикалью как опорой, а у верхнего вида направление взгляда почти совпадает
    с вертикалью - там опора скачком переключалась на другую ось, и картинка
    разворачивалась рывком. У параметризации был разрыв ровно на том виде,
    который и оказался худшим. У вектора вращения особых точек нет.
    """
    rv, ld, lf, px, py = p[:3], p[3], p[4], p[5], p[6]
    dist, f = np.exp(ld), np.exp(lf)
    Rm = Rot.from_rotvec(rv).as_matrix()
    eye = C - Rm.T @ np.array([0.0, 0.0, dist])     # центр меша -> центр кадра
    mm_px = dist / (f * scale)
    k = COARSE / scale
    return R.Camera(f, Rm, -Rm @ eye + np.array([px * mm_px / k, py * mm_px / k, 0]),
                    scale=scale)


def gap(a, b):
    out = []
    for x, y in ((a, b), (b, a)):
        cs, _ = cv2.findContours(x, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not cs:
            return 1e3
        pts = max(cs, key=cv2.contourArea)[:, 0, :]
        do = cv2.distanceTransform(255 - y, cv2.DIST_L2, 3)
        di = cv2.distanceTransform(y, cv2.DIST_L2, 3)
        v = np.where(y[pts[:, 1], pts[:, 0]] > 0,
                     di[pts[:, 1], pts[:, 0]], do[pts[:, 1], pts[:, 0]])
        out.append(float(np.abs(v).mean()))
    return sum(out) / 2


def center(m):
    M = cv2.moments(m)
    return (M['m10'] / M['m00'], M['m01'] / M['m00']) if M['m00'] else (0, 0)


def fit_view(view, variant, store):
    d, dist, foc = START[view]
    eye0 = C + np.asarray(d, float) * dist
    rv0 = Rot.from_matrix(R.look_at(eye0, C)).as_rotvec()
    p0 = np.array([rv0[0], rv0[1], rv0[2], np.log(dist), np.log(foc), 0.0, 0.0])

    refs, cuts = {}, {}
    for s in (COARSE, FINE):
        refs[s], cuts[s] = R.load_mask(variant, view, s)

    def cost(p, s):
        try:
            m = make_cam(p, s).silhouette(cutoff_row=cuts[s])
        except Exception:
            return 1e3
        if np.count_nonzero(m) < 50:
            return 1e3
        return gap(m, refs[s]) * (COARSE / s)          # приводим к пикселям COARSE

    cx1, cy1 = center(refs[COARSE])

    def recenter(p):
        p = p.copy()
        c0 = center(make_cam(p, COARSE).silhouette(cutoff_row=cuts[COARSE]))
        p[5] += cx1 - c0[0]; p[6] += cy1 - c0[1]
        return p

    # Кандидаты по повороту: вокруг стартового ракурса (доворот вокруг оси
    # взгляда + небольшие отклонения) плюс равномерная случайная выборка по
    # всем ориентациям - на случай, если стартовая догадка неверна вовсе.
    R0 = Rot.from_rotvec(p0[:3])
    cands = [recenter(p0)]
    for spin in np.linspace(-np.pi, np.pi, 16, endpoint=False):
        for tilt_ax in ((1, 0, 0), (0, 1, 0)):
            for tilt in (-0.35, -0.15, 0.0, 0.15, 0.35):
                dR = (Rot.from_rotvec(np.array([0.0, 0.0, spin])) *
                      Rot.from_rotvec(np.asarray(tilt_ax, float) * tilt))
                p = p0.copy(); p[:3] = (dR * R0).as_rotvec()
                cands.append(recenter(p))
    rng = np.random.default_rng(1)
    for _ in range(N_RANDOM):
        p = p0.copy()
        p[:3] = Rot.random(random_state=int(rng.integers(1 << 30))).as_rotvec()
        p[3] += rng.normal(0, 0.2)
        cands.append(recenter(p))
    if view in store:
        cands.append(np.array(store[view]['p']))

    scored = sorted(((cost(p, COARSE), i) for i, p in enumerate(cands)))
    best = (scored[0][0], cands[scored[0][1]])
    for val, i in scored[:N_POLISH]:
        r = minimize(cost, cands[i], args=(COARSE,), method='Nelder-Mead',
                     options=dict(maxiter=MAXITER, xatol=1e-3, fatol=1e-3))
        if r.fun < best[0]:
            best = (r.fun, r.x)
    for _ in range(5):                                  # полировка на FINE
        r = minimize(cost, best[1], args=(FINE,), method='Nelder-Mead',
                     options=dict(maxiter=2500, xatol=1e-4, fatol=1e-4))
        cur = cost(best[1], FINE)
        if r.fun >= cur - 1e-4:
            break
        best = (r.fun, r.x)
    return cost(best[1], FINE), best[1], refs, cuts


store = {}
if os.path.exists(STORE):
    with open(STORE, encoding='utf-8') as f:
        store = json.load(f)

VAR = 'v1'
print(f"Свободный ракурс, вариант {VAR}. Контроль - маска v2 вместо CAD.")
print(f"Полировка на масштабе {FINE}; числа приведены к пикселям масштаба {COARSE}.")
print()
print(f"{'вид':<7}{'CAD':>18}{'контроль (фото v2)':>19}")
print("-" * 46)

panels = []
for view in ('back', 'left', 'top'):
    val, par, refs, cuts = fit_view(view, VAR, store)
    prev = store.get(view, {}).get('val')
    if prev is None or val < prev:
        store[view] = {'val': float(val), 'p': [float(x) for x in par]}
    else:
        val, par = prev, np.array(store[view]['p'])

    v2 = R.load_mask('v2', view, COARSE)[0]
    ctrl = gap(v2, refs[COARSE])
    print(f"{view:<7}{val:>7.2f} px{val * MM_PER_PX:>8.2f} мм"
          f"{ctrl:>9.2f} px{ctrl * MM_PER_PX:>8.2f} мм")

    m = make_cam(par, COARSE).silhouette(cutoff_row=cuts[COARSE])
    ref = refs[COARSE]
    h, w = ref.shape
    vis = np.zeros((h, w, 3), np.uint8)
    vis[:, :, 2] = m; vis[:, :, 1] = ref
    vis[cv2.bitwise_and(m, ref) > 0] = (0, 255, 255)
    cv2.putText(vis, f"{view} RED=CAD GREEN=photo {val:.1f}px", (8, 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1)
    panels.append(vis)

with open(STORE, 'w', encoding='utf-8') as f:
    json.dump(store, f, indent=1)
cv2.imwrite(os.path.join(HERE, 'a3_bestcase.png'), np.hstack(panels))
print()
print("Контроль - предел, ниже которого не бывает: две съёмки одного шлема.")
