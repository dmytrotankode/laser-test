"""Собрать финальный .LS из поправленных в вьювере точек - без 3030.

Шаблон (template.ls) уже лежит рядом со сценой - его туда положил build_scene.py
при сборке, специально чтобы этот шаг ни от чего не зависел. Правится только
X/Y/Z точек редактируемой кривой, весь остальной текст (скорости, W/P/R,
заголовки) - как в шаблоне.

    python export_final.py v26
"""
import os
import sys
import json
import argparse

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ls_points                                          # noqa: E402
import scene as S                                          # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def export(variant):
    d = os.path.join(S.SCENES, variant)
    scene_path = os.path.join(d, 'scene.json')
    tmpl_path = os.path.join(d, 'template.ls')
    if not os.path.exists(scene_path):
        raise SystemExit(f'нет сцены {variant} - сначала build_scene.py')
    if not os.path.exists(tmpl_path):
        raise SystemExit(f'нет шаблона {tmpl_path} - сцена собрана старой версией build_scene.py?')

    with open(scene_path, encoding='utf-8') as f:
        doc = json.load(f)
    editable = [c for c in doc['curves'] if c.get('editable')]
    if not editable:
        raise SystemExit('в сцене нет редактируемой кривой')
    c = editable[0]

    cut_by_id = {i: tuple(p) for i, p in zip(c['ids'], c['points'])}
    axis_by_id = {i: tuple(a) for i, a in zip(c['ids'], c['axes'])}
    n_touched = sum(1 for t in c.get('touched', []) if t)

    # Ім'я файлу МАЄ співпадати з /PROG всередині - контролер відмовляється
    # завантажувати інакше (та сама вимога, що вже задокументована в
    # pipeline/ls_template.py). Раніше файл звався "<variant>_final.LS", а
    # /PROG - "CORR_...", тобто вони й не могли співпасти; це і був "другий
    # рядком нижче" збій, що йшов одразу після виправлення самого /PROG.
    prog_name = ls_points.fanuc_safe_name(f'CORR_{variant}')
    out_path = os.path.join(d, f'{prog_name}.LS')
    ls_points.write_points(tmpl_path, out_path, cut_by_id, axis_by_id,
                           new_prog_name=prog_name)
    print(f'{variant}: {out_path}')
    print(f'  точек всего {len(cut_by_id)}, тронуто оператором {n_touched}')
    return out_path, len(cut_by_id), n_touched


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('variant')
    export(ap.parse_args().variant)
