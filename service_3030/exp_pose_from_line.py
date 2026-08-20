"""Поза шлема по линии сгиба на двух ракурсах - без библиотеки и без k-NN.

Схема, которую с самого начала предлагал заказчик: нашли линию, сравнили с
эталонной, повернули на ту же величину, пошли резать. Теперь её можно проверить:
камеры посчитаны в координатах станка (exp_camera_joint), а линия сгиба - это
линия реза со сдвигом 2.3 мм вдоль оси инструмента (там же измерено).

Ищется жёсткое движение T, при котором проекция ЭТАЛОННОГО кольца в обе камеры
садится на разметку нового снимка. Соответствие точек не нужно - кривая к кривой.

КАК ЭТО ЧЕСТНО ПРОВЕРИТЬ

* мера - та же, что во всём 5056: `lsgeom.curve_distance` между сдвинутым
  эталонным кольцом и ЗАПИСАННОЙ программой варианта, в мм. Так число прямо
  сравнимо с LOO=1.23 мм у нынешней модели;
* программа самого варианта в подгонку не входит вообще: T строится только по
  двум фотографиям;
* камеры пересчитываются БЕЗ этого варианта. Иначе его разметка попала бы в
  калибровку, и проверка перестала бы быть проверкой;
* контроль «ничего не делать»: эталонное кольцо как есть. У 5056 этот контроль
  даёт 1.90 мм, и всё, что не лучше него, бессмысленно.

    python exp_pose_from_line.py
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

import line_features                                    # noqa: E402
import dataset                                          # noqa: E402
import fit_model                                        # noqa: E402
import lsgeom                                           # noqa: E402
import exp_camera_joint as J                            # noqa: E402
import exp_camera_fit as E                              # noqa: E402
from bench import dist_to_polyline                      # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

REF = 'v1'
FOLD_OFFSET = 2.3          # сгиб выше реза, мм вдоль оси инструмента (exp_camera_joint)
VIEWS = ('back', 'left')


def cameras(variants, marks, exclude=None):
    """Обе камеры, посчитанные БЕЗ указанного варианта."""
    names = [v for v in variants if v != exclude]
    out = {}
    for view in VIEWS:
        f = json.load(open(E.LASER_CAMS, encoding='utf-8'))[view]['focus']
        x0 = np.load(os.path.join(BASE, 'data', f'cam_{view}.npy'))
        out[view] = (J.fit(view, names, marks, f, x0), f)
    return out


def pose_error(p6, cams, marks, variant, ref_fold):
    """Расхождение проекции повёрнутого эталона с разметкой, мм на детали."""
    R = cv2.Rodrigues(p6[:3])[0]
    X = ref_fold @ R.T + p6[3:6]
    out = []
    for view in VIEWS:
        (pc, f) = cams[view]
        uv, z = E.project(X, pc[:3], pc[3:6], f)
        d = np.abs(dist_to_polyline(marks[variant][view], E.near_arc(uv, z)))
        out.append(d * float(np.median(z)) / f)
    return np.concatenate(out)


def main():
    marks = line_features.load_marks()
    train = [v for v in dataset.TRAIN if v != 'v2']
    held = list(dataset.HELDOUT)
    for v in train + held:
        fit_model.standoff(v)

    ref_fold = E.ring(REF, FOLD_OFFSET)          # эталонная линия СГИБА
    ref_cut = E.ring(REF, 0.0)                   # эталонная линия РЕЗА
    print(f'Эталон {REF}. Поза ищется только по двум снимкам; программа варианта '
          f'в подгонке не участвует.\n')
    print(f"{'вариант':<9}{'по линии':>10}{'ничего не делать':>20}{'разметка':>12}")

    rows = []
    for v in train + held:
        cams = cameras(train, marks, exclude=v)
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
    print(f'у нынешней модели 5056 по тому же измерителю: LOO 1.23 мм, '
          f'контроль «ничего не делать» 1.90 мм')


if __name__ == '__main__':
    main()
