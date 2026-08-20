"""То же, что exp_pose_from_line.py, но на камерах от маркерной калибровки (20.08).

exp_pose_from_line.py каждый раз ПЕРЕСЧИТЫВАЕТ back/left по .LS+пятнам, исключая
тестируемый вариант - так делать, чтобы разметка варианта не утекла в камеру.
Маркерным точкам утекать неоткуда: они вообще не знают про существование
вариантов v1..v25, набраны отдельно 18.08. Поэтому здесь камера ОДНА и ФИКСИРОВАНА
для всех вариантов - честно и без пересчёта на каждом шаге.

Смысл прогона: exp_pose_from_line.py считался на камере `left`, которая в этот же
день (20.08) оказалась сломана на маркерных точках (91 мм). Если часть разрыва до
потолка в HANDOFF §2 была не наблюдаемостью, а плохой камерой - здесь это должно
всплыть как явное улучшение.

    python exp_pose_from_line_marker.py
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

import line_features                                    # noqa: E402
import dataset                                          # noqa: E402
import fit_model                                        # noqa: E402
import lsgeom                                           # noqa: E402
import exp_camera_fit as E                              # noqa: E402
from bench import dist_to_polyline                      # noqa: E402
import json                                              # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

REF = 'v1'
FOLD_OFFSET = 2.3
VIEWS = ('back', 'left')


def load_marker_cams():
    """cam_*_joint2.npy = [rvec(3), C(3), отступ сгиба(1)] - фокус там НЕ хранится,
    он был зафиксирован при подгонке (exp_camera_joint_marker.py) и берётся из
    того же LASER_CAMS, что и раньше."""
    out = {}
    for view in VIEWS:
        arr = np.load(os.path.join(BASE, 'data', f'cam_{view}_joint2.npy'))
        rvec, C = arr[:3], arr[3:6]
        f = json.load(open(E.LASER_CAMS, encoding='utf-8'))[view]['focus']
        out[view] = ((rvec, C), f)
    return out


def pose_error(p6, cams, marks, variant, ref_fold):
    R = cv2.Rodrigues(p6[:3])[0]
    X = ref_fold @ R.T + p6[3:6]
    out = []
    for view in VIEWS:
        (pc, f) = cams[view]
        uv, z = E.project(X, pc[0], pc[1], f)
        d = np.abs(dist_to_polyline(marks[variant][view], E.near_arc(uv, z)))
        out.append(d * float(np.median(z)) / f)
    return np.concatenate(out)


def main():
    marks = line_features.load_marks()
    train = [v for v in dataset.TRAIN if v != 'v2']
    held = list(dataset.HELDOUT)
    for v in train + held:
        fit_model.standoff(v)

    cams = load_marker_cams()
    ref_fold = E.ring(REF, FOLD_OFFSET)
    ref_cut = E.ring(REF, 0.0)
    print(f'Эталон {REF}. Камеры фиксированы (маркерная калибровка 20.08), '
          f'не пересчитываются по вариантам.\n')
    print(f"{'вариант':<9}{'по линии':>10}{'ничего не делать':>20}{'разметка':>12}")

    rows = []
    for v in train + held:
        r = least_squares(pose_error, np.zeros(6),
                          args=(cams, marks, v, ref_fold), method='lm', max_nfev=200)
        R = cv2.Rodrigues(r.x[:3])[0]
        moved = ref_cut @ R.T + r.x[3:6]
        own = E.ring(v, 0.0)
        err = float(lsgeom.curve_distance(moved, own).mean())
        zero = float(lsgeom.curve_distance(ref_cut, own).mean())
        resid = float(np.median(np.abs(r.fun)))
        rows.append((v, err, zero, resid))
        print(f'{v:<9}{err:>10.2f}{zero:>20.2f}{resid:>12.2f}')

    a = np.array([r[1] for r in rows])
    b = np.array([r[2] for r in rows])
    print(f'\nсреднее: по линии {a.mean():.2f} мм, ничего не делать {b.mean():.2f} мм, '
          f'худший по линии {a.max():.2f}')
    print(f'для сравнения (та же мера): exp_pose_from_line.py на старых камерах, '
          f'модель 5056 LOO 1.23 мм, контроль «ничего не делать» 1.90 мм')


if __name__ == '__main__':
    main()
