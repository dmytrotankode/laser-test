"""Совместная подгонка: кольцо реза + лазерные пятна + маркерные точки (20.08).

exp_camera_joint.py держит позу двумя источниками - разметкой линии (сотни точек,
но привязана к неизвестному отступу сгиба) и лазерными пятнами (весит мало,
7 штук, зато без всякого отступа). Сегодняшний прогон `exp_pose_from_line_marker.py`
показал: камера, откалиброванная ТОЛЬКО по маркерным точкам (весь купол), на
задаче с кромкой реза заметно хуже (9 мм против 3.4) - это чужая для неё
территория, marker-точки её не покрывают.

Здесь маркерные точки - ТРЕТИЙ источник в той же связке, а не замена. Держит то
же самое, что уже умеет: слабые оси позы (весь купол, а не плоское кольцо), но
не перетягивает точность на кромке - вес источника делится на корень из объёма,
как и остальные (эту дисциплину ввёл ещё exp_camera_joint.py).

Только собственные точки каждой камеры (own_and_cross из exp_marker_calib) -
угловые/чужие точки слишком шумные (шум наводки сопла, см. историю чата 20.08),
в подгонку их совать нельзя, только для отдельной проверки.

service_5056 только читается.

    python exp_camera_joint_marker.py
"""
import os
import sys
import csv
import json
import numpy as np
from scipy.optimize import least_squares

BASE = os.path.dirname(os.path.abspath(__file__))
S5056 = os.path.abspath(os.path.join(BASE, '..', 'service_5056'))
NEW0810 = os.path.join(S5056, 'scratch', 'new0810')
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(S5056, 'scripts'))
sys.path.insert(0, NEW0810)

import line_features                                    # noqa: E402
import dataset                                          # noqa: E402
import fit_model                                        # noqa: E402
from exp_camera_fit import ring, project, near_arc, LASER_CAMS  # noqa: E402
from exp_camera_joint import line_error_mm, spot_error_mm  # noqa: E402
from exp_marker_calib import load_correspondences, own_and_cross  # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def marker_error_mm(p, pts, f):
    """Расхождение проекции с кликом на маркерную точку, мм на детали."""
    if not pts:
        return np.zeros(1)
    X = np.array([pt['XYZ'] for pt in pts])
    uv_obs = np.array([pt['uv'] for pt in pts])
    uv_pred, z = project(X, p[:3], p[3:6], f)
    err_px = np.linalg.norm(uv_pred - uv_obs, axis=1)
    return err_px * z / f


def fit(view, variants, marks, f, x0, own_pts, w_line=1.0, w_spot=1.0, w_marker=1.0, spots=None):
    def resid(p):
        a = line_error_mm(p, view, variants, marks, f)
        b = spot_error_mm(p, view, f, spots)
        c = marker_error_mm(p[:6], own_pts, f)
        return np.concatenate([w_line * a / np.sqrt(len(a)),
                               w_spot * b / np.sqrt(len(b)),
                               w_marker * c / np.sqrt(len(c))])
    return least_squares(resid, x0, method='lm', max_nfev=400).x


def report(view):
    marks = line_features.load_marks()
    train = [v for v in dataset.TRAIN if v != 'v2']
    held = list(dataset.HELDOUT)
    for v in train + held:
        fit_model.standoff(v)

    cam = json.load(open(LASER_CAMS, encoding='utf-8'))[view]
    f = cam['focus']
    x0 = np.r_[cam['x'][:6], 10.0]

    by_view = load_correspondences()
    own_pts, cross_pts = own_and_cross(by_view[view], view)

    sys.path.insert(0, NEW0810)
    import L4_rays                                       # noqa: E402
    n_spots = len(L4_rays.observations(view))

    print(f'=== {view}: кольцо реза ({len(train)} вар.) + {n_spots} лазерных пятен '
          f'+ {len(own_pts)} маркерных точек\n')

    p = fit(view, train, marks, f, x0, own_pts)
    print(f'Совместное решение: отступ «сгиб выше реза» {p[6]:+.1f} мм')
    print(f'   остаток на разметке   медиана {np.median(line_error_mm(p, view, train, marks, f)):.2f} мм')
    print(f'   остаток на пятнах     медиана {np.median(spot_error_mm(p, view, f)):.2f} мм, '
          f'макс {np.max(spot_error_mm(p, view, f)):.2f}')
    m_err = marker_error_mm(p[:6], own_pts, f)
    print(f'   остаток на маркерах   медиана {np.median(m_err):.2f} мм, макс {np.max(m_err):.2f}')

    if cross_pts:
        c_err = marker_error_mm(p[:6], cross_pts, f)
        print(f'   независимо: чужие/угловые маркеры  медиана {np.median(c_err):.2f} мм, '
              f'макс {np.max(c_err):.2f}  (не участвовали в подгонке)')

    print('\n1. Предсказание пятна, исключённого из подгонки (протокол §4e):')
    errs = []
    for i in range(n_spots):
        keep = set(range(n_spots)) - {i}
        q = fit(view, train, marks, f, x0, own_pts, spots=keep)
        e = float(spot_error_mm(q, view, f, {i})[0])
        errs.append(e)
    print(f'   медиана {np.median(errs):.2f} мм   (только линия+пятна, старый результат см. exp_camera_joint.py)')

    print('\n2. Предсказание разметки варианта, не участвовавшего в подгонке:')
    errs2 = []
    for v in train:
        rest = [u for u in train if u != v]
        q = fit(view, rest, marks, f, x0, own_pts)
        e = float(np.median(line_error_mm(q, view, [v], marks, f)))
        errs2.append(e)
    print(f'   по {len(train)} вариантам: медиана {np.median(errs2):.2f} мм, худший {np.max(errs2):.2f} мм')
    e_held = [float(np.median(line_error_mm(p, view, [v], marks, f))) for v in held]
    print(f'   held-out {", ".join(held)}: ' + ', '.join(f'{e:.2f} мм' for e in e_held))

    print('\n3. Чувствительность к весу маркерных точек (не должно рвать разметку/пятна):')
    for wm in (0.0, 0.3, 1.0, 3.0, 10.0):
        q = fit(view, train, marks, f, x0, own_pts, w_marker=wm)
        print(f'   вес маркеров {wm:>4.1f}   разметка {np.median(line_error_mm(q, view, train, marks, f)):.2f} мм   '
              f'пятна {np.median(spot_error_mm(q, view, f)):.2f} мм   '
              f'маркеры {np.median(marker_error_mm(q[:6], own_pts, f)):.2f} мм   '
              f'камера сдвинулась на {np.linalg.norm(q[3:6] - p[3:6]):.0f} мм от совместного решения')

    out_path = os.path.join(BASE, 'data', f'cam_{view}_joint2.npy')
    np.save(out_path, p)
    print(f'\nсохранено: {out_path}')
    return p, f


if __name__ == '__main__':
    for view in ('back', 'left'):
        report(view)
        print()
