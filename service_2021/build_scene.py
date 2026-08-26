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


def build(variant, ls_path, cams, photos):
    pts = ls_points.read_points(ls_path)
    if not pts:
        raise SystemExit(f'в {ls_path} не нашлось ни одной точки P[..]{{X=...}}')
    ids = [p[0] for p in pts]
    xyz = [[p[1], p[2], p[3]] for p in pts]
    print(f'{variant}: {len(pts)} точек из {os.path.basename(ls_path)}')

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

    curve = S.curve(f'линия реза (расчёт, {variant})', xyz, '#3b82f6',
                    closed=True, width=2, editable=True, ids=ids)

    path = S.write(variant, cameras=cam_objs, curves=[curve],
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
    a = ap.parse_args()
    build(a.variant, a.ls,
         {'back': a.cam_back, 'left': a.cam_left, 'top': a.cam_top},
         {'back': a.photo_back, 'left': a.photo_left, 'top': a.photo_top})
