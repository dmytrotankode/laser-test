"""Що дає розмітка з різних ракурсів на РЕАЛЬНИХ шоломах 05.10 (14.10).

Правда = кільце різу з .LS набору (оператор/програма під цей шолом).
Розмітка = ТОЧНА проекція правди в камеру (без шуму оператора) - тобто
вимірюємо лише те, що залежить від геометрії камер і від того, що еталон
іншої форми. Еталон = TOR_XL_1010_1. Підгонка - як у Методі 3 (симетрична
відстань до розмітки у мм на деталі), варіанти:
  * ракурси: back+left (як зараз) / back+left+top (top - усе кільце);
  * модель: жорстко+масштаб (Метод 3) / + плавний вигин K=2 (floor_smooth.py).

    python exp_marks_views.py
"""
import os
import sys

import cv2
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

S21 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'service_2021')
sys.path.insert(0, S21)
import ls_points  # noqa: E402
from pipeline import contour_fit, camera_model as CM  # noqa: E402

BASE = os.path.dirname(os.path.abspath(__file__))
cams = contour_fit.marker_cams(os.path.join(S21, 'calib', 'cameras', 'marker_2026-09-30'))


def ring(p):
    return np.array([q[2] for q in ls_points.read_ring(p)])


REF = ring(os.path.join(BASE, 'TOR_XL_1010_1.LS'))
SETS = {s: ring(os.path.join(BASE, 'sets_0510', f'TOR_XL_{s}', f'TOR_XL_{s}.LS')) for s in ('0510_1', '0510_2')}


def visible(P, w):
    pc, f = cams[w]
    uv, z = CM.project(P, pc[:3], pc[3:6], f)
    if w == 'top':                       # згори видно все кільце
        return np.r_[uv, uv[:1]], z
    return CM.near_arc(uv, z), z


def marks_of(truth, views):
    return {w: contour_fit.resample(visible(truth, w)[0], 150) for w in views}


def fit(marks, K):
    c = REF.mean(0)
    th = np.arctan2(REF[:, 1] - c[1], REF[:, 0] - c[0])
    rad = np.c_[np.cos(th), np.sin(th), np.zeros_like(th)]
    F = np.c_[[np.ones_like(th)] + [f(k * th) for k in range(1, K + 1) for f in (np.cos, np.sin)]].T if K else np.zeros((len(th), 0))
    nb = F.shape[1]

    def shape(p):
        R = cv2.Rodrigues(p[:3])[0]
        X = REF.copy()
        if nb:
            X = X + rad * (F @ p[7:7 + nb])[:, None]
            X[:, 2] += F @ p[7 + nb:]
        return (X - c) @ R.T * np.exp(p[6]) + c + p[3:6]

    def res(p):
        P = shape(p)
        out = []
        for w, m in marks.items():
            pc, f = cams[w]
            vis, z = visible(P, w)
            vis = contour_fit.resample(vis, 150)
            out.append(np.r_[np.abs(CM.dist_to_polyline(m, vis)), np.abs(CM.dist_to_polyline(vis, m))] * np.median(z) / f)
        out.append(p[7:] * 0.05)          # м'яко тримати вигин малим, де розмітка не вимагає
        return np.concatenate(out)

    lo = np.r_[[-0.6] * 3, [-150.0] * 3, -0.35, [-8.0] * (2 * nb)]
    hi = np.r_[[0.6] * 3, [150.0] * 3, 0.35, [8.0] * (2 * nb)]
    x = least_squares(res, np.zeros(7 + 2 * nb), method='trf', bounds=(lo, hi), max_nfev=3000).x
    return shape(x)


def dense(R, n=3000):
    Q = np.r_[R, R[:1]]
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
    t = np.linspace(0, d[-1], n, endpoint=False)
    return np.c_[[np.interp(t, d, Q[:, i]) for i in range(3)]].T


if __name__ == '__main__':
    for s, truth in SETS.items():
        tree = cKDTree(dense(truth))
        d0 = tree.query(REF)[0]
        print(f'=== {s}: еталон як є - середня {d0.mean():.2f}, макс {d0.max():.2f} мм')
        for views in (('back', 'left'), ('back', 'left', 'top')):
            for K in (0, 2):
                P = fit(marks_of(truth, views), K)
                d = tree.query(P)[0]
                print(f'  {"+".join(views):15s} {"жорстко" if K == 0 else "+вигин K=2":10s}: '
                      f'середня {d.mean():.2f}, 90% {np.percentile(d, 90):.2f}, макс {d.max():.2f} мм, <1мм {np.mean(d < 1) * 100:.0f}%')
