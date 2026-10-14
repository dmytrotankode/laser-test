"""Як розмітка оператора (лінія ЗГИНУ) співвідноситься з правильною лінією РІЗУ (.LS) - на
всіх наборах, де є і те, і те (14.10).

Гіпотеза з 12.08 (пам'ять проєкту, service_3030 exp_camera_joint.py): лінія згину на фото =
записана лінія різу, зсунута на +2.3 мм ВЗДОВЖ ОСІ ІНСТРУМЕНТА (своєї в кожній точці).
Тут: для зсуву o вздовж осі - проекція (різ + o*вісь) у back/left камерою рецепта набору,
середня відстань розмітки до неї (мм на деталі). Яке o найкраще - і чи стабільно воно.
v1, v10-v16 - один майстер-шолом; v20-v25 - інші екземпляри (v22, v23 - розмітка
«сумнівна» зі слів замовника, HANDOFF 13.08); nabir-1005-* - нова розстановка.

    python exp_marks_vs_truth.py
"""
import json
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

BASE = os.path.dirname(os.path.abspath(__file__))
S21 = os.path.abspath(os.path.join(BASE, '..', 'service_2021'))
sys.path.insert(0, S21)
import ls_points  # noqa: E402
from pipeline import generate as gen, contour_fit, camera_model as CM  # noqa: E402

SETS = ['v1', 'v10', 'v11', 'v12', 'v13', 'v14', 'v15', 'v16', 'v20', 'v21', 'v22', 'v23', 'v24', 'v25',
        'nabir-0909-001', 'nabir-1005-001', 'nabir-1005-002']
OFFS = [-2.0, 0.0, 1.0, 2.3, 3.5, 5.0]


def dense_idx(P, n=1500):
    Q = np.r_[P, P[:1]]
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
    t = np.linspace(0, d[-1], n, endpoint=False)
    return np.c_[[np.interp(t, d, Q[:, i]) for i in range(Q.shape[1])]].T


if __name__ == '__main__':
    best_all = []
    for v in SETS:
        gt = os.path.join(gen.ARCHIVE, v, 'ground_truth.ls')
        if not os.path.exists(gt) or not all(os.path.exists(os.path.join(S21, 'lines', f'{v}_{w}.json')) for w in ('back', 'left')):
            continue
        prog = ls_points.read_ring(gt)
        cut = np.array([p[2] for p in prog])
        ax = np.array([p[3] for p in prog])
        cams = contour_fit.marker_cams(os.path.join(gen.CALIB, 'cameras', gen.recipe_for(v)['camera_calibration']))
        row, per_o = [], {}
        for o in OFFS:
            P = dense_idx(np.c_[cut + o * ax])
            tot = []
            for w in ('back', 'left'):
                mk = contour_fit.resample(np.array(json.load(open(os.path.join(S21, 'lines', f'{v}_{w}.json'), encoding='utf-8'))['points'], float), 150)
                pc, f = cams[w]
                uv, z = CM.project(P, pc[:3], pc[3:6], f)
                uv = uv[z < np.median(z)]
                tot.append(cKDTree(uv).query(mk)[0] * float(np.median(z)) / f)
            per_o[o] = np.concatenate(tot).mean()
        b = min(per_o, key=per_o.get)
        best_all.append((v, b))
        tag = 'майстер' if v in ('v1', 'v10', 'v11', 'v12', 'v13', 'v14', 'v15', 'v16') else ('нова' if '1005' in v else 'інший')
        print(f'{v:15s} ({tag:7s}): ' + '  '.join(f'{o:+.1f}:{per_o[o]:.2f}' for o in OFFS) + f'   найкраще {b:+.1f}')
