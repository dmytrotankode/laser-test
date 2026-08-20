"""Попытка откалибровать верхнюю камеру по имеющимся снимкам.

Зачем: из шести степеней свободы позы две камеры видят три, остальные слабее в
сотни раз (exp_observability). Третий ракурс бьёт прямо в это. Лазерных точек на
`top` всего две при шести неизвестных, поэтому §4e её посчитать не смог - но
есть другой путь.

ИДЕЯ. Положение шлема в координатах станка известно БЕЗ камер: подгоняем кромку
CAD к записанной линии реза, это чистая трёхмерная задача. Значит для каждого
варианта известна и вся его поверхность. Верхняя камера обязана проецировать эту
поверхность так, чтобы силуэт совпал с маской на снимке `top`.

ЧЕСТНЫЕ ДОПУЩЕНИЯ, каждое может испортить результат:

* CAD - это ОБРЕЗАННЫЙ шлем, а на снимке юбка ещё не срезана и торчит наружу.
  Поэтому вводится один параметр - на сколько силуэт детали шире силуэта модели.
  Он физически осмыслен, но добавляет неизвестное;
* силуэт модели считается выпуклой оболочкой проекции. Сверху шлем почти
  выпуклый, но «почти» - это приближение;
* фокус закреплён на 22700 px, как у двух других камер. Свободный фокус на
  почти плоской мишени вырождается вместе с дальностью - проверено на back.

ПРОВЕРКА (без неё результату верить нельзя):
    * две лазерные точки на `top` - независимы, про силуэт ничего не знают;
    * камера, подогнанная без какого-то варианта, проверяется на нём;
    * разброс решения при подгонке по разным вариантам поодиночке.
"""
import os
import sys
import numpy as np
import cv2
from scipy.optimize import least_squares, minimize

BASE = os.path.dirname(os.path.abspath(__file__))
S5056 = os.path.abspath(os.path.join(BASE, '..', 'service_5056'))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(S5056, 'scripts'))

import lsgeom                                            # noqa: E402
import fit_model                                         # noqa: E402
import export_scene as XS                                # noqa: E402
import exp_cad_fit as F                                  # noqa: E402
import exp_camera_fit as E                               # noqa: E402
import exp_all_methods as A                              # noqa: E402
from step03_segment_monochrome import segment_image      # noqa: E402
from shots import img_path                               # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

FOCUS = 22700.0
SCALE = 4
W, H = 4096 // SCALE, 3000 // SCALE
VARIANTS = ['v1', 'v8', 'v13', 'v21']


def mask_top(variant):
    m, _, _, _, _ = segment_image(img_path(variant, 'top'), True)
    return cv2.resize(m, (W, H), interpolation=cv2.INTER_NEAREST) > 0


def helmet_in_machine(variant, rim, verts, R0, t0):
    """Поверхность шлема в координатах станка - через его ЗАПИСАННУЮ программу.

    Камеры здесь не участвуют вообще, поэтому их ошибка в опору не попадает.
    """
    fit_model.standoff(variant)
    cut = E.ring(variant, 0.0)

    def resid(p):
        P = rim @ (cv2.Rodrigues(p[:3])[0] @ R0).T + t0 + p[3:6]
        return np.r_[lsgeom.curve_distance(P, cut), lsgeom.curve_distance(cut, P)]

    q = least_squares(resid, np.zeros(6), method='lm', max_nfev=600).x
    R = cv2.Rodrigues(q[:3])[0] @ R0
    return verts @ R.T + t0 + q[3:6]


def silhouette(V, p, margin_px):
    """Выпуклая оболочка проекции, раздутая на `margin_px` - это юбка."""
    R = cv2.Rodrigues(p[:3])[0]
    C = p[3:6]
    Xc = (V - C) @ R.T
    z = Xc[:, 2]
    if (z <= 1).any():
        return None
    uv = np.c_[FOCUS * Xc[:, 0] / z + 4096 / 2, FOCUS * Xc[:, 1] / z + 3000 / 2] / SCALE
    hull = cv2.convexHull(uv.astype(np.float32))
    img = np.zeros((H, W), np.uint8)
    cv2.fillConvexPoly(img, hull.astype(np.int32), 1)
    if margin_px > 0.5:
        k = int(margin_px) | 1
        img = cv2.dilate(img, np.ones((k, k), np.uint8))
    return img > 0


def badness(p, data):
    tot = 0.0
    for V, m in data:
        s = silhouette(V, p[:6], p[6])
        if s is None:
            return 1.0
        inter = np.count_nonzero(s & m)
        union = np.count_nonzero(s | m)
        tot += 1.0 - inter / max(union, 1)
    return tot / len(data)


def starts(center):
    out = []
    for az in np.radians(np.arange(0, 360, 30)):
        for dist in (2000.0, 2150.0, 2300.0):
            eye = center + np.array([0, 0, -dist])       # верх это -Z
            fwd = center - eye
            fwd /= np.linalg.norm(fwd)
            up = np.array([np.cos(az), np.sin(az), 0.0])
            right = np.cross(up, fwd)
            right /= np.linalg.norm(right)
            up = np.cross(fwd, right)
            R = np.vstack([right, up, fwd])
            out.append(np.r_[cv2.Rodrigues(R)[0].ravel(), eye, 20.0])
    return out


def main():
    rim = XS.mesh_rim(F.STL)
    verts = np.unique(F.load_stl(F.STL).reshape(-1, 3), axis=0)
    R0, t0 = A.cad_start()
    data = []
    for v in VARIANTS:
        V = helmet_in_machine(v, rim, verts, R0, t0)
        data.append((V, mask_top(v)))
        print(f'  {v}: поверхность в координатах станка получена', flush=True)
    center = data[0][0].mean(0)

    best = None
    for p0 in starts(center):
        b = badness(p0, data)
        if best is None or b < best[0]:
            best = (b, p0)
    print(f'\nлучший старт: несовпадение {best[0]:.3f}')

    r = minimize(badness, best[1], args=(data,), method='Powell',
                 options=dict(maxiter=8000, xtol=1e-3, ftol=1e-5))
    p = r.x
    print(f'после подгонки: несовпадение {r.fun:.3f} (IoU {1 - r.fun:.3f})')
    print(f'камера top: {np.round(p[3:6], 0)}, до шлема '
          f'{np.linalg.norm(p[3:6] - center) / 1000:.2f} м, запас на юбку {p[6]:.0f} px')
    for v, (V, m) in zip(VARIANTS, data):
        s = silhouette(V, p[:6], p[6])
        iou = np.count_nonzero(s & m) / max(np.count_nonzero(s | m), 1)
        print(f'   {v}: IoU {iou:.3f}')

    print('\nПроверка исключением: подгоняем без варианта, смотрим на нём')
    for i, v in enumerate(VARIANTS):
        rest = [d for j, d in enumerate(data) if j != i]
        q = minimize(badness, p, args=(rest,), method='Powell',
                     options=dict(maxiter=4000, xtol=1e-3, ftol=1e-5)).x
        V, m = data[i]
        s = silhouette(V, q[:6], q[6])
        iou = np.count_nonzero(s & m) / max(np.count_nonzero(s | m), 1)
        print(f'   {v}: IoU {iou:.3f}, камера сместилась на '
              f'{np.linalg.norm(q[3:6] - p[3:6]):.0f} мм')

    np.save(os.path.join(BASE, 'data', 'cam_top_try.npy'), np.r_[p, FOCUS])
    print('\nсохранено в data/cam_top_try.npy (имя с _try: в сцену пока не идёт)')


if __name__ == '__main__':
    main()
