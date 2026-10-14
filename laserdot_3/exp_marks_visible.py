"""Те саме, що exp_marks_views.py, але ЧЕСНО: кожна камера «розмічає» лише ті ділянки
лінії, які вона справді бачить (exp_fold_visibility.py - промінь до камери не перетинає
3D-модель шолома). У exp_marks_views для top бралось ВСЕ кільце - а згори перед шолома
закритий куполом (видно ~60 %), тож ті цифри для top були завищені.

Розмітка = точна проекція правильної лінії (без похибки оператора) на видимих ділянках.
Нев'язка: кожна точка розмітки -> до лінії підгонки (вся проекція кільця); кожна видима
точка підгонки -> до найближчої точки розмітки.

    python exp_marks_visible.py
"""
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
from pipeline import camera_model as CM  # noqa: E402

CAMS = dict(T.cams, right=V.right_cam())
REF = T.REF
c = REF.mean(0)


def visible_mask(truth, w):
    p = T.pose_to(truth)
    tri = T.apply(p, T.TRI.reshape(-1, 3) @ T.R0.T + T.t0).reshape(-1, 3, 3)
    return ~V.occluded(truth, CAMS[w][0][3:6], tri)


def make_marks(truth, vis):
    """Щільні точки правди на видимих ділянках, спроєктовані в камеру."""
    D = T.dense(truth, 3000)
    j = cKDTree(truth).query(D)[1]
    out = {}
    for w, m in vis.items():
        pc, f = CAMS[w]
        uv, z = CM.project(D[m[j]], pc[:3], pc[3:6], f)
        out[w] = (uv[::max(1, len(uv) // 200)], float(np.median(z)) / f)
    return out


def fit(marks, vis_ref, K):
    th = np.arctan2(REF[:, 1] - c[1], REF[:, 0] - c[0])
    rad = np.c_[np.cos(th), np.sin(th), 0 * th]
    F = np.c_[[np.ones_like(th)] + [f(k * th) for k in range(1, K + 1) for f in (np.cos, np.sin)]].T if K else np.zeros((len(th), 0))
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
            d1 = cKDTree(uv).query(mk)[0]
            uvr, _ = CM.project(P[vis_ref[w]], pc[:3], pc[3:6], f)
            d2 = cKDTree(mk).query(uvr)[0]
            out.append(np.r_[d1 / np.sqrt(len(d1)), d2 / np.sqrt(len(d2))] * mm * 10)
        out.append(p[7:] * 0.05)
        return np.concatenate(out)

    lo = np.r_[[-0.6] * 3, [-150.0] * 3, -0.35, [-8.0] * (2 * nb)]
    hi = np.r_[[0.6] * 3, [150.0] * 3, 0.35, [8.0] * (2 * nb)]
    return shape(least_squares(res, np.zeros(7 + 2 * nb), method='trf', bounds=(lo, hi), max_nfev=3000).x)


if __name__ == '__main__':
    for n in ('nabir-1005-001', 'nabir-1005-002'):
        truth = T.ring(os.path.join(T.S21, 'archive', n, 'ground_truth.ls'))
        vis = {w: visible_mask(truth, w) for w in CAMS}
        # видимість для точок ЕТАЛОНА - за тим самим індексом найближчої точки правди
        jr = cKDTree(truth).query(T.apply(T.pose_to(truth), REF))[1]
        vis_ref = {w: m[jr] for w, m in vis.items()}
        tree = cKDTree(T.dense(truth))
        print(f'=== {n}: видно back {vis["back"].mean()*100:.0f}%, left {vis["left"].mean()*100:.0f}%, '
              f'top {vis["top"].mean()*100:.0f}%, right {vis["right"].mean()*100:.0f}%, '
              f'хоч одна з back/left {(vis["back"] | vis["left"]).mean()*100:.0f}%, '
              f'+top {(vis["back"] | vis["left"] | vis["top"]).mean()*100:.0f}%, +right {(vis["back"] | vis["left"] | vis["right"]).mean()*100:.0f}%')
        for views in (('back', 'left'), ('back', 'left', 'top'), ('back', 'left', 'right'), ('back', 'left', 'right', 'top')):
            mk = make_marks(truth, {w: vis[w] for w in views})
            for K in (0, 2):
                d = tree.query(fit(mk, vis_ref, K))[0]
                print(f'  {"+".join(views):20s} {"жорстко" if K == 0 else "+вигин":8s}: середня {d.mean():.2f}, 90% {np.percentile(d, 90):.2f}, '
                      f'макс {d.max():.2f}, <1мм {np.mean(d < 1) * 100:.0f}%, <2мм {np.mean(d < 2) * 100:.0f}%')
