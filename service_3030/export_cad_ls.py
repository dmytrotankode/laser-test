"""Выгрузить .LS по траектории из CAD - без библиотеки поз.

Форма берётся из модели, поза - из двух снимков (разметка сгиба плюс опорные
числа силуэта). Ни соседа, ни матрицы 150x6 в расчёте нет.

ЧТО ВСЁ ЖЕ БЕРЁТСЯ ИЗ АРХИВА, и это надо знать:

* программа соседа служит ТЕКСТОВЫМ ШАБЛОНОМ - заголовки, скорости, номера
  точек. Так же поступает и step05 в 5056;
* ориентация инструмента W/P/R в шаблоне НЕ переписывается. Это уже не только
  текст, а геометрия: углы подхода останутся от соседа. Для сравнения траекторий
  это правильно (сравниваем линии реза), но полностью независимым от архива
  такой файл называть нельзя.

Точки кромки модели переносятся на сетку шаблона по ближайшей точке, чтобы
сохранить количество и порядок, которых ждёт робот. Расстановка от этого чуть
неравномерная, сама траектория та же.

    python export_cad_ls.py v21 v24
"""
import os
import re
import sys
import argparse
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
S5056 = os.path.abspath(os.path.join(BASE, '..', 'service_5056'))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(S5056, 'scripts'))

import lsgeom                                            # noqa: E402
import features as f5                                    # noqa: E402
import fit_model                                         # noqa: E402
import line_features                                     # noqa: E402
import export_scene as XS                                # noqa: E402
import export_ls as X                                    # noqa: E402
import exp_cad_fit as F                                  # noqa: E402
import exp_camera_fit as E                               # noqa: E402
import exp_all_methods as A                              # noqa: E402
import exp_observability as O                            # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

OUT = os.path.join(BASE, 'out')


def export(variant, rim, verts, marks, cams, R0, t0, F_all):
    fit_model.standoff(variant)
    _, P = O.fit(variant, rim, verts, marks, cams, R0, t0, True)

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
    name = lsgeom.program_name(f'cad_{variant}')
    text = X.POINT_RE.sub(replace, text)
    text = re.sub(r'(/PROG\s+)\S+', lambda m: m.group(1) + name, text, count=1)
    text = re.sub(r'(FILE_NAME\s*=\s*)[^;]*', lambda m: m.group(1) + name[:8],
                  text, count=1)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f'{name}.LS')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

    back = lsgeom.load(path)
    got, _ = lsgeom.cut_surface(back, lsgeom.NOMINAL_STANDOFF)
    own = E.ring(variant, 0.0)
    d = lsgeom.curve_distance(got, own)
    dz = lsgeom.curve_distance(E.ring(nb, 0.0), own)
    print(f'{variant}: {path}')
    print(f'   шаблон {nb} (только текст и углы W/P/R)')
    print(f'   против записанной: среднее {d.mean():.2f}  макс {d.max():.2f}  '
          f'в допуске 2мм {100 * np.mean(d <= 2):.0f}%')
    print(f'   сосед как есть:    среднее {dz.mean():.2f}  макс {dz.max():.2f}  '
          f'в допуске 2мм {100 * np.mean(dz <= 2):.0f}%')
    return path


def main(variants):
    marks = line_features.load_marks()
    rim = XS.mesh_rim(F.STL)
    verts = np.unique(F.load_stl(F.STL).reshape(-1, 3), axis=0)
    cams = X.cameras()
    R0, t0 = A.cad_start()
    every = A.TRAIN + A.CLEAN
    for v in every:
        fit_model.standoff(v)
    F_all = f5.load(every)
    for v in variants:
        export(v, rim, verts, marks, cams, R0, t0, F_all)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('variants', nargs='+')
    main(ap.parse_args().variants)
