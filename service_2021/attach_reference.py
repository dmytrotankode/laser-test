"""Добавить эталонный .LS в УЖЕ собранную сцену, не трогая её правку.

Для случая "сцену уже правили, эталон появился позже". Полная пересборка
(build_scene.py) стёрла бы touched/points - здесь только дописываются две
новые нередактируемые кривые, редактируемая кривая и её история не трогаются.

    python attach_reference.py v26 "путь\к\эталону.LS"
"""
import os
import sys
import json
import argparse

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import build_scene as B                                    # noqa: E402
import scene as S                                            # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def attach(variant, reference_path):
    p = os.path.join(S.SCENES, variant, 'scene.json')
    if not os.path.exists(p):
        raise SystemExit(f'сцены {variant} ещё нет - сначала build_scene.py')
    with open(p, encoding='utf-8') as f:
        doc = json.load(f)

    prefix = 'еталон, лінія різу ('
    doc['curves'] = [c for c in doc['curves'] if not c['name'].startswith(prefix)]
    new_curves = B.reference_curves(reference_path)
    if not new_curves:
        return
    doc['curves'] += [c for c in new_curves
                      if not any(c['name'] == e['name'] for e in doc['curves'])]

    with open(p, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False)
    print(f'{variant}: эталон добавлен, редактируемая кривая не тронута')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('variant')
    ap.add_argument('reference')
    a = ap.parse_args()
    attach(a.variant, a.reference)
