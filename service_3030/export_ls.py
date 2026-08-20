"""Выгрузить .LS по позе, уточнённой линией сгиба - чтобы сравнить руками.

Числа расхождения кривых - это мои числа и мой измеритель. Файл программы можно
взять и сравнить с чужими результатами независимо, поэтому он и нужен.

Как строится, ровно как в step05_visualize_export: берётся .LS СОСЕДА и в нём
переписываются только X/Y/Z каждой точки контура, а всё остальное - заголовки,
скорости, W/P/R - остаётся байт в байт. Тогда оси инструмента, по которым робот
пойдёт, это оси шаблона, и обратный переход от линии реза к позе сопла
согласован по построению.

Отличие от 5056 одно: поправка берётся не из матрицы 150x6, а из подгонки
эталонного кольца к линии сгиба на двух снимках (exp_pose_from_line).

    python export_ls.py v13                 сосед выбирается правилом 5056
    python export_ls.py v13 --neighbour v5

Пишет в service_3030/out/. В service_5056 ничего не создаётся и не меняется.
"""
import os
import re
import sys
import json
import argparse
import numpy as np
import cv2
from scipy.optimize import least_squares

BASE = os.path.dirname(os.path.abspath(__file__))
S5056 = os.path.abspath(os.path.join(BASE, '..', 'service_5056'))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(S5056, 'scripts'))

import line_features                                    # noqa: E402
import dataset                                          # noqa: E402
import features as feat5056                             # noqa: E402
import fit_model                                        # noqa: E402
import lsgeom                                           # noqa: E402
import exp_camera_fit as E                              # noqa: E402
from bench import dist_to_polyline                      # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

FOLD_OFFSET = 2.3
VIEWS = ('back', 'left')
OUT = os.path.join(BASE, 'out')

POINT_RE = re.compile(
    r'(P\[(\d+)\]\{.*?X\s*=\s*)([-\d.]+)(.*?Y\s*=\s*)([-\d.]+)(.*?Z\s*=\s*)([-\d.]+)',
    re.DOTALL | re.IGNORECASE)


def cameras():
    foc = json.load(open(E.LASER_CAMS, encoding='utf-8'))
    return {w: (np.load(os.path.join(BASE, 'data', f'cam_{w}.npy')), foc[w]['focus'])
            for w in VIEWS}


def resample(a, n=120):
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(a, axis=0).T))]
    t = np.linspace(0, d[-1], n)
    return np.c_[np.interp(t, d, a[:, 0]), np.interp(t, d, a[:, 1])]


def pose_from_line(variant, neighbour, marks, cams):
    """Жёсткое движение, при котором кольцо соседа садится на разметку варианта."""
    ref_fold = E.ring(neighbour, FOLD_OFFSET)

    def resid(p6):
        R = cv2.Rodrigues(p6[:3])[0]
        X = ref_fold @ R.T + p6[3:6]
        out = []
        for w in VIEWS:
            pc, f = cams[w]
            uv, z = E.project(X, pc[:3], pc[3:6], f)
            d = np.abs(dist_to_polyline(resample(marks[variant][w]), E.near_arc(uv, z)))
            out.append(d * float(np.median(z)) / f)
        return np.concatenate(out)

    # Обычный МНК, и это выбор по замеру, а не по умолчанию (exp_loss.py).
    #
    # Для реза решает худшее место, поэтому напрашивался минимакс - и на
    # мастер-шлеме он действительно лучше (78 % точек в допуске 2 мм против 64).
    # Но на ЧУЖИХ шлемах он рушится: 15 % против 57. Причина не в оптимизаторе:
    # у чужого экземпляра форма кольца своя, в остатке сидит неустранимая
    # разница формы, и минимакс отдаёт ей всю подгонку. Устойчивая потеря
    # (soft_l1) хуже везде - она глушит большие остатки, а у чужого шлема
    # большим является почти весь контур, то есть глушится сигнал.
    #
    # Агрегат по всем наборам этот провал МАСКИРУЕТ: там минимакс выглядел
    # выигрышем, потому что мастер-шлемов в выборке большинство. Смотреть надо
    # по группам.
    p = least_squares(resid, np.zeros(6), method='lm', max_nfev=300).x
    return cv2.Rodrigues(p[:3])[0], p[3:6], float(np.max(resid(p)))


