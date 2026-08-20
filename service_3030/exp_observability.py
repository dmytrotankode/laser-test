"""Наблюдаемость позы: сколько степеней свободы реально видно с двух камер.

Открытие, ради которого написано: подгонка модели по линии сгиба садится на
разметку с остатком 0.2-0.4 мм, а траектория при этом мимо записанной на 2-3 мм.
Разложение чувствительности объясняет почему - из шести направлений позы три
наблюдаются в 100-1000 раз слабее остальных. Вдоль мягкого направления модель
можно сдвинуть на 3.2 мм, ухудшив картинку всего на 0.1 мм.

Гипотеза: силуэт даёт ограничения другой природы и закрывает мягкие направления.
Проверяется здесь.

Силуэт берётся НЕ растровый. Растеризация в уменьшенном масштабе квантует
ответ шагами в треть миллиметра, и производные, по которым считается
чувствительность, окажутся шумом. Вместо этого - три опорных числа на ракурс:
верх купола и левый/правый края силуэта. Они гладкие (минимум и максимум
проекции), считаются мгновенно и несут ровно ту информацию, которой не хватает:
высоту и дальность.

Меряется три вещи:
    * сингулярные числа - выровнялись ли направления;
    * утечка: на сколько уезжает траектория при ухудшении картинки на 0.1 мм;
    * расхождение с записанной программой - стало ли лучше по делу.
"""
import os
import sys
import json
import numpy as np
import cv2
from scipy.optimize import least_squares

BASE = os.path.dirname(os.path.abspath(__file__))
S5056 = os.path.abspath(os.path.join(BASE, '..', 'service_5056'))
S2020 = os.path.abspath(os.path.join(BASE, '..', 'service_2020'))
sys.path.insert(0, BASE)
sys.path.insert(0, S2020)
sys.path.insert(0, os.path.join(S5056, 'scripts'))

import lsgeom                                            # noqa: E402
import fit_model                                         # noqa: E402
import line_features                                     # noqa: E402
import export_scene as XS                                # noqa: E402
import export_ls as X                                    # noqa: E402
import exp_cad_fit as F                                  # noqa: E402
import exp_camera_fit as E                               # noqa: E402
import exp_all_methods as A                              # noqa: E402
from bench import dist_to_polyline                       # noqa: E402
from step03_segment_monochrome import segment_image      # noqa: E402
from shots import img_path                               # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

VIEWS = ('back', 'left')
CLEAN = ['v6', 'v13', 'v20', 'v21', 'v24', 'v25']
REF = 'v1'                  # опорный снимок для разностного силуэта
_MASK = {}


def mask_box(variant, view):
    """Верх и боковые края силуэта, в пикселях полного кадра.

    Низ не берётся: там необрезанная юбка и штатная отсечка маски, у модели
    этого нет.
    """
    key = (variant, view)
    if key not in _MASK:
        m, _, _, _, _ = segment_image(img_path(variant, view), False)
        ys, xs = np.where(m > 0)
        _MASK[key] = (float(ys.min()), float(xs.min()), float(xs.max()))
    return _MASK[key]


def model_box(p, verts, cams, view, R0, t0):
    """Верх и края проекции модели - те же три числа, что берём с маски."""
    R = cv2.Rodrigues(p[:3])[0] @ R0
    V = verts @ R.T + t0 + p[3:6]
    pc, f = cams[view]
    uv, _ = E.project(V, pc[:3], pc[3:6], f)
    return np.array([uv[:, 1].min(), uv[:, 0].min(), uv[:, 0].max()])


def ref_pose(rim, R0, t0):
    """Поза модели на опорном варианте, найденная по его ЗАПИСАННОЙ линии реза.

    Нужна только как точка отсчёта для разностного силуэта. Фотографии тут не
    участвуют, поэтому ошибка камер сюда не попадает.
    """
    fit_model.standoff(REF)
    cut = E.ring(REF, 0.0)

    def resid(p):
        P = rim @ (cv2.Rodrigues(p[:3])[0] @ R0).T + t0 + p[3:6]
        return np.r_[lsgeom.curve_distance(P, cut), lsgeom.curve_distance(cut, P)]

    return least_squares(resid, np.zeros(6), method='lm', max_nfev=600).x


