"""Калибровка камер по маркерным точкам (20.08), независимо от .LS-метода.

Источник: `laserdot_2/calib_correspondences.csv` - 40 пар пиксель<->3D (UFRAME2),
получены наведением сопла на промаркерные точки на шлеме и ручной разметкой
пикселя в вебе (`laserdot_2/mark.html`), с уточнением центра пятна по маленькому
окну вокруг клика.

ГЛАВНЫЙ ВЫВОД ЭТОГО ПРОХОДА. Старая калибровка (L4_cameras.json, посчитана по
.LS + лазерным пятнам на кольце реза) проверена на этих точках - камера их не
видела вообще. `back` держится посредственно (8.5 мм на своих точках, было
0.3-1.3 на пятнах), `left` проваливается катастрофически (90-100 мм). Кольцо
реза почти плоское, и веса вдоль слабых направлений позы там не закреплены -
именно ловушка №9/№2 хендоффа: то, что хорошо объясняет плоскую мишень, может
быть далеко от истины на объёмной.

Свежая калибровка (PnP по маркерным точкам ЭТОЙ ЖЕ камеры, без чужих) для всех
трёх камер ложится на 0.2-1.0 мм - на уровне исходного эталона §4e. Причём
СВОБОДНЫЙ ФОКУС ЗДЕСЬ ДЕРЖИТСЯ (расходится не больше чем на 10% от закреплённого) -
в отличие от силуэта кольца, который на свободном фокусе вырождался. Маркерные
точки объёмны (весь купол, а не плоское кольцо) - видимо поэтому.

Точки, снятые ПОД БОЛЬШИМ УГЛОМ с чужой камеры (напр. `13`, `14` видны и с
`left`, и с `back`), в подгонку позы этой камеры НЕ идут - на грани обзора
чернильная точка размазывается, а прицел сопла даёт наводочную ошибку тем
больше, чем острее угол (MARKER_POINTS.md, 0.4-0.6 мм/градус). Используются
отдельно - как независимая межкамерная проверка уже готовой позы.

service_5056 только читается. Ничего не перезаписывает существующие .npy.

    python exp_marker_calib.py
"""
import os
import sys
import csv
import json
import numpy as np
import cv2

BASE = os.path.dirname(os.path.abspath(__file__))
S5056 = os.path.abspath(os.path.join(BASE, '..', 'service_5056'))
NEW0810 = os.path.join(S5056, 'scratch', 'new0810')
LASER_CAMS = os.path.join(NEW0810, 'L4_cameras.json')
CORR = os.path.join(BASE, '..', 'laserdot_2', 'calib_correspondences.csv')

