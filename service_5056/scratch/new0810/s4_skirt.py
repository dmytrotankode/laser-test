"""Шаг 1d: юбка или поза?

step03 ставит границу Safe Zone на 58% ВЫСОТЫ СИЛУЭТА, считая от верха купола
вниз, а низ силуэта - это край необрезанного кевлара. Значит длина юбки двигает
границу по куполу: длиннее юбка -> ниже отсечка -> в маску попадает другая часть
детали, и признаки уезжают, хотя шлем стоит там же.

Различаются два случая, и они дают разную подпись:

  шлем поднялся   верх купола уходит ВВЕРХ, высота силуэта та же;
  юбка длиннее    верх купола на месте, низ силуэта уходит ВНИЗ.

Меряется на исходных величинах step03 (до применения отсечки), поэтому вывод не
зависит от самой отсечки.
"""
import os
import sys
import json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
from step03_segment_monochrome import segment_image   # noqa: E402
import dataset                                        # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CACHE = os.path.join(HERE, 's4_skirt.json')
SHOTS = {'v20': {'back': 'shot1', 'left': 'shot2'},
         'v21': {'top': 'shot1', 'left': 'shot2', 'back': 'shot3'},
         'v22': {'left': 'shot1', 'back': 'shot3'},
         'v23': {'left': 'shot1', 'back': 'shot3'},
         'v24': {'left': 'shot2', 'back': 'shot3'},
         'v25': {'left': 'shot2', 'back': 'shot3'}}
VIEWS = ('back', 'left')

data = json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def measure(path):
    _, _, bbox, cutoff, backend = segment_image(path, False)
    assert backend != 'otsu', path
    top = int(bbox[1])
    true_h = (cutoff - top) / 0.58
    return dict(top=top, cutoff=int(cutoff), true_h=float(true_h),
                bottom=float(top + true_h))


for v in dataset.TRAIN + dataset.HELDOUT:
    for view in VIEWS:
        key = f'{v}/{view}'
        if key in data:
            continue
        data[key] = measure(os.path.join(BASE, 'input', 'archive', v, f'{view}.png'))
        print(f'  архив {key}', flush=True)

for v, sh in SHOTS.items():
    for view in VIEWS:
        key = f'{v}/{view}'
        if key in data:
            continue
        data[key] = measure(os.path.join(BASE, 'results', '_new0810', v,
                                         f'{sh[view]}.png'))
        print(f'  новый {key}', flush=True)

json.dump(data, open(CACHE, 'w'), indent=1)

print()
print("ШАГ 1d. Верх купола и низ силуэта, пиксели")
print("=" * 74)
arch = dataset.TRAIN + dataset.HELDOUT
for view in VIEWS:
    t = np.array([data[f'{v}/{view}']['top'] for v in arch])
    b = np.array([data[f'{v}/{view}']['bottom'] for v in arch])
    h = np.array([data[f'{v}/{view}']['true_h'] for v in arch])
    c = np.array([data[f'{v}/{view}']['cutoff'] for v in arch])
    print(f"\n--- {view} ---")
    print(f"{'':<8}{'верх купола':>13}{'низ силуэта':>13}{'высота':>10}"
          f"{'отсечка':>10}")
    print(f"{'архив 16':<8}{t.mean():>9.0f} ±{t.std():<3.0f}{b.mean():>9.0f} ±{b.std():<3.0f}"
          f"{h.mean():>10.0f}{c.mean():>10.0f}")
    for v in SHOTS:
        d = data[f'{v}/{view}']
        print(f"{v:<8}{d['top']:>9.0f} {(d['top'] - t.mean()) / t.std():>+4.1f}"
              f"{d['bottom']:>9.0f} {(d['bottom'] - b.mean()) / b.std():>+4.1f}"
              f"{d['true_h']:>10.0f}{d['cutoff']:>10.0f}"
              f"   низ {d['bottom'] - b.mean():>+6.0f} px, верх {d['top'] - t.mean():>+5.0f} px")
