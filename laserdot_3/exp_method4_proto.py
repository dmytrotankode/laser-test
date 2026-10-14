"""Прототип Методу 4 офлайн, БЕЗ підглядання у правильну відповідь (14.10).

1. Старт - Метод 3 (реальна розмітка оператора back+left, сервіс уже порахував).
2. Згори: край шолома на фото шукається АВТОМАТИЧНО вздовж нормалей до проекції
   поточної лінії (exp_top_edge.edge_offsets) - це і є «розмітка згори», без людини.
3. Підгонка: back+left (реальна розмітка) + top (знайдений край), жорстко або з плавним
   вигином K=2; викиди краю (волокна юбки) приглушує робастна функція втрат.
4. Двічі: після підгонки край шукається знову від нової лінії.
Правильний .LS - ЛИШЕ для оцінки в кінці.

    python exp_method4_proto.py
"""
import json
import os
import sys

import cv2
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import exp_top_silhouette as T  # noqa: E402
import exp_fold_visibility as V  # noqa: E402
from exp_top_edge import edge_offsets  # noqa: E402
from pipeline import camera_model as CM, contour_fit  # noqa: E402

CAMS = T.cams
REF = T.REF
c = REF.mean(0)


def vis_mask(P, w):
    """Які точки лінії P бачить камера w - промінь не перетинає модель шолома в позі P."""
    p = T.pose_to(P)
    tri = T.apply(p, T.TRI.reshape(-1, 3) @ T.R0.T + T.t0).reshape(-1, 3, 3)
    return ~V.occluded(P, CAMS[w][0][3:6], tri)


def top_edge_marks(P, img):
    pc, f = CAMS['top']
    uv, z = CM.project(P, pc[:3], pc[3:6], f)
    D = T.dense(np.c_[uv, np.zeros(len(uv))], 400)[:, :2]
    off = edge_offsets(img, D)
    cc = D.mean(0)
    out = []
    for i, p in enumerate(D):
        t = D[(i + 1) % len(D)] - D[i - 1]
        nrm = np.array([-t[1], t[0]]) / (np.linalg.norm(t) + 1e-9)
        if nrm @ (p - cc) < 0:
            nrm = -nrm
        out.append(p + off[i] * nrm)
    return np.array(out), float(np.median(z)) / f


def fit(marks, vis_ref, K, robust_top=False, mode='sym'):
    th = np.arctan2(REF[:, 1] - c[1], REF[:, 0] - c[0])
    rad = np.c_[np.cos(th), np.sin(th), 0 * th]
    F = np.c_[[np.ones_like(th)] + [g(k * th) for k in range(1, K + 1) for g in (np.cos, np.sin)]].T if K else np.zeros((len(th), 0))
    nb = F.shape[1]

    def shape(p):
        X = REF.copy()
        if nb:
            X = X + rad * (F @ p[7:7 + nb])[:, None]
            X[:, 2] += F @ p[7 + nb:]
        R = cv2.Rodrigues(p[:3])[0]
        return (X - c) @ R.T * np.exp(p[6]) + c + p[3:6]

    def res(p):
        P = shape(p)
        out = []
        for w, (mk, mm) in marks.items():
            pc, f = CAMS[w]
            uv, _ = CM.project(T.dense(P, 600), pc[:3], pc[3:6], f)
            d1 = cKDTree(uv).query(mk)[0] * mm
            uvr, _ = CM.project(P[vis_ref[w]], pc[:3], pc[3:6], f)
            dd, jj = cKDTree(mk).query(uvr)
            if mode == 'trim' and w != 'top':
                # лінія -> розмітка лише там, де найближча точка розмітки НЕ біля її кінця:
                # видимі, але не розмічені оператором ділянки інакше тягнуться до кінця розмітки
                # (обнуляємо, а не викидаємо - довжина нев'язки мусить бути сталою)
                k = len(mk)
                dd = dd * ((jj > 0.05 * k) & (jj < 0.95 * k))
            if mode == 'd1' and w != 'top':
                dd = dd * 0.0
            d2 = dd * mm
            d = np.r_[d1 / np.sqrt(len(d1)), d2 / np.sqrt(max(len(d2), 1))]
            if w == 'top' and robust_top:          # викиди краю (волокна) - не більше ~2 мм впливу
                d = np.sign(d) * np.minimum(np.abs(d), 2.0 / np.sqrt(len(d1)))
            out.append(d * 10)
        out.append(p[7:] * 0.05)
        return np.concatenate(out)

    lo = np.r_[[-0.6] * 3, [-150.0] * 3, -0.35, [-8.0] * (2 * nb)]
    hi = np.r_[[0.6] * 3, [150.0] * 3, 0.35, [8.0] * (2 * nb)]
    return shape(least_squares(res, np.zeros(7 + 2 * nb), method='trf', bounds=(lo, hi), max_nfev=3000).x)


def report(tag, P, truth):
    d = cKDTree(T.dense(truth)).query(P)[0]
    print(f'  {tag:40s} середня {d.mean():.2f}, 90% {np.percentile(d, 90):.2f}, макс {d.max():.2f}, '
          f'<1мм {np.mean(d < 1) * 100:.0f}%, <2мм {np.mean(d < 2) * 100:.0f}%')


if __name__ == '__main__':
    for n in ('nabir-1005-001', 'nabir-1005-002'):
        truth = T.ring(os.path.join(T.S21, 'archive', n, 'ground_truth.ls'))
        m3 = T.ring(os.path.join(T.S21, 'data', 'generated', f'{n}_method3.LS'))
        img = cv2.imread(os.path.join(T.S21, 'archive', n, 'top.png'), 0)
        print(f'=== {n}')
        report('Метод 3 (сервіс, реальна розмітка)', m3, truth)
        marks = {}
        for w in ('back', 'left'):
            pts = np.array(json.load(open(os.path.join(T.S21, 'lines', f'{n}_{w}.json'), encoding='utf-8'))['points'], float)
            pc, f = CAMS[w]
            _, z = CM.project(m3, pc[:3], pc[3:6], f)
            marks[w] = (contour_fit.resample(pts, 200), float(np.median(z)) / f)
        P = m3
        for K, mode in ((0, 'sym'), (0, 'trim'), (0, 'd1'), (2, 'trim'), (2, 'd1')):
            P = m3
            for it in range(2):
                # видимість для точок еталона - за поточною лінією (не за правдою)
                jr = cKDTree(P).query(T.apply(T.pose_to(P), REF))[1]
                vis_ref = {w: vis_mask(P, w)[jr] for w in ('back', 'left')}
                vis_ref['top'] = np.ones(len(REF), bool)
                mk = dict(marks)
                mk['top'] = top_edge_marks(P, img)
                P = fit(mk, vis_ref, K, mode=mode)
            report(f'М4: край згори, {"жорстко" if K == 0 else "+вигин"}, {mode}', P, truth)
