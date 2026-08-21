"""Держит ли полный контур силуэта сверху то, чего не держат три числа.

Что известно. Двумя камерами не наблюдаются три направления, и все три - это
скольжение кольца по куполу: поворот вокруг вертикали и два сдвига, смешивающих
вертикаль с горизонталью. Купол гладкий, кольцо на нём почти овальное, поэтому
проекция к таким движениям почти безразлична.

Три опорных числа с силуэта (верх и края) этого не ловят - проверено, слабая
тройка не сдвинулась. Но сверху шлем виден как овал С ВЫСТУПАМИ УШЕЙ, а выступы
- как раз угловая примета, которая обязана держать поворот вокруг вертикали.
Значит нужен не габарит, а форма контура.

Как считается. Кромка модели проецируется в `top` и сравнивается с контуром
маски. Юбка на снимке не срезана и торчит наружу, поэтому вводится один
параметр - радиальный запас, общий на весь контур. Он физически осмыслен, и его
подобранное значение служит проверкой: должно выйти несколько миллиметров, а не
десятки.
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
import exp_cad_fit as F, exp_camera_fit as E             # noqa: E402
import exp_all_methods as A, exp_observability as O      # noqa: E402
import exp_three_cams as T                               # noqa: E402
from bench import dist_to_polyline                       # noqa: E402
from step03_segment_monochrome import segment_image      # noqa: E402
from shots import img_path                               # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

_C = {}


def top_contour(variant, n=160):
    """Контур маски сверху, равномерно проряженный."""
    if variant not in _C:
        m, _, _, _, _ = segment_image(img_path(variant, 'top'), True)
        c = max(cv2.findContours((m > 0).astype(np.uint8), cv2.RETR_EXTERNAL,
                                 cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)
        p = c[:, 0, :].astype(float)
        k = np.linspace(0, len(p) - 1, n).astype(int)
        _C[variant] = p[k]
    return _C[variant]


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
        if mode in ('box3', 'contour'):
            V = verts @ R.T + t0 + p[3:6]
            for w in (('back', 'left', 'top') if mode == 'box3' else ('back', 'left')):
                pc, f = cams[w]
                uv, z = E.project(V, pc[:3], pc[3:6], f)
                got = np.array([uv[:, 1].min(), uv[:, 0].min(), uv[:, 0].max()])
                want = np.array(T.mask_box3(variant, w))
                out.append((got - want) * float(np.median(z)) / f / np.sqrt(3))
        if mode == 'contour':
            skirt = p[6]
            edge = (rim + skirt * rad) @ R.T + t0 + p[3:6]
            pc, f = cams['top']
            uv, z = E.project(edge, pc[:3], pc[3:6], f)
            q = top_contour(variant)
            d = np.abs(dist_to_polyline(q, uv))
            out.append(d * float(np.median(z)) / f / np.sqrt(len(d)))
        return np.concatenate(out)
    return resid


def main():
    marks = line_features.load_marks()
    rim = XS.mesh_rim(F.STL)
    verts = np.unique(F.load_stl(F.STL).reshape(-1, 3), axis=0)
    cams = T.marker_cams()
    R0, t0 = A.cad_start()
    cases = [('силуэт(2), как было', 'box2', 6), ('силуэт(3), три числа', 'box3', 6),
             ('КОНТУР сверху', 'contour', 7)]
    print(f"{'вариант':<7}{'набор':<22}{'слабая тройка':<26}{'запас юбки':>11}"
          f"{'против программы':>24}")
    acc = {c[0]: [] for c in cases}
    for v in O.CLEAN:
        fit_model.standoff(v)
        own = E.ring(v, 0.0)
        for name, mode, npar in cases:
            r = least_squares(resid_of(v, rim, verts, marks, cams, R0, t0, mode),
                              np.r_[np.zeros(6), 12.0][:npar], method='lm', max_nfev=900)
            S = np.linalg.svd(r.jac, compute_uv=False)
            sv = S / S.max()
            P = rim @ (cv2.Rodrigues(r.x[:3])[0] @ R0).T + t0 + r.x[3:6]
            d = lsgeom.curve_distance(P, own)
            acc[name].append((d.mean(), d.max(), 100 * np.mean(d <= 2)))
            sk = f'{r.x[6]:>10.1f}' if npar == 7 else f'{"":>10}'
            print(f'{v:<7}{name:<22}{np.array2string(np.round(sv[-3:], 4), separator=" "):<26}'
                  f'{sk} {d.mean():>10.2f}/{d.max():<6.2f}{100 * np.mean(d <= 2):>4.0f}%',
                  flush=True)
    print()
    for name, _, _ in cases:
        a = np.array(acc[name])
        m = [i for i, v in enumerate(O.CLEAN) if v in A.MASTER]
        o = [i for i, v in enumerate(O.CLEAN) if v not in A.MASTER]
        print(f'{name:<24} мастер {a[m, 0].mean():5.2f}/{a[m, 1].mean():5.2f}/'
              f'{a[m, 2].mean():3.0f}%   чужие {a[o, 0].mean():5.2f}/{a[o, 1].mean():5.2f}/'
              f'{a[o, 2].mean():3.0f}%')


if __name__ == '__main__':
    main()
