"""Калибровка камер по маркерным точкам 18.08 (laserdot_2).

ЧТО НЕ ТАК В ГОТОВОМ ФАЙЛЕ. В `calib_correspondences.csv` за трёхмерную
координату точки взята координата СОПЛА с пульта. Но точка лежит примерно в
10 мм от сопла вдоль оси инструмента, а ориентация сопла у разных точек своя -
W/P/R гуляют на десятки градусов. Значит в каждой строке сидит ошибка около
сантиметра, направленная каждый раз по-разному. Калибровка по таким данным не
может не испортиться.

КАК ПРАВИЛЬНО (постановка §4e). Отступ знать не нужно вовсе:

    точка лежит ГДЕ-ТО на оси инструмента, выходящей из сопла,
    и камера видит её в известном пикселе,

значит луч инструмента и луч зрения обязаны ПЕРЕСЕКАТЬСЯ. Мерой служит
кратчайшее расстояние между этими прямыми, сразу в миллиметрах. Расстояние вдоль
луча - свободный параметр, который решается сам.

Здесь считаются оба способа рядом, чтобы разница была видна числом, а не на
словах. Проверка - предсказание точки, исключённой из подгонки.
"""
import os
import sys
import csv
import json
import numpy as np
import cv2
from scipy.optimize import least_squares

BASE = os.path.dirname(os.path.abspath(__file__))
S5056 = os.path.abspath(os.path.join(BASE, '..', 'service_5056'))
DATA = os.path.abspath(os.path.join(BASE, '..', 'laserdot_2'))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(S5056, 'scripts'))

import lsgeom                                            # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

W_IMG, H_IMG = 4096, 3000
FOCUS = {'back': 22655.68, 'left': 22766.74, 'top': 22700.0}
VIEWS = ('back', 'left', 'top')


def nozzles():
    """Все подходы сопла: положение и направление оси к детали."""
    out = []
    for r in csv.DictReader(open(os.path.join(DATA, 'points_dry.csv'), encoding='utf-8')):
        pos = np.array([float(r['X']), float(r['Y']), float(r['Z'])])
        w, p, rr = float(r['W']), float(r['P']), float(r['R'])
        axis = lsgeom.rot_from_ypr(rr, p, w).apply([0.0, 0.0, 1.0])
        out.append(dict(point=r['point'], repeat=bool(r['repeat_of']),
                        pos=pos, dir=-np.asarray(axis, float)))
    return out


def pixels(source='csv', fname='points_pixels_weighted.json', drop_flagged=False):
    """Пиксели точек. ДВА ИСТОЧНИКА, и они расходятся не только числами.

    На `back` и `top` в json один и тот же пиксель подписан точкой 13, а в csv -
    точкой 19. Это разные точки, стоящие в 200 мм друг от друга: подпись 13 даёт
    в подгонку заведомо ложное соответствие. На `left` подмены нет, и `left` по
    json считается чисто - что и указывает на источник беды.
    """
    if source == 'json':
        d = json.load(open(os.path.join(DATA, fname), encoding='utf-8'))
        return {v: {str(q['point']): np.array([q['x'], q['y']]) for q in d.get(v, [])}
                for v in VIEWS}
    out = {v: {} for v in VIEWS}
    for r in csv.DictReader(open(os.path.join(DATA, 'calib_correspondences.csv'),
                                 encoding='utf-8')):
        if drop_flagged and r['status'] != 'ok':
            continue
        out[r['view']][r['point']] = np.array([float(r['u']), float(r['v'])])
    return out


def observations(view, px, noz, first_only=True):
    """Пары «луч инструмента - пиксель». Повторы по умолчанию не берём:

    у них та же точка, и в подгонке они дали бы ей двойной вес. Зато они
    отдельно годятся как проверка ошибки инструмента.
    """
    have = px.get(view, {})
    out = []
    for n in noz:
        if n['point'] in have and (not n['repeat'] or not first_only):
            out.append((n['point'], n['pos'], n['dir'], have[n['point']]))
    return out


def gap_mm(p6, obs, focus):
    """Кратчайшее расстояние между лучом инструмента и лучом зрения, мм."""
    R = cv2.Rodrigues(np.asarray(p6[:3], float).reshape(3, 1))[0]
    C = np.asarray(p6[3:6], float)
    out = []
    for _, pos, dirn, uv in obs:
        ray = R.T @ np.array([(uv[0] - W_IMG / 2) / focus,
                              (uv[1] - H_IMG / 2) / focus, 1.0])
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


def pnp_naive(obs, focus):
    """Способ из готового файла: координата СОПЛА выдаётся за координату точки."""
    P3 = np.array([o[1] for o in obs], np.float64)
    P2 = np.array([o[3] for o in obs], np.float64)
    K = np.array([[focus, 0, W_IMG / 2], [0, focus, H_IMG / 2], [0, 0, 1]])
    ok, rvec, tvec = cv2.solvePnP(P3, P2, K, None, flags=cv2.SOLVEPNP_ITERATIVE)
    R = cv2.Rodrigues(rvec)[0]
    C = -R.T @ tvec.ravel()
    return np.r_[rvec.ravel(), C]


