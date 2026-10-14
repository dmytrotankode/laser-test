"""Як саме відрізняються кільця різу різних шоломів: чи потрібен масштаб, і який.

Для кожної пари (еталон -> правда) найкраща підгонка в 3D (без камер) з моделями:
  rigid      - поворот+зсув
  scale      - + однаковий масштаб
  scale_xy   - + окремий масштаб уздовж і впоперек шолома (головні осі кільця) + висоти
  fourier2   - + плавний вигин K=2 (floor_smooth.py)
Плюс: нахил (кут площини кільця) і «ривки» (відхилення від згладженої кривої) у .LS.

    python exp_shape_modes.py
"""
import glob
import os
import sys

import cv2
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

BASE = os.path.dirname(os.path.abspath(__file__))
S21 = os.path.join(BASE, '..', 'service_2021')
sys.path.insert(0, S21)
import ls_points  # noqa: E402


def ring(p, what=2):
    return np.array([q[what] for q in ls_points.read_ring(p)])


def dense(R, n=3000):
    Q = np.r_[R, R[:1]]
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
    t = np.linspace(0, d[-1], n, endpoint=False)
    return np.c_[[np.interp(t, d, Q[:, i]) for i in range(3)]].T


def frame(P):
    """Головні осі кільця: e1 - довжина (найдовша), e2 - ширина, e3 - нормаль площини."""
    c = P.mean(0)
    _, _, Vt = np.linalg.svd(P - c)
    return c, Vt


def fit(A, B, model, yaw_starts):
    tree = cKDTree(dense(B))
    c, Vt = frame(A)
    L = (A - c) @ Vt.T                     # координати в осях еталона
    th = np.arctan2(L[:, 1], L[:, 0])
    F = np.c_[np.ones_like(th), np.cos(th), np.sin(th), np.cos(2 * th), np.sin(2 * th)]
    radial = np.c_[np.cos(th), np.sin(th), 0 * th]

    def shape(p):
        X = L.copy()
        if model == 'scale_xy':                # лише довжина і ширина, висота не масштабується
            X = X * np.exp(np.r_[p[7:9], 0.0])
        if model == 'fourier2':
            X = X + radial * (F @ p[7:12])[:, None]
            X[:, 2] += F @ p[12:17]
        X = X @ Vt + c
        R = cv2.Rodrigues(p[:3])[0]
        s = np.exp(p[6]) if model == 'scale' else 1.0
        return (X - c) @ R.T * s + c + p[3:6]

    n = 7 + {'rigid': 0, 'scale': 0, 'scale_xy': 3, 'fourier2': 10}[model]
    best = None
    for yaw in yaw_starts:
        x0 = np.zeros(n)
        x0[2] = yaw
        x0[3:6] = B.mean(0) - c
        lo, hi = np.full(n, -np.inf), np.full(n, np.inf)
        lo[6:], hi[6:] = -0.1, 0.1             # масштаби ±10 %
        if model == 'fourier2':
            lo[7:], hi[7:] = -8.0, 8.0
        r = least_squares(lambda p: tree.query(shape(p))[0], x0, bounds=(lo, hi))
        if best is None or r.cost < best.cost:
            best = r
    d = tree.query(shape(best.x))[0]
    extra = ''
    if model == 'scale_xy':
        extra = f' (довжина {np.exp(best.x[7]) * 100 - 100:+.1f}%, ширина {np.exp(best.x[8]) * 100 - 100:+.1f}%)'
    if model == 'scale':
        extra = f' (масштаб {np.exp(best.x[6]) * 100 - 100:+.2f}%)'
    return d, extra


def jitter(P):
    """«Ривок» точки: друга різниця |P[i-1] - 2P[i] + P[i+1]| / 2 - наскільки точка
    вибивається з прямої між сусідами, мм (на плавній дузі кроку 13 мм це ~0.1-0.4)."""
    Q = np.r_[P[-1:], P, P[:1]]
    return np.linalg.norm(Q[:-2] - 2 * Q[1:-1] + Q[2:], axis=1) / 2


def tilt(P):
    _, Vt = frame(P)
    nrm = Vt[2] * np.sign(Vt[2][2])
    return np.degrees(np.arccos(abs(nrm[2]))), nrm


if __name__ == '__main__':
    new = {'1010_1': os.path.join(BASE, 'TOR_XL_1010_1.LS'),
           '0510_1': os.path.join(BASE, 'sets_0510', 'TOR_XL_0510_1', 'TOR_XL_0510_1.LS'),
           '0510_2': os.path.join(BASE, 'sets_0510', 'TOR_XL_0510_2', 'TOR_XL_0510_2.LS')}
    print('=== НОВА розстановка: еталон 1010_1 -> правда')
    A = ring(new['1010_1'])
    for k in ('0510_1', '0510_2'):
        B = ring(new[k])
        for m in ('rigid', 'scale', 'scale_xy', 'fourier2'):
            d, ex = fit(A, B, m, np.radians(np.arange(-20, 21, 10)))
            print(f'  -> {k} {m:9s}: середня {d.mean():.2f}, макс {d.max():.2f}, <1мм {np.mean(d < 1) * 100:3.0f}%{ex}')

    print('=== СТАРИЙ архів: еталон v1 -> інші екземпляри (v21-v26, різні шоломи, форми 1 і 4)')
    arch = os.path.join(S21, 'archive')
    A = ring(os.path.join(arch, 'v1', 'ground_truth.ls'))
    for v in ('v21', 'v22', 'v23', 'v24', 'v25', 'v26'):
        p = os.path.join(arch, v, 'ground_truth.ls')
        if not os.path.exists(p):
            continue
        B = ring(p)
        row = []
        for m in ('rigid', 'scale', 'scale_xy', 'fourier2'):
            d, ex = fit(A, B, m, np.radians(np.arange(-20, 21, 10)))
            row.append(f'{m} {d.mean():.2f}/{d.max():.2f}{ex if m == "scale_xy" else ""}')
        print(f'  {v}: ' + ' | '.join(row))

    print('=== нахил площини кільця (від горизонталі) і «ривки» .LS')
    allp = dict(new, **{v: os.path.join(arch, v, 'ground_truth.ls') for v in ('v1', 'v21', 'v22', 'v23', 'v24', 'v25', 'v26')})
    for k, p in allp.items():
        if not os.path.exists(p):
            continue
        cut, noz = ring(p, 2), ring(p, 1)
        t, _ = tilt(cut)
        prog = ls_points.read_ring(p)
        ax = np.array([q[3] for q in prog])
        dang = np.degrees(np.arccos(np.clip((ax[1:] * ax[:-1]).sum(1), -1, 1)))
        jn, jc = jitter(noz), jitter(cut)
        print(f'  {k:7s}: нахил {t:4.1f}°, ривки сопла медіана {np.median(jn):.2f} 90% {np.percentile(jn, 90):.2f} мм, '
              f'лінії різу медіана {np.median(jc):.2f} 90% {np.percentile(jc, 90):.2f} мм, '
              f'кут осі між сусідніми точками медіана {np.median(dang):.1f}° макс {dang.max():.1f}°')
