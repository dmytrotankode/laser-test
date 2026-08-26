r"""Собрать сцену для правки - берёт СЫРЫЕ файлы по явным путям, не код 3030/5056.

Никаких sys.path в чужие сервисы и никаких их импортов - только:
  - текстовый .LS (парсит ls_points.py, свой),
  - .npy камеры: ровно 7 чисел [rvec(3), позиция(3), фокус], numpy.load,
  - обычные картинки (просто копируются).

Если 3030 или 5056 переименуют свои скрипты, эта команда не сломается - ей всё
равно, откуда взялись файлы, важен только их формат, а он стабилен (формат
контроллера робота и формат камеры, а не чей-то python-код).

    python build_scene.py v26 ^
        --ls "..\service_3030\out\DISTI_CADC_V26.LS" ^
        --cam-back "..\service_3030\data\cam_back_marker.npy" ^
        --cam-left "..\service_3030\data\cam_left_marker.npy" ^
        --cam-top  "..\service_3030\data\cam_top_marker.npy" ^
        --photo-back "..\service_5056\input\archive\v26\back.png" ^
        --photo-left "..\service_5056\input\archive\v26\left.png" ^
        --photo-top  "..\service_5056\input\archive\v26\top.png"
"""
import os
import sys
import shutil
import argparse
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ls_points                                          # noqa: E402
import scene as S                                          # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def load_cam(path):
    """.npy: [rvec(3), позиция(3), фокус] - весь контракт, больше ничего не знаем."""
    a = np.load(path)
    if a.shape != (7,):
        raise ValueError(f'{path}: ожидал 7 чисел [rvec,pos,focus], получил {a.shape}')
    return a[:3], a[3:6], float(a[6])


def reference_curves(reference_path):
    """Эталон - и как линия реза (эталон - сопло минус его же отступ), и как
    путь сопла (то, что реально записано в файле). Обе нередактируемые."""
    ref_pts = ls_points.read_ring(reference_path)
    if not ref_pts:
        print(f'  эталон {reference_path}: не нашлось точек, пропускаю')
        return []
    name = os.path.basename(reference_path)
    print(f'  эталон: {name}, {len(ref_pts)} точек')
    return [
        S.curve(f'эталон, линия реза ({name})', [list(p[2]) for p in ref_pts],
               '#22c55e', closed=True, width=2),
        S.curve(f'эталон, путь сопла ({name})', [list(p[1]) for p in ref_pts],
               '#86efac', closed=True, width=1),
    ]


def build(variant, ls_path, cams, photos, reference_path=None):
    pts = ls_points.read_ring(ls_path)
    if not pts:
        raise SystemExit(f'в {ls_path} не нашлось ни одной точки P[..]{{X=...}}')
    ids = [p[0] for p in pts]
    cut_xyz = [list(p[2]) for p in pts]      # линия РЕЗА, не путь сопла
    axes = [list(p[3]) for p in pts]
    print(f'{variant}: {len(pts)} точек из {os.path.basename(ls_path)} '
          f'(показывается линия реза, отступ {ls_points.NOMINAL_STANDOFF} мм уже вычтен)')

    dst = S.asset_dir(variant)
    # исходный .LS - шаблон для финальной сборки, копия рядом со сценой,
    # чтобы 2021 не зависел от того, жив ли ещё файл в out/ у 3030
    shutil.copy(ls_path, os.path.join(dst, 'template.ls'))

    cam_objs = []
    for view in ('back', 'left', 'top'):
        img_name = None
        if photos.get(view) and os.path.exists(photos[view]):
            img_name = f'{view}.jpg'
            shutil.copy(photos[view], os.path.join(dst, img_name))
        if cams.get(view):
            rvec, pos, focal = load_cam(cams[view])
            cam_objs.append(S.camera(view, position=pos, rotation=rvec,
                                     focal_px=focal, image=img_name))

    nozzle_xyz = [list(p[1]) for p in pts]
    curve = S.curve(f'линия реза (расчёт, {variant})', cut_xyz, '#3b82f6',
                    closed=True, width=2, editable=True, ids=ids, axes=axes)
    curves = [curve,
             S.curve(f'путь сопла (расчёт, {variant})', nozzle_xyz, '#93c5fd', closed=True, width=1)]

    if reference_path:
        curves += reference_curves(reference_path)

    path = S.write(variant, cameras=cam_objs, curves=curves,
                   note=f'{variant}: из {os.path.basename(ls_path)}, довести руками')
    print(f'сцена готова: {path}')
    print('открыть: http://localhost:2021')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('variant')
    ap.add_argument('--ls', required=True)
    ap.add_argument('--cam-back')
    ap.add_argument('--cam-left')
    ap.add_argument('--cam-top')
    ap.add_argument('--photo-back')
    ap.add_argument('--photo-left')
    ap.add_argument('--photo-top')
    ap.add_argument('--reference', help='эталонный .LS для этих же фото, если есть')
    a = ap.parse_args()
    build(a.variant, a.ls,
         {'back': a.cam_back, 'left': a.cam_left, 'top': a.cam_top},
         {'back': a.photo_back, 'left': a.photo_left, 'top': a.photo_top},
         reference_path=a.reference)