def export(variant, neighbour=None):
    marks = line_features.load_marks()
    train = [v for v in dataset.TRAIN if v != 'v2']
    pool = [u for u in train if u != variant]
    for v in set(pool + [variant]):
        fit_model.standoff(v)
    if neighbour is None:
        F = feat5056.load(pool + [variant])
        neighbour = fit_model.nearest(variant, pool, F, 'prof')
    print(f'Вариант {variant}, сосед {neighbour} '
          f'({"правило 5056" if neighbour else "задан вручную"})')

    R, t, resid = pose_from_line(variant, neighbour, marks, cameras())
    # ypr_from_rot отдаёт УЖЕ градусы - переводить второй раз нельзя
    ypr = np.round(lsgeom.ypr_from_rot(R), 3)
    print(f'Поправка по линии: сдвиг {np.round(t, 2)} мм, '
          f'yaw/pitch/roll {ypr}°, худший остаток на снимках {resid:.2f} мм')

    src = os.path.join(S5056, 'input', 'archive', neighbour, 'ground_truth.ls')
    tmpl = lsgeom.load(src)
    _, cont_ids, _ = tmpl.split_path()
    st = fit_model.standoff(neighbour)
    cut_full, ids_full = lsgeom.cut_surface(tmpl, st, full=True)
    axis_by_id = dict(zip(ids_full, lsgeom.tool_axes(tmpl, ids_full)))
    cut_by_id = dict(zip(ids_full, np.asarray(cut_full, float)))

    def replace(m):
        i = int(m.group(2))
        pt = np.array(tmpl.points[i][:3], float)
        if i in cut_by_id:
            # правим в координатах ЛИНИИ РЕЗА и возвращаемся к соплу по оси шаблона
            pt = cut_by_id[i] @ R.T + t + lsgeom.NOMINAL_STANDOFF * axis_by_id[i]
        return (f'{m.group(1)}{pt[0]:.3f}{m.group(4)}{pt[1]:.3f}'
                f'{m.group(6)}{pt[2]:.3f}')

    text = open(src, encoding='utf-8', errors='ignore').read()
    name = lsgeom.program_name(f'line_{variant}')
    text = POINT_RE.sub(replace, text)
    text = re.sub(r'(/PROG\s+)\S+', lambda m: m.group(1) + name, text, count=1)
    text = re.sub(r'(FILE_NAME\s*=\s*)[^;]*', lambda m: m.group(1) + name[:8],
                  text, count=1)

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f'{name}.LS')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

    # непогружаемая программа хуже отсутствующей - перечитываем то, что записали
    back = lsgeom.load(path)
    got, _ = lsgeom.cut_surface(back, lsgeom.NOMINAL_STANDOFF)
    own = E.ring(variant, 0.0)
    nb_as_is = E.ring(neighbour, 0.0)
    print(f'Записано: {path}  ({len(back.points)} точек, контур {len(cont_ids)})')
    d, dz = (lsgeom.curve_distance(got, own), lsgeom.curve_distance(nb_as_is, own))
    # для реза решает худшее место и доля в допуске, а не среднее
    print(f'   против записанной {variant}: среднее {d.mean():.2f}  макс {d.max():.2f}  '
          f'в допуске 2мм {100 * np.mean(d <= 2):.0f}%')
    print(f'   сосед как есть:     среднее {dz.mean():.2f}  макс {dz.max():.2f}  '
          f'в допуске 2мм {100 * np.mean(dz <= 2):.0f}%')
    return path


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('variant')
    ap.add_argument('--neighbour', default=None)
    a = ap.parse_args()
    export(a.variant, a.neighbour)
