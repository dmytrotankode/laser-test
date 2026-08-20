"""Можно ли определить ширину шлема по двум снимкам вместе с позой.

Зачем. Габарит линии реза, померенный прямо по записанным программам, показал:
чужие экземпляры ШИРЕ мастер-шлема на 3.0 мм (264.6 против 261.6, разброс внутри
групп 0.4-0.8). Модель сделана по мастеру и с ним совпадает. Значит одна модель
на все шлемы даёт систематическую ошибку около 3 мм - столько же, сколько вся
ошибка, за которую идёт борьба.

Выход: искать ширину вместе с позой, по тем же двум снимкам. Седьмой параметр -
масштаб модели вдоль её короткой оси.

САМОПРОВЕРКА, ради которой опыт и ставится: истинная ширина каждого шлема
известна из его же программы, а подгонка её не видит - она работает только по
фотографиям. Если найденная ширина совпадёт с истинной, параметр настоящий.
Если нет, но при этом траектория улучшится - значит он просто подворовывает из
мягких направлений позы, и такому улучшению грош цена.

Печатается и то, и другое, плюс сингулярные числа - не стала ли подгонка
вырожденной от лишнего параметра.
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

import lsgeom                                            # noqa: E402
import fit_model                                         # noqa: E402
import line_features                                     # noqa: E402
import export_scene as XS                                # noqa: E402
import export_ls as X                                    # noqa: E402
import exp_cad_fit as F                                  # noqa: E402
import exp_camera_fit as E                               # noqa: E402
import exp_all_methods as A                              # noqa: E402
import exp_observability as O                            # noqa: E402
from bench import dist_to_polyline                       # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def short_axis(P):
    """Габарит кривой по короткой оси - та самая «ширина между ушами»."""
    c = P.mean(0)
    Q = P - c
    vt = np.linalg.svd(Q, full_matrices=False)[2]
    ext = sorted((Q @ vt[0]).ptp() if hasattr(Q @ vt[0], 'ptp') else
                 (Q @ vt[0]).max() - (Q @ vt[0]).min() for _ in [0])
    a = Q @ vt[0]
    b = Q @ vt[1]
    return min(a.max() - a.min(), b.max() - b.min())


def fit(variant, rim0, verts0, marks, cams, R0, t0, free_width):
    """Поза (+ ширина). Смещение сгиба закреплено, силуэт как в лучшей настройке."""
    def build(s):
        sc = np.array([s, 1.0, 1.0])            # локальный X модели - короткая ось
        rim = rim0 * sc
        nrm = A.radial(rim)
        off = A.FOLD_RADIAL * nrm
        off[:, 2] += A.FOLD_UP
        return rim, rim + off, verts0 * sc

    def resid(p):
        s = p[6] if free_width else 1.0
        rim, fold0, verts = build(s)
        R = cv2.Rodrigues(p[:3])[0] @ R0
        fold = fold0 @ R.T + t0 + p[3:6]
        out = []
        for w in O.VIEWS:
            pc, f = cams[w]
            uv, z = E.project(fold, pc[:3], pc[3:6], f)
            d = np.abs(dist_to_polyline(X.resample(marks[variant][w]), E.near_arc(uv, z)))
            mm = float(np.median(z)) / f
            out.append(d * mm / np.sqrt(len(d)))
            got = O.model_box(np.r_[p[:6]], verts, cams, w, R0, t0)
            want = np.array(O.mask_box(variant, w))
            out.append((got - want) * mm / np.sqrt(3))
        return np.concatenate(out)

    x0 = np.r_[np.zeros(6), 1.0]
    r = least_squares(resid, x0, method='lm', max_nfev=800)
    s = r.x[6] if free_width else 1.0
    rim, _, _ = build(s)
    R = cv2.Rodrigues(r.x[:3])[0] @ R0
    return rim @ R.T + t0 + r.x[3:6], s, r


def main():
    marks = line_features.load_marks()
    rim0 = XS.mesh_rim(F.STL)
    verts0 = np.unique(F.load_stl(F.STL).reshape(-1, 3), axis=0)
    cams = X.cameras()
    R0, t0 = A.cad_start()
    w_cad = short_axis(rim0)
    print(f'ширина кромки модели: {w_cad:.1f} мм\n')

    print(f"{'вариант':<7}{'шлем':<8}{'истинная':>10}{'найдена':>10}{'ошибка':>9}"
          f"{'без ширины: сред/макс/доп':>28}{'с шириной':>26}")
    rows = []
    for v in O.CLEAN:
        fit_model.standoff(v)
        own = E.ring(v, 0.0)
        w_true = short_axis(own)
        P0, _, _ = fit(v, rim0, verts0, marks, cams, R0, t0, False)
        P1, s, r1 = fit(v, rim0, verts0, marks, cams, R0, t0, True)
        d0 = lsgeom.curve_distance(P0, own)
        d1 = lsgeom.curve_distance(P1, own)
        w_fit = w_cad * s
        rows.append((v, w_true, w_fit, d0, d1, r1))
        kind = 'мастер' if v in A.MASTER else 'чужой'
        print(f'{v:<7}{kind:<8}{w_true:>10.1f}{w_fit:>10.1f}{w_fit - w_true:>+9.1f}'
              f'{d0.mean():>12.2f}/{d0.max():<6.2f}{100 * np.mean(d0 <= 2):>4.0f}%'
              f'{d1.mean():>12.2f}/{d1.max():<6.2f}{100 * np.mean(d1 <= 2):>4.0f}%',
              flush=True)

    err = np.array([r[2] - r[1] for r in rows])
    print(f'\nширина: ошибка {err.mean():+.2f} ± {err.std():.2f} мм, '
          f'по модулю в среднем {np.abs(err).mean():.2f}')
    print('   (разница между группами шлемов, которую надо было поймать: 3.0 мм)')
    for nm, grp in (('мастер', [r for r in rows if r[0] in A.MASTER]),
                    ('чужие', [r for r in rows if r[0] not in A.MASTER])):
        a0 = np.array([(r[3].mean(), r[3].max(), 100 * np.mean(r[3] <= 2)) for r in grp])
        a1 = np.array([(r[4].mean(), r[4].max(), 100 * np.mean(r[4] <= 2)) for r in grp])
        print(f'{nm:<8} без ширины {a0[:, 0].mean():5.2f}/{a0[:, 1].mean():5.2f}/'
              f'{a0[:, 2].mean():3.0f}%    с шириной {a1[:, 0].mean():5.2f}/'
              f'{a1[:, 1].mean():5.2f}/{a1[:, 2].mean():3.0f}%')
    S = np.linalg.svd(rows[0][5].jac, compute_uv=False)
    print(f'\nсингулярные числа с семью параметрами: {np.round(S / S.max(), 4)}')


if __name__ == '__main__':
    main()
