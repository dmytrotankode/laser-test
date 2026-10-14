"""Чи варто враховувати зазор між лінією згину (що розмічає оператор) і лінією різу.

Метод 3 підганяє ЛІНІЮ РІЗУ еталона прямо під розмітку ЛІНІЇ ЗГИНУ, без зсуву. Тут
перед підгонкою еталон зсувається на (radial, up) мм - «де була б лінія згину», - а
результатом береться та сама поза, застосована до лінії різу. Сітка зсувів на реальній
розмітці nabir-1005-001/002.

    python exp_fold_offset.py
"""
import json
import os
import sys

import cv2
import numpy as np
from scipy.optimize import least_squares

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import exp_marks_views as X  # noqa: E402
from eval_real_marks import S21, ring, line_dist  # noqa: E402
from pipeline import contour_fit, camera_model as CM  # noqa: E402

REF = X.REF
c = REF.mean(0)
rad = REF - c
rad[:, 2] = 0
rad /= np.linalg.norm(rad, axis=1, keepdims=True)


def fit_with_offset(marks, radial, up):
    fold = REF + radial * rad + np.c_[0 * rad[:, 0], 0 * rad[:, 0], np.full(len(REF), up)]

    def tf(p, A):
        R = cv2.Rodrigues(p[:3])[0]
        return (A - c) @ R.T * np.exp(p[6]) + c + p[3:6]

    def res(p):
        P = tf(p, fold)
        out = []
        for w, m in marks.items():
            vis, z = X.visible(P, w)
            vis = contour_fit.resample(vis, 150)
            f = X.cams[w][1]
            out.append(np.r_[np.abs(CM.dist_to_polyline(m, vis)), np.abs(CM.dist_to_polyline(vis, m))] * np.median(z) / f)
        return np.concatenate(out)

    b = (np.r_[[-0.6] * 3, [-150.0] * 3, -0.35], np.r_[[0.6] * 3, [150.0] * 3, 0.35])
    x = least_squares(res, np.zeros(7), method='trf', bounds=b, max_nfev=3000).x
    return tf(x, REF)


if __name__ == '__main__':
    for n in ('nabir-1005-001', 'nabir-1005-002'):
        truth = ring(os.path.join(S21, 'archive', n, 'ground_truth.ls'))
        marks = {w: contour_fit.resample(np.array(json.load(open(os.path.join(S21, 'lines', f'{n}_{w}.json'), encoding='utf-8'))['points'], float), 150)
                 for w in ('back', 'left')}
        print('===', n)
        for radial in (-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0):
            for up in (-2.0, 0.0, 2.0):
                d = line_dist(fit_with_offset(marks, radial, up), truth)
                print(f'  radial {radial:+.0f} up {up:+.0f}: середня {d.mean():.2f}, 90% {np.percentile(d, 90):.2f}, макс {d.max():.2f}, <2мм {np.mean(d < 2) * 100:.0f}%')
