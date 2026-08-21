"""Добавить в уже существующую сцену 2020 нашу сгенерированную .LS как кривую.

Не трогает камеры/положение модели/фото - дописывает третью кривую поверх
уже собранной сцены (`export_scene.py`), читая её же traiettoria прямо из
сгенерированного .LS (тот же путь, который получит станок).

    python add_generated_curve.py v21 out/DISTI_CADC_V21.LS
"""
import os
import sys
import json
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
S5056 = os.path.abspath(os.path.join(BASE, '..', 'service_5056'))
S2020 = os.path.abspath(os.path.join(BASE, '..', 'service_2020'))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(S5056, 'scripts'))

import lsgeom                                            # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def main(variant, ls_path, label=None, color='#ef4444'):
    scene_path = os.path.join(S2020, 'data', 'scenes', variant, 'scene.json')
    if not os.path.exists(scene_path):
        raise SystemExit(f'сцены {variant} ещё нет - сначала python export_scene.py {variant}')

    prog = lsgeom.load(ls_path)
    pts, _ = lsgeom.cut_surface(prog, lsgeom.NOMINAL_STANDOFF)
    pts = np.asarray(pts, float)

    with open(scene_path, encoding='utf-8') as f:
        doc = json.load(f)

    name = label or f'сгенерировано: {os.path.basename(ls_path)}'
    doc['curves'] = [c for c in doc['curves'] if c['name'] != name] + [{
        'name': name,
        'points': pts.tolist(),
        'color': color,
        'closed': True,
        'width': 3,
    }]

    with open(scene_path, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False)
    print(f'{variant}: добавлена кривая "{name}" ({len(pts)} точек) в {scene_path}')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        raise SystemExit('использование: python add_generated_curve.py <вариант> <путь.LS> [метка]')
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