def fit(variant, rim, verts, marks, cams, R0, t0, use_box, w_box=1.0,
        mode='absolute', base=None):
    nrm = A.radial(rim)
    off = A.FOLD_RADIAL * nrm
    off[:, 2] += A.FOLD_UP

    def resid(p):
        R = cv2.Rodrigues(p[:3])[0] @ R0
        fold = (rim + off) @ R.T + t0 + p[3:6]
        out = []
        for w in VIEWS:
            pc, f = cams[w]
            uv, z = E.project(fold, pc[:3], pc[3:6], f)
            d = np.abs(dist_to_polyline(X.resample(marks[variant][w]), E.near_arc(uv, z)))
            mm = float(np.median(z)) / f
            out.append(d * mm / np.sqrt(len(d)))
            if use_box:
                got = model_box(p, verts, cams, w, R0, t0)
                want = np.array(mask_box(variant, w))
                if mode == 'differential':
                    # Сравниваем не абсолютные силуэты, а ИЗМЕНЕНИЕ относительно
                    # опорного снимка. Постоянная разница «модель против детали»
                    # при этом сокращается, и силуэт перестаёт тянуть позу к форме
                    # модели. В абсолютном виде он это делал: на v13 доля в допуске
                    # падала с 65 до 52 %, на v6 с 42 до 17 %.
                    got = got - base['model'][w]
                    want = want - base['mask'][w]
                out.append(w_box * (got - want) * mm / np.sqrt(3))
        return np.concatenate(out)

    r = least_squares(resid, np.zeros(6), method='lm', max_nfev=800)
    R = cv2.Rodrigues(r.x[:3])[0] @ R0
    return r, rim @ R.T + t0 + r.x[3:6]


def leak(resid, p0, Vt, k, rim, R0, t0):
    """На сколько уезжает траектория, если картинку ухудшить на 0.1 мм."""
    base = np.sqrt(np.mean(resid(p0) ** 2))
    d = Vt[k]
    lo, hi = 0.0, 50.0
    for _ in range(40):
        m = (lo + hi) / 2
        if np.sqrt(np.mean(resid(p0 + m * d) ** 2)) - base < 0.1:
            lo = m
        else:
            hi = m
    def place(p):
        return rim @ (cv2.Rodrigues(p[:3])[0] @ R0).T + t0 + p[3:6]
    return float(np.linalg.norm(place(p0 + lo * d) - place(p0), axis=1).mean())


def main():
    marks = line_features.load_marks()
    rim = XS.mesh_rim(F.STL)
    verts = np.unique(F.load_stl(F.STL).reshape(-1, 3), axis=0)
    cams = X.cameras()
    R0, t0 = A.cad_start()
    global BASE_LM
    pr = ref_pose(rim, R0, t0)
    BASE_LM = dict(model={w: model_box(pr, verts, cams, w, R0, t0) for w in VIEWS},
                   mask={w: np.array(mask_box(REF, w)) for w in VIEWS})
    print(f'модель: кромка {len(rim)} точек, вершин {len(verts)}')
    print(f'опора для разностного силуэта: {REF}, её поза найдена по записанной '
          f'программе, без участия фотографий\n')

    print(f"{'вариант':<7}{'источник':<16}{'сингулярные числа':<42}"
          f"{'утечка, мм':>12}{'против программы: сред/макс/допуск':>36}")
    for v in CLEAN:
        fit_model.standoff(v)
        own = E.ring(v, 0.0)
        for use_box, mode, tag in ((False, 'absolute', 'только линия'),
                                   (True, 'absolute', 'силуэт как есть'),
                                   (True, 'differential', 'силуэт разностный')):
            r, P = fit(v, rim, verts, marks, cams, R0, t0, use_box,
                       mode=mode, base=BASE_LM)
            U, Sv, Vt = np.linalg.svd(r.jac, full_matrices=False)
            Sv = Sv / Sv.max()
            off = A.FOLD_RADIAL * A.radial(rim)
            off[:, 2] += A.FOLD_UP
            fn = (lambda p, _v=v, _b=use_box, _m=mode:
                  _resid_for(p, _v, _b, rim, off, verts, marks, cams, R0, t0,
                             mode=_m, base=BASE_LM))
            lk = leak(fn, r.x, Vt, 5, rim, R0, t0)
            d = lsgeom.curve_distance(P, own)
            print(f'{v:<7}{tag:<16}{np.array2string(np.round(Sv, 3), separator=" "):<42}'
                  f'{lk:>12.2f}{d.mean():>14.2f}/{d.max():<7.2f}{100 * np.mean(d <= 2):>6.0f}%',
                  flush=True)


def _resid_for(p, variant, use_box, rim, off, verts, marks, cams, R0, t0, w_box=1.0,
               mode='absolute', base=None):
    R = cv2.Rodrigues(p[:3])[0] @ R0
    fold = (rim + off) @ R.T + t0 + p[3:6]
    out = []
    for w in VIEWS:
        pc, f = cams[w]
        uv, z = E.project(fold, pc[:3], pc[3:6], f)
        d = np.abs(dist_to_polyline(X.resample(marks[variant][w]), E.near_arc(uv, z)))
        mm = float(np.median(z)) / f
        out.append(d * mm / np.sqrt(len(d)))
        if use_box:
            got = model_box(p, verts, cams, w, R0, t0)
            want = np.array(mask_box(variant, w))
            if mode == 'differential':
                got = got - base['model'][w]
                want = want - base['mask'][w]
            out.append(w_box * (got - want) * mm / np.sqrt(3))
    return np.concatenate(out)


if __name__ == '__main__':
    main()
