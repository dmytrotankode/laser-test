"""Калібровка камер за маркерними точками 30.09 - променева постановка.

Та сама математика, що service_3030/exp_marker_calib.py (там докладні пояснення):
точка лежить ДЕСЬ на осі інструмента, що виходить із сопла; камера бачить її в
відомому пікселі -> промінь інструмента і промінь зору мусять перетнутись. Міра -
найкоротша відстань між прямими, у мм. Відступ сопла знати не треба.
Скопійовано сюди (а не імпортовано з 3030), щоб працювало від цієї папки.

Пікселі точок - pixels.json ({view: {label: [u, v]}}), координати пульта -
points_pendant.csv.

    python calib_rays.py           -> калібровка + перевірка виключенням
"""
import csv
import json
import os

import cv2
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

BASE = os.path.dirname(os.path.abspath(__file__))
W_IMG, H_IMG = 4096, 3000
FOCUS = {'back': 22655.68, 'left': 22766.74, 'top': 22700.0}   # як 18.08, закріплені
VIEWS = ('back', 'left', 'top')


def nozzles():
    out = []
    for r in csv.DictReader(open(os.path.join(BASE, 'points_pendant.csv'), encoding='utf-8')):
        pos = np.array([float(r['X']), float(r['Y']), float(r['Z'])])
        axis = Rotation.from_euler('ZYX', [float(r['R']), float(r['P']), float(r['W'])],
                                   degrees=True).apply([0.0, 0.0, 1.0])
        out.append(dict(label=r['label'], point=r['point'], repeat=r['repeat'] != '0',
                        pos=pos, dir=-axis))
    return out


def observations(view, px, noz, with_repeats=False):
    have = px.get(view, {})
    return [(n['label'], n['pos'], n['dir'], np.asarray(have[n['label']], float))
            for n in noz if n['label'] in have and (with_repeats or not n['repeat'])]


def gap_mm(p6, obs, focus):
    R = cv2.Rodrigues(np.asarray(p6[:3], float).reshape(3, 1))[0]
    C = np.asarray(p6[3:6], float)
    out = []
    for _, pos, dirn, uv in obs:
        ray = R.T @ np.array([(uv[0] - W_IMG / 2) / focus, (uv[1] - H_IMG / 2) / focus, 1.0])
        u, v = dirn / np.linalg.norm(dirn), ray / np.linalg.norm(ray)
        w0 = pos - C
        a, b, c, d, e = u @ u, u @ v, v @ v, u @ w0, v @ w0
        den = a * c - b * b
        if abs(den) < 1e-12:
            out.append(1e3)
            continue
        s, t = (b * e - c * d) / den, (a * e - b * d) / den
        out.append(float(np.linalg.norm((pos + s * u) - (C + t * v))))
    return np.array(out)


def in_front(p6, obs):
    R = cv2.Rodrigues(np.asarray(p6[:3], float).reshape(3, 1))[0]
    C = np.asarray(p6[3:6], float)
    z = np.array([(R @ (o[1] - C))[2] for o in obs])
    return np.maximum(0.0, 100.0 - z)


def pnp_naive(obs, focus):
    P3 = np.array([o[1] for o in obs], np.float64)
    P2 = np.array([o[3] for o in obs], np.float64)
    K = np.array([[focus, 0, W_IMG / 2], [0, focus, H_IMG / 2], [0, 0, 1]])
    _, rvec, tvec = cv2.solvePnP(P3, P2, K, None, flags=cv2.SOLVEPNP_ITERATIVE)
    R = cv2.Rodrigues(rvec)[0]
    return np.r_[rvec.ravel(), -R.T @ tvec.ravel()]


def fit_rays(obs, focus, x0):
    def resid(p):
        return np.concatenate([gap_mm(p, obs, focus), in_front(p, obs)])
    return least_squares(resid, x0, method='lm', max_nfev=3000).x


MIN_DEPTH = 1000.0   # камери стоять за 1.8-2.8 м; ближче - хибний мінімум


def median_depth(p6, obs):
    R = cv2.Rodrigues(np.asarray(p6[:3], float).reshape(3, 1))[0]
    return float(np.median([(R @ (o[1] - p6[3:6]))[2] for o in obs]))


def solve(obs, focus, extra_starts=()):
    """Кілька стартів: solvePnP на всіх точках і на кожній підмножині без однієї.
    Спіймано 14.10 на back: зі старту solvePnP по всіх 13 точках підгонка сідала
    в хибний мінімум (камера за 400 мм від шолома, остаток 1-4 мм), хоча правильне
    рішення (2.8 м, остаток 0.1 мм) поруч. Відкидаємо рішення ближче MIN_DEPTH."""
    starts = [pnp_naive(obs, focus), *extra_starts]
    if len(obs) >= 7:
        starts += [pnp_naive([o for j, o in enumerate(obs) if j != i], focus) for i in range(len(obs))]
    best = None
    for start in starts:
        q = fit_rays(obs, focus, start)
        if in_front(q, obs).max() > 0 or median_depth(q, obs) < MIN_DEPTH:
            continue
        e = float(np.median(gap_mm(q, obs, focus)))
        if best is None or e < best[0]:
            best = (e, q)
    return best[1] if best else fit_rays(obs, focus, pnp_naive(obs, focus))


def project(p6, focus, P):
    R = cv2.Rodrigues(np.asarray(p6[:3], float).reshape(3, 1))[0]
    Xc = (np.asarray(P, float) - p6[3:6]) @ R.T
    return np.c_[focus * Xc[:, 0] / Xc[:, 2] + W_IMG / 2, focus * Xc[:, 1] / Xc[:, 2] + H_IMG / 2], Xc[:, 2]


def leave_one_out(obs, focus):
    loo = []
    for i in range(len(obs)):
        rest = [o for j, o in enumerate(obs) if j != i]
        q = solve(rest, focus)
        loo.append(float(gap_mm(q, [obs[i]], focus)[0]))
    return np.array(loo)


def main():
    noz = nozzles()
    px = json.load(open(os.path.join(BASE, 'pixels.json'), encoding='utf-8'))
    result = {}
    for view in VIEWS:
        obs = observations(view, px, noz)
        if len(obs) < 6:
            print(f'{view}: точок {len(obs)} - мало')
            continue
        f = FOCUS[view]
        p = solve(obs, f)
        g = gap_mm(p, obs, f)
        loo = leave_one_out(obs, f)
        rep = observations(view, px, noz, with_repeats=True)
        rep = [o for o in rep if '_' in o[0]]
        g_rep = gap_mm(p, rep, f) if rep else np.array([])
        R = cv2.Rodrigues(p[:3])[0]
        zc = np.array([(R @ (o[1] - p[3:6]))[2] for o in obs])
        print(f'=== {view}: {len(obs)} точок, фокус {f:.0f}, позиція {p[3:6].round(0)}, '
              f'дальність {np.median(zc):.0f} мм')
        print(f'   остаток медіана {np.median(g):.2f} мм, макс {g.max():.2f} ({obs[int(g.argmax())][0]})')
        print(f'   ПЕРЕВІРКА виключенням: медіана {np.median(loo):.2f}, макс {loo.max():.2f}, '
              f'найгірші {[obs[i][0] for i in np.argsort(-loo)[:3]]}')
        if len(g_rep):
            print(f'   повтори (не в підгонці): {dict(zip([o[0] for o in rep], g_rep.round(2)))}')
        result[view] = np.r_[p, f]
    return result


if __name__ == '__main__':
    main()
