"""Разобрать incoming/ и собрать сцены для новых папок - сам, без ручного вызова.

Ожидаемые файлы в incoming/<имя>/ (фиксированные имена, специально просто):
    trajectory.LS      - наш расчёт (обязателен)
    reference.LS        - эталон, если есть (необязателен)
    cam_back.npy, cam_left.npy, cam_top.npy   - камеры (сколько есть)
    back.jpg|png, left.jpg|png, top.jpg|png   - фото (сколько есть)

НЕ трогает уже собранные сцены - если data/scenes/<имя>/scene.json уже есть,
папку пропускает. Иначе правка, которая там уже идёт, стёрлась бы при каждом
обновлении страницы. Пересобрать заново - отдельное, явное действие
(build_scene.py руками), не автоматическое.
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import build_scene as B                                    # noqa: E402
import scene as S                                            # noqa: E402

INCOMING = os.path.join(BASE, 'incoming')


def find_one(d, stem):
    for ext in ('.jpg', '.jpeg', '.png'):
        p = os.path.join(d, stem + ext)
        if os.path.exists(p):
            return p
    return None


def scan_and_build():
    if not os.path.isdir(INCOMING):
        return []
    built = []
    for name in sorted(os.listdir(INCOMING)):
        d = os.path.join(INCOMING, name)
        if not os.path.isdir(d):
            continue
        scene_path = os.path.join(S.SCENES, name, 'scene.json')
        if os.path.exists(scene_path):
            continue                        # уже собрана - не трогаем правки
        ls_path = os.path.join(d, 'trajectory.LS')
        if not os.path.exists(ls_path):
            continue                        # папка неполная, ждём файл
        cams = {v: os.path.join(d, f'cam_{v}.npy') for v in ('back', 'left', 'top')}
        cams = {v: p for v, p in cams.items() if os.path.exists(p)}
        photos = {v: find_one(d, v) for v in ('back', 'left', 'top')}
        ref = os.path.join(d, 'reference.LS')
        ref = ref if os.path.exists(ref) else None
        print(f'discover: новая папка {name}, собираю сцену')
        B.build(name, ls_path, cams, photos, reference_path=ref)
        built.append(name)
    return built


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    names = scan_and_build()
    print(f'собрано новых сцен: {len(names)}' + (f' ({", ".join(names)})' if names else ''))