IMG_W, IMG_H = 4096, 3000
OWN_RANGE = {'top': range(1, 9), 'back': range(19, 27), 'left': range(9, 19)}

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def load_correspondences():
    by_view = {}
    with open(CORR, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            by_view.setdefault(row['view'], []).append({
                'point': row['point'],
                'uv': (float(row['u']), float(row['v'])),
                'XYZ': (float(row['X']), float(row['Y']), float(row['Z'])),
            })
    return by_view


def own_and_cross(pts, view):
    own = [p for p in pts if int(p['point']) in OWN_RANGE[view]]
    cross = [p for p in pts if int(p['point']) not in OWN_RANGE[view]]
    return own, cross


def project(X, rvec, C, f):
    """Та же дырочная камера, что в exp_camera_fit.py: без дисторсии, гп в центре."""
    R = cv2.Rodrigues(np.asarray(rvec, float))[0]
    Xc = (np.asarray(X, float) - np.asarray(C, float)) @ R.T
    z = np.maximum(Xc[:, 2], 1e-6)
    return np.c_[f * Xc[:, 0] / z + IMG_W / 2, f * Xc[:, 1] / z + IMG_H / 2], Xc[:, 2]


def reproj_report(view, pts, rvec, C, f, label, n_worst=3):
    if not pts:
        return
    X = np.array([p['XYZ'] for p in pts])
    uv_obs = np.array([p['uv'] for p in pts])
    uv_pred, z = project(X, rvec, C, f)
    err_px = np.linalg.norm(uv_pred - uv_obs, axis=1)
    err_mm = err_px * z / f
    print(f'  [{label}] {view}: n={len(pts)}  '
          f'px медиана {np.median(err_px):.1f} макс {np.max(err_px):.1f}   '
          f'мм медиана {np.median(err_mm):.2f} макс {np.max(err_mm):.2f}')
    order = np.argsort(-err_mm)[:n_worst]
    for i in order:
        print(f'      худшая: точка {pts[i]["point"]:>3}  {err_mm[i]:.2f} мм')
    return err_mm


def solve_pnp(pts, focus0):
    X = np.array([p['XYZ'] for p in pts], dtype=np.float64)
    uv = np.array([p['uv'] for p in pts], dtype=np.float64)
    K = np.array([[focus0, 0, IMG_W / 2], [0, focus0, IMG_H / 2], [0, 0, 1]], dtype=np.float64)
    # ITERATIVE без стартовой позы (DLT-инициализация) на этих точках расходится.
    # EPnP устойчивее без старта, им и инициализируем, потом дотачиваем ITERATIVE.
    _, rvec0, tvec0 = cv2.solvePnP(X, uv, K, None, flags=cv2.SOLVEPNP_EPNP)
    _, rvec, tvec = cv2.solvePnP(X, uv, K, None, rvec0, tvec0,
                                  useExtrinsicGuess=True, flags=cv2.SOLVEPNP_ITERATIVE)
    R = cv2.Rodrigues(rvec)[0]
    C = (-R.T @ tvec).ravel()
    return rvec.ravel(), C


def free_focus_check(pts, focus0):
    X = np.array([p['XYZ'] for p in pts], dtype=np.float32)
    uv = np.array([p['uv'] for p in pts], dtype=np.float32)
    K0 = np.array([[focus0, 0, IMG_W / 2], [0, focus0, IMG_H / 2], [0, 0, 1]], dtype=np.float64)
    flags = (cv2.CALIB_USE_INTRINSIC_GUESS | cv2.CALIB_FIX_PRINCIPAL_POINT |
             cv2.CALIB_ZERO_TANGENT_DIST | cv2.CALIB_FIX_K1 | cv2.CALIB_FIX_K2 |
             cv2.CALIB_FIX_K3 | cv2.CALIB_FIX_ASPECT_RATIO)
    _, K, _, rvecs, tvecs = cv2.calibrateCamera([X], [uv], (IMG_W, IMG_H), K0, None, flags=flags)
    R = cv2.Rodrigues(rvecs[0])[0]
    C = (-R.T @ tvecs[0]).ravel()
    return rvecs[0].ravel(), C, float(K[0, 0])


def step1_old_calibration_check(by_view, cams):
    print('=== Шаг 1: старая калибровка (back/left) против ВСЕХ новых точек, без подгонки\n')
    for view in ('back', 'left'):
        if view not in by_view:
            continue
        cam = cams[view]
        rvec, C, f = cam['x'][:3], cam['x'][3:6], cam['focus']
        own, cross = own_and_cross(by_view[view], view)
        reproj_report(view, own, rvec, C, f, 'старая калибровка, свои точки')
        reproj_report(view, cross, rvec, C, f, 'старая калибровка, чужие/угловые')
    print()


def step2_fresh_calibration(by_view, cams):
    print('=== Шаг 2: свежая калибровка каждой камеры по её СВОИМ точкам\n')
    focus_default = float(np.mean([cams['back']['focus'], cams['left']['focus']]))
    results = {}
    for view in ('back', 'left', 'top'):
        if view not in by_view:
            continue
        own, cross = own_and_cross(by_view[view], view)
        focus0 = cams[view]['focus'] if view in cams else focus_default
        print(f'--- {view}: {len(own)} своих точек, старт-фокус {focus0:.0f} px')
        rvec, C = solve_pnp(own, focus0)
        reproj_report(view, own, rvec, C, focus0, 'PnP по своим, фокус закреплён')

        rvec_f, C_f, f_free = free_focus_check(own, focus0)
        held = abs(f_free - focus0) < focus0 * 0.15
        print(f'    свободный фокус -> {f_free:.0f} px '
              f'({"держит" if held else "УЕХАЛ, вырождается"})')

        if cross:
            print(f'    независимая проверка по {len(cross)} чужим/угловым точкам '
                  f'(не участвовали в подгонке этой камеры):')
            reproj_report(view, cross, rvec, C, focus0, '   чужие точки', n_worst=len(cross))

        out_path = os.path.join(BASE, 'data', f'cam_{view}_marker.npy')
        np.save(out_path, np.r_[rvec, C, focus0])
        print(f'    сохранено: {out_path}\n')
        results[view] = {'rvec': rvec.tolist(), 'C': C.tolist(), 'focus': focus0}
    return results


def main():
    cams = json.load(open(LASER_CAMS, encoding='utf-8'))
    by_view = load_correspondences()
    step1_old_calibration_check(by_view, cams)
    step2_fresh_calibration(by_view, cams)


if __name__ == '__main__':
    main()