def in_front(p6, obs):
    """Насколько точки оказались ЗА камерой, мм (0 - все перед ней).

    Критерий пересечения прямых знака не различает: камера, зеркально
    перенесённая на другую сторону сцены и развёрнутая, даёт ту же прямую
    зрения и ту же невязку. На `top` подгонка именно так и ушла - камера встала
    под шлемом и смотрела от него, а остаток и проверка исключением остались
    отличными. Поэтому глубина проверяется отдельно.
    """
    R = cv2.Rodrigues(np.asarray(p6[:3], float).reshape(3, 1))[0]
    C = np.asarray(p6[3:6], float)
    z = np.array([(R @ (o[1] - C))[2] for o in obs])
    return np.maximum(0.0, 100.0 - z)


def fit_rays(obs, focus, x0):
    def resid(p):
        return np.concatenate([gap_mm(p, obs, focus), in_front(p, obs)])
    return least_squares(resid, x0, method='lm', max_nfev=2000).x


def start_for(view):
    p = os.path.join(BASE, 'data', f'cam_{view}.npy')
    if os.path.exists(p):
        return np.load(p)[:6]
    p = os.path.join(BASE, 'data', 'cam_top_try.npy')
    if view == 'top' and os.path.exists(p):
        return np.load(p)[:6]
    return None


def main():
    noz = nozzles()
    px = pixels()
    print(f'подходов сопла: {len(noz)} (из них повторов {sum(n["repeat"] for n in noz)})\n')

    for view in VIEWS:
        obs = observations(view, px, noz)
        if len(obs) < 6:
            print(f'{view}: точек {len(obs)} - мало, пропускаю')
            continue
        f = FOCUS[view]
        x0 = start_for(view)
        naive = pnp_naive(obs, f)
        # Стартов два, и оба нужны. solvePnP смещён отступом (он считает сопло
        # точкой), но сторону камеры определяет правильно - а лучевая постановка
        # от отступа свободна, зато знака не различает и умеет уйти за сцену.
        # Берём лучшее из решений, у которых точки перед камерой.
        best = None
        for start in [naive] + ([x0] if x0 is not None else []):
            q = fit_rays(obs, f, start)
            if in_front(q, obs).max() > 0:
                continue
            e = float(np.median(gap_mm(q, obs, f)))
            if best is None or e < best[0]:
                best = (e, q)
        p = best[1] if best else fit_rays(obs, f, naive)
        g_ray = gap_mm(p, obs, f)
        g_naive = gap_mm(naive, obs, f)
        print(f'=== {view}: {len(obs)} точек, фокус {f:.0f}')
        print(f'   лучевая постановка: остаток медиана {np.median(g_ray):.2f} мм, '
              f'макс {g_ray.max():.2f}')
        print(f'   способ из файла:    остаток медиана {np.median(g_naive):.2f} мм, '
              f'макс {g_naive.max():.2f}')
        print(f'   камеры расходятся на {np.linalg.norm(p[3:6] - naive[3:6]):.0f} мм')

        # Проверка исключением должна повторять ту же процедуру, что и основная
        # подгонка, иначе меряет не её. В частности стартовать из решения на
        # ОСТАВШИХСЯ точках, а не из общего ответа и не из чужого начального
        # приближения.
        loo = []
        for i in range(len(obs)):
            rest = [o for j, o in enumerate(obs) if j != i]
            cand = []
            for start in [pnp_naive(rest, f)] + ([x0] if x0 is not None else []):
                q = fit_rays(rest, f, start)
                if in_front(q, rest).max() == 0:
                    cand.append((float(np.median(gap_mm(q, rest, f))), q))
            q = min(cand)[1] if cand else fit_rays(rest, f, pnp_naive(rest, f))
            loo.append(float(gap_mm(q, [obs[i]], f)[0]))
        loo = np.array(loo)
        R = cv2.Rodrigues(p[:3])[0]
        zc = np.array([(R @ (o[1] - p[3:6]))[2] for o in obs])
        print(f'   точки перед камерой: глубина {zc.min():.0f}..{zc.max():.0f} мм '
              + ('OK' if zc.min() > 0 else 'ПРОВАЛ, камера не с той стороны'))
        print(f'   ПРОВЕРКА исключением: медиана {np.median(loo):.2f} мм, '
              f'макс {loo.max():.2f}, худшие точки '
              f'{[obs[i][0] for i in np.argsort(-loo)[:3]]}')
        np.save(os.path.join(BASE, 'data', f'cam_{view}_marker.npy'), np.r_[p, f])
    print('\nсохранено в data/cam_*_marker.npy (в расчёты пока не подключено)')


if __name__ == '__main__':
    main()
