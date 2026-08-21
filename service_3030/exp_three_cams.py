"""Лечит ли третья камера недоопределённость позы.

Измерено раньше (exp_observability): двумя камерами из шести степеней свободы
наблюдаются три, остальные слабее в 100-1000 раз. Модель можно сдвинуть на
3.2 мм, ухудшив картинку на 0.1 мм. Это, а не точность камер, держит результат.

Теперь `top` откалибрована по маркерным точкам 18.08 (exp_marker_calib), и её
можно подключить. Линия сгиба сверху не видна, поэтому третий ракурс входит
только опорными числами силуэта - верх купола и края.

Сравниваются три набора ограничений на одних данных:
    линия(2)              - только разметка сгиба на back и left
    линия(2) + силуэт(2)  - плюс силуэт тех же двух
    линия(2) + силуэт(3)  - плюс силуэт ТРЁХ, включая top

Смотреть надо на сингулярные числа и утечку, а не только на итог: если третья
камера действительно добавляет наблюдаемость, слабые направления обязаны
подтянуться.
"""
import os
import sys
import json
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
from step03_segment_monochrome import segment_image      # noqa: E402
from shots import img_path                               # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

LINE_VIEWS = ('back', 'left')
_MASK3 = {}


def marker_cams():
    out = {}
    for v in ('back', 'left', 'top'):
        z = np.load(os.path.join(BASE, 'data', f'cam_{v}_marker.npy'))
        out[v] = (z[:6], z[6])
    return out


def mask_box3(variant, view):
    """Опорные числа силуэта. Для `top` отсечки нет, у боковых штатная."""
    key = (variant, view)
    if key not in _MASK3:
        m, _, _, _, _ = segment_image(img_path(variant, view), view == 'top')
        ys, xs = np.where(m > 0)
        _MASK3[key] = (float(ys.min()), float(xs.min()), float(xs.max()))
    return _MASK3[key]


def make_resid(variant, rim, verts, marks, cams, R0, t0, box_views):
    off = A.FOLD_RADIAL * A.radial(rim)
    off[:, 2] += A.FOLD_UP

    def resid(p):
        R = cv2.Rodrigues(p[:3])[0] @ R0
        fold = (rim + off) @ R.T + t0 + p[3:6]
        V = verts @ R.T + t0 + p[3:6]
        out = []
        for w in LINE_VIEWS:
            pc, f = cams[w]
            uv, z = E.project(fold, pc[:3], pc[3:6], f)
            d = np.abs(dist_to_polyline(X.resample(marks[variant][w]), E.near_arc(uv, z)))
            out.append(d * float(np.median(z)) / f / np.sqrt(len(d)))
        for w in box_views:
            pc, f = cams[w]
            uv, z = E.project(V, pc[:3], pc[3:6], f)
            got = np.array([uv[:, 1].min(), uv[:, 0].min(), uv[:, 0].max()])
            want = np.array(mask_box3(variant, w))
            out.append((got - want) * float(np.median(z)) / f / np.sqrt(3))
        return np.concatenate(out)
    return resid


def leak(resid, p0, Vt, rim, R0, t0):
    base = np.sqrt(np.mean(resid(p0) ** 2))
    d = Vt[-1]
    lo, hi = 0.0, 50.0
    for _ in range(40):
        m = (lo + hi) / 2
        if np.sqrt(np.mean(resid(p0 + m * d) ** 2)) - base < 0.1:
            lo = m
        else:
            hi = m
    place = lambda p: rim @ (cv2.Rodrigues(p[:3])[0] @ R0).T + t0 + p[3:6]
    return float(np.linalg.norm(place(p0 + lo * d) - place(p0), axis=1).mean())


def main():
    marks = line_features.load_marks()
    rim = XS.mesh_rim(F.STL)
    verts = np.unique(F.load_stl(F.STL).reshape(-1, 3), axis=0)
    cams = marker_cams()
    R0, t0 = A.cad_start()

    cases = [('линия(2)', ()), ('линия(2)+силуэт(2)', ('back', 'left')),
             ('линия(2)+силуэт(3)', ('back', 'left', 'top'))]
    print(f"{'вариант':<7}{'набор':<21}{'сингулярные числа':<44}"
          f"{'утечка':>9}{'против программы':>26}")
    acc = {c[0]: [] for c in cases}
    for v in O.CLEAN:
        fit_model.standoff(v)
        own = E.ring(v, 0.0)
        for name, bv in cases:
            resid = make_resid(v, rim, verts, marks, cams, R0, t0, bv)
            r = least_squares(resid, np.zeros(6), method='lm', max_nfev=800)
            S = np.linalg.svd(r.jac, full_matrices=False)
            sv = S[1] / S[1].max()
            lk = leak(resid, r.x, S[2], rim, R0, t0)
            P = rim @ (cv2.Rodrigues(r.x[:3])[0] @ R0).T + t0 + r.x[3:6]
            d = lsgeom.curve_distance(P, own)
            acc[name].append((d.mean(), d.max(), 100 * np.mean(d <= 2)))
            print(f'{v:<7}{name:<21}{np.array2string(np.round(sv, 4), separator=" "):<44}'
                  f'{lk:>9.2f}{d.mean():>14.2f}/{d.max():<6.2f}{100 * np.mean(d <= 2):>4.0f}%',
                  flush=True)
    print()
    for name, _ in cases:
        a = np.array(acc[name])
        m = [i for i, v in enumerate(O.CLEAN) if v in A.MASTER]
        o = [i for i, v in enumerate(O.CLEAN) if v not in A.MASTER]
        print(f'{name:<22} мастер {a[m, 0].mean():5.2f}/{a[m, 1].mean():5.2f}/'
              f'{a[m, 2].mean():3.0f}%   чужие {a[o, 0].mean():5.2f}/{a[o, 1].mean():5.2f}/'
              f'{a[o, 2].mean():3.0f}%')


if __name__ == '__main__':
    main()
