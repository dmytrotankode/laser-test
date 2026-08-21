"""Выгрузить .LS лучшим известным способом на сегодня: контур top + маркерные камеры.

export_cad_ls.py считает позу через exp_observability.fit - силуэт двух камер,
три грубых числа (box2/box3), без контура. exp_top_contour.py показал, что
полный контур сверху даёт заметно лучше (15-17% -> 56% на чужих). Этот файл
берёт готовую подгонку из exp_top_contour.resid_of(mode='contour') и то же
самое построение .LS-файла (подстановка в шаблон соседа), что и export_cad_ls.py -
меняется только СПОСОБ НАЙТИ ПОЗУ, не способ ЗАПИСАТЬ файл.

Камеры - маркерные (exp_three_cams.marker_cams, лучевая калибровка 20-21.08),
не старые из export_ls.cameras().

    python export_cad_ls_contour.py v21 v24
"""
import os
import re
import sys
import argparse
import numpy as np
import cv2
from scipy.optimize import least_squares

BASE = os.path.dirname(os.path.abspath(__file__))
S5056 = os.path.abspath(os.path.join(BASE, '..', 'service_5056'))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(S5056, 'scripts'))

import lsgeom                                            # noqa: E402
import features as f5                                    # noqa: E402
import fit_model                                          # noqa: E402
import line_features                                      # noqa: E402
import export_scene as XS                                 # noqa: E402
import export_ls as X                                      # noqa: E402
import exp_cad_fit as F                                     # noqa: E402
import exp_camera_fit as E                                   # noqa: E402
import exp_all_methods as A                                   # noqa: E402
import exp_three_cams as T                                     # noqa: E402
import exp_top_contour as TC                                    # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

OUT = os.path.join(BASE, 'out')


def export(variant, rim, verts, marks, cams, R0, t0, F_all):
    # У НОВОГО шлема (первый физический рез, ещё не резался) записанной
    # программы нет вообще - сравнивать не с чем, и это нормально, не ошибка.
    # Генерация .LS от этого не зависит (она берёт форму из CAD + позу из фото),
    # зависит только блок "против записанной" ниже.
    has_ground_truth = os.path.exists(os.path.join(
        S5056, 'input', 'archive', variant, 'ground_truth.ls'))
    if has_ground_truth:
        fit_model.standoff(variant)

    r = least_squares(TC.resid_of(variant, rim, verts, marks, cams, R0, t0, 'contour'),
                      np.r_[np.zeros(6), 12.0], method='lm', max_nfev=900)
    R = cv2.Rodrigues(r.x[:3])[0] @ R0
    P = rim @ R.T + t0 + r.x[3:6]
    skirt = r.x[6]

    nb = fit_model.nearest(variant, [u for u in A.TRAIN if u != variant], F_all, 'prof')
    src = os.path.join(S5056, 'input', 'archive', nb, 'ground_truth.ls')
    tmpl = lsgeom.load(src)
    st = fit_model.standoff(nb)
    cut_full, ids_full = lsgeom.cut_surface(tmpl, st, full=True)
    axis_by_id = dict(zip(ids_full, lsgeom.tool_axes(tmpl, ids_full)))
    cut_by_id = dict(zip(ids_full, np.asarray(cut_full, float)))

    def on_cad(pt):
        return P[int(np.argmin(np.linalg.norm(P - pt, axis=1)))]

    def replace(m):
        i = int(m.group(2))
        pt = np.array(tmpl.points[i][:3], float)
        if i in cut_by_id:
            pt = on_cad(cut_by_id[i]) + lsgeom.NOMINAL_STANDOFF * axis_by_id[i]
        return (f'{m.group(1)}{pt[0]:.3f}{m.group(4)}{pt[1]:.3f}'
                f'{m.group(6)}{pt[2]:.3f}')

    text = open(src, encoding='utf-8', errors='ignore').read()
    name = lsgeom.program_name(f'cadc_{variant}')
    text = X.POINT_RE.sub(replace, text)
    text = re.sub(r'(/PROG\s+)\S+', lambda m: m.group(1) + name, text, count=1)
    text = re.sub(r'(FILE_NAME\s*=\s*)[^;]*', lambda m: m.group(1) + name[:8],
                  text, count=1)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f'{name}.LS')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f'{variant}: {path}')
    print(f'   шаблон {nb} (только текст и углы W/P/R), запас юбки {skirt:.1f} мм')

    if not has_ground_truth:
        print('   записанной программы нет (новый шлем, ещё не резался) - '
              'сравнить не с чем, это ожидаемо. Сверить после физического реза.')
        return path

    back = lsgeom.load(path)
    got, _ = lsgeom.cut_surface(back, lsgeom.NOMINAL_STANDOFF)
    own = E.ring(variant, 0.0)
    d = lsgeom.curve_distance(got, own)
    dz = lsgeom.curve_distance(E.ring(nb, 0.0), own)
    print(f'   против записанной: среднее {d.mean():.2f}  макс {d.max():.2f}  '
          f'в допуске 2мм {100 * np.mean(d <= 2):.0f}%')
    print(f'   сосед как есть:    среднее {dz.mean():.2f}  макс {dz.max():.2f}  '
          f'в допуске 2мм {100 * np.mean(dz <= 2):.0f}%')

    old_path = os.path.join(OUT, f'DISTI_CAD_{variant.upper()}.LS')
    if os.path.exists(old_path):
        old = lsgeom.load(old_path)
        got_old, _ = lsgeom.cut_surface(old, lsgeom.NOMINAL_STANDOFF)
        d_old = lsgeom.curve_distance(got_old, own)
        print(f'   старый export_cad_ls.py ({os.path.basename(old_path)}): '
              f'среднее {d_old.mean():.2f}  макс {d_old.max():.2f}  '
              f'в допуске 2мм {100 * np.mean(d_old <= 2):.0f}%')
    return path


def main(variants):
    marks = line_features.load_marks()
    rim = XS.mesh_rim(F.STL)
    verts = np.unique(F.load_stl(F.STL).reshape(-1, 3), axis=0)
    cams = T.marker_cams()
    R0, t0 = A.cad_start()
    every = A.TRAIN + A.CLEAN
    for v in every:
        fit_model.standoff(v)
    # Новый вариант тоже нужен в F_all - fit_model.nearest сравнивает его силуэт
    # с пулом TRAIN, значит его собственный признак должен быть посчитан тоже.
    F_all = f5.load(every + [v for v in variants if v not in every])
    for v in variants:
        export(v, rim, verts, marks, cams, R0, t0, F_all)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('variants', nargs='+')
    main(ap.parse_args().variants)
