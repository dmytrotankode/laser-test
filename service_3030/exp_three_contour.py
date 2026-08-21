"""Контур силуэта не только сверху, а на всех трёх камерах разом.

Продолжение exp_top_contour.py (MARKER_RESULTS_2026-08-21.md, §7 п.1): там кромка
модели + один параметр «запас на юбку» проецировались в `top` и сравнивались с
контуром маски - слабая тройка осей подтянулась в 6 раз, доля в допуске на
чужих шлемах выросла с 15-17% до 56%.

Идея расширения: та же кромка (+ тот же общий запас на юбку) проецируется теперь
ещё и в `back`/`left`, сверх уже имеющейся разметки линии сгиба. Не замена
разметке - разметка точнее (линия против кривой), а добавка: разметка держит
позицию сгиба, контур - габарит купола выше сгиба, которого разметка не видит
вообще (она размечена только вдоль сгиба, не выше).

Осторожно: это НЕ то же самое геометрически, что top. Сверху кромка+юбка
проецируется близко к тому, что реально видно по контуру (смотрим почти вдоль
оси симметрии). Сбоку силуэт формирует в основном КУПОЛ выше сгиба, а не кромка -
здесь эта аппроксимация грубее. Числа покажут, работает ли она вообще, не
предполагаю заранее.

    python exp_three_contour.py
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

import lsgeom, fit_model, line_features                  # noqa: E402
import export_scene as XS, export_ls as X                # noqa: E402
import exp_cad_fit as F, exp_camera_fit as E              # noqa: E402
import exp_all_methods as A, exp_observability as O       # noqa: E402
import exp_three_cams as T                                # noqa: E402
import exp_top_contour as TC                              # noqa: E402
from bench import dist_to_polyline                        # noqa: E402
from step03_segment_monochrome import segment_image       # noqa: E402
from shots import img_path                                # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

_SC = {}


def side_contour(variant, view, n=160):
    """Контур маски back/left, той же равномерной прорезкой, что и top_contour."""
    key = (variant, view)
    if key not in _SC:
        m, _, _, _, _ = segment_image(img_path(variant, view), False)
        c = max(cv2.findContours((m > 0).astype(np.uint8), cv2.RETR_EXTERNAL,
                                 cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)
        p = c[:, 0, :].astype(float)
        k = np.linspace(0, len(p) - 1, n).astype(int)
        _SC[key] = p[k]
    return _SC[key]


def resid_of(variant, rim, verts, marks, cams, R0, t0, mode):
    off = A.FOLD_RADIAL * A.radial(rim)
    off[:, 2] += A.FOLD_UP
    rad = A.radial(rim)

    def resid(p):
        R = cv2.Rodrigues(p[:3])[0] @ R0
        fold = (rim + off) @ R.T + t0 + p[3:6]
        out = []
        for w in ('back', 'left'):
            pc, f = cams[w]
            uv, z = E.project(fold, pc[:3], pc[3:6], f)
            d = np.abs(dist_to_polyline(X.resample(marks[variant][w]), E.near_arc(uv, z)))
            out.append(d * float(np.median(z)) / f / np.sqrt(len(d)))

        skirt = p[6]
        edge = (rim + skirt * rad) @ R.T + t0 + p[3:6]

        views = ('top',) if mode == 'top_only' else ('back', 'left', 'top')
        for w in views:
            pc, f = cams[w]
            uv, z = E.project(edge, pc[:3], pc[3:6], f)
            q = TC.top_contour(variant) if w == 'top' else side_contour(variant, w)
            uv_use = uv if w == 'top' else E.near_arc(uv, z)
            d = np.abs(dist_to_polyline(q, uv_use))
            out.append(d * float(np.median(z)) / f / np.sqrt(len(d)))
        return np.concatenate(out)
    return resid


def main():
    marks = line_features.load_marks()
    rim = XS.mesh_rim(F.STL)
    verts = np.unique(F.load_stl(F.STL).reshape(-1, 3), axis=0)
    cams = T.marker_cams()
    R0, t0 = A.cad_start()
    cases = [('контур top (было)', 'top_only'), ('контур все три (ново)', 'contour3')]
    print(f"{'вариант':<7}{'набор':<24}{'слабая тройка':<26}{'запас юбки':>11}"
          f"{'против программы':>24}")
    acc = {c[0]: [] for c in cases}
    for v in O.CLEAN:
        fit_model.standoff(v)
        own = E.ring(v, 0.0)
        for name, mode in cases:
            r = least_squares(resid_of(v, rim, verts, marks, cams, R0, t0, mode),
                              np.r_[np.zeros(6), 12.0], method='lm', max_nfev=900)
            S = np.linalg.svd(r.jac, compute_uv=False)
            sv = S / S.max()
            P = rim @ (cv2.Rodrigues(r.x[:3])[0] @ R0).T + t0 + r.x[3:6]
            d = lsgeom.curve_distance(P, own)
            acc[name].append((d.mean(), d.max(), 100 * np.mean(d <= 2)))
            print(f'{v:<7}{name:<24}{np.array2string(np.round(sv[-3:], 4), separator=" "):<26}'
                  f'{r.x[6]:>10.1f} {d.mean():>10.2f}/{d.max():<6.2f}{100 * np.mean(d <= 2):>4.0f}%',
                  flush=True)
    print()
    for name, _ in cases:
        a = np.array(acc[name])
        m = [i for i, v in enumerate(O.CLEAN) if v in A.MASTER]
        o = [i for i, v in enumerate(O.CLEAN) if v not in A.MASTER]
        print(f'{name:<26} мастер {a[m, 0].mean():5.2f}/{a[m, 1].mean():5.2f}/'
              f'{a[m, 2].mean():3.0f}%   чужие {a[o, 0].mean():5.2f}/{a[o, 1].mean():5.2f}/'
              f'{a[o, 2].mean():3.0f}%')


if __name__ == '__main__':
    main()
