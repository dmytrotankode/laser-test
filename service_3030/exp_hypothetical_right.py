"""Помогла бы камера СПРАВА (зеркально к left) так же, как top, или хуже?

Строим гипотетическую камеру: зеркально отражаем left относительно
вертикальной плоскости (ось Z станка + горизонтальное направление на back,
как приближение сагиттальной плоскости шлема). Реальных снимков с неё нет и
быть не может - но для анализа наблюдаемости (матрица чувствительности,
SVD) реальные пиксели не нужны, нужна только ГЕОМЕТРИЯ проекции: как
меняются координаты силуэта при малом повороте/сдвиге позы. Это можно
посчитать для любой гипотетической камеры без единого снимка.

Сравниваются те же три слабых сингулярных числа (exp_three_cams.py, случай
"силуэт(3)"), с реальной top и с гипотетической right - на одних и тех же
вариантах, одной и той же схемой (силуэт = 3 опорных числа, не полный контур,
чтобы сравнение было честным: контур с right тоже не посчитать без снимка).

    python exp_hypothetical_right.py
"""
import os
import sys
import numpy as np
import cv2
from scipy.optimize import least_squares

BASE = os.path.dirname(os.path.abspath(__file__))
S5056 = os.path.abspath(os.path.join(BASE, '..', 'service_5056'))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(S5056, 'scripts'))

import fit_model, line_features                          # noqa: E402
import export_scene as XS, export_ls as X                 # noqa: E402
import exp_cad_fit as F, exp_camera_fit as E               # noqa: E402
import exp_all_methods as A, exp_observability as O        # noqa: E402
import exp_three_cams as T                                  # noqa: E402
from bench import dist_to_polyline                          # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def mirror_camera(cam_left, pivot, d_back):
    """Зеркальное отражение камеры left относительно вертикальной плоскости
    через pivot, содержащей ось Z и горизонтальное направление на back."""
    p6, f = cam_left
    C = p6[3:6]
    z_axis = np.array([0.0, 0.0, 1.0])
    d_h = d_back.copy()
    d_h[2] = 0.0
    d_h /= np.linalg.norm(d_h)
    n = np.cross(z_axis, d_h)
    n /= np.linalg.norm(n)
    M = np.eye(3) - 2 * np.outer(n, n)

    C_right = M @ (C - pivot) + pivot
    R_left = cv2.Rodrigues(p6[:3])[0]
    R_right = M @ R_left @ M
    rvec_right = cv2.Rodrigues(R_right)[0].ravel()
    return np.r_[rvec_right, C_right], f


def box_of(V, cam):
    pc, f = cam
    uv, z = E.project(V, pc[:3], pc[3:6], f)
    return np.array([uv[:, 1].min(), uv[:, 0].min(), uv[:, 0].max()]), float(np.median(z)), f


def make_resid(variant, rim, verts, marks, cams, R0, t0, extra_view, target):
    """Как exp_three_cams.make_resid, но третий вид - словарь {name: (cam, want)},
    want задан заранее (не читается из фото - для гипотетической камеры его нет)."""
    off = A.FOLD_RADIAL * A.radial(rim)
    off[:, 2] += A.FOLD_UP

    def resid(p):
        R = cv2.Rodrigues(p[:3])[0] @ R0
        fold = (rim + off) @ R.T + t0 + p[3:6]
        V = verts @ R.T + t0 + p[3:6]
        out = []
        for w in ('back', 'left'):
            pc, f = cams[w]
            uv, z = E.project(fold, pc[:3], pc[3:6], f)
            d = np.abs(dist_to_polyline(X.resample(marks[variant][w]), E.near_arc(uv, z)))
            out.append(d * float(np.median(z)) / f / np.sqrt(len(d)))
        for w in ('back', 'left'):
            got, mm, f = box_of(V, cams[w])
            want = np.array(T.mask_box3(variant, w))
            out.append((got - want) * mm / f / np.sqrt(3))
        got, mm, f = box_of(V, extra_view)
        out.append((got - target) * mm / f / np.sqrt(3))
        return np.concatenate(out)
    return resid


def main():
    marks = line_features.load_marks()
    rim = XS.mesh_rim(F.STL)
    verts = np.unique(F.load_stl(F.STL).reshape(-1, 3), axis=0)
    cams = T.marker_cams()
    R0, t0 = A.cad_start()

    d_back = cams['back'][0][3:6] - A.PIVOT
    right_cam = mirror_camera(cams['left'], A.PIVOT, d_back)
    print(f'гипотетическая right: позиция {right_cam[0][3:6].round(0)}  '
          f'(для сравнения left {cams["left"][0][3:6].round(0)}, '
          f'back {cams["back"][0][3:6].round(0)})\n')

    print(f"{'вариант':<7}{'третья камера':<14}{'сингулярные числа (низ->верх)':<42}")
    for v in O.CLEAN[:3]:                      # трёх вариантов достаточно для геометрического сравнения
        fit_model.standoff(v)
        V0 = verts @ R0.T + t0

        for label, cam3, use_real_target in (('top (реальная)', cams['top'], True),
                                              ('right (гипотеза)', right_cam, False)):
            if use_real_target:
                target = np.array(T.mask_box3(v, 'top'))
            else:
                target, _, _ = box_of(V0, cam3)   # своя цель в нуле - для SVD достаточно
            resid = make_resid(v, rim, verts, marks, cams, R0, t0, cam3, target)
            r = least_squares(resid, np.zeros(6), method='lm', max_nfev=400)
            S = np.linalg.svd(r.jac, full_matrices=False)[1]
            sv = S / S.max()
            print(f'{v:<7}{label:<14}{np.array2string(np.round(sv, 4), separator=" ")}')
        print()


if __name__ == '__main__':
    main()
