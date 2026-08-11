"""Шаг 2: разложить наборы 10.08 по местам, как лежат все прежние съёмки.

Две площадки, как в PLAN 1a:

  archive/vNN/            сырьё как пришло: .raw, .LS, .tp + converted/ с полными
                          PNG и превью. Не в git (папка в .gitignore);
  service_5056/input/archive/vNN/   рабочий вход: back/left/top.png + ground_truth.ls.

Имя ракурса в converted/ ставится по ОПОЗНАННОМУ виду, а не по порядку файла:
порядок съёмки в этих наборах разный (v20 back-left-top, v22/v23 left-top-back,
остальные top-left-back), и в самом архиве он тоже не постоянен - v13 и v15 лежат
как top-left-back.

Файлы только копируются. Ни dataset.py, ни model_pose.json, ни библиотека не
трогаются: эти шесть должны остаться независимыми.

В конце - самопроверка: признаки, посчитанные из разложенных файлов, обязаны
совпасть с посчитанными раньше прямо из shotN.png. Если ракурсы при копировании
перепутались, цифры разойдутся.
"""
import os
import re
import sys
import json
import shutil
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
ROOT = os.path.abspath(os.path.join(BASE, '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SRC = os.path.join(ROOT, 'Helmet (10.08)')
ARCH = os.path.join(ROOT, 'archive')
INP = os.path.join(BASE, 'input', 'archive')
PNG = os.path.join(BASE, 'results', '_new0810')

VIEWS_OF = {
    'v20': {'back': 'shot1', 'left': 'shot2', 'top': 'shot3'},
    'v21': {'top': 'shot1', 'left': 'shot2', 'back': 'shot3'},
    'v22': {'left': 'shot1', 'top': 'shot2', 'back': 'shot3'},
    'v23': {'left': 'shot1', 'top': 'shot2', 'back': 'shot3'},
    'v24': {'top': 'shot1', 'left': 'shot2', 'back': 'shot3'},
    'v25': {'top': 'shot1', 'left': 'shot2', 'back': 'shot3'},
}
SRCDIR = {'v20': 'v20 form_1', 'v21': 'v21 form_1', 'v22': 'v22 form_4',
          'v23': 'v23 form_4', 'v24': 'v24 form_1', 'v25': 'v25 form_1'}

for var, sub in SRCDIR.items():
    s = os.path.join(SRC, sub)
    raws = sorted(f for f in os.listdir(s) if f.endswith('.raw'))
    shot_of = {f'shot{k}': f for k, f in enumerate(raws, 1)}
    view_of = {shot: view for view, shot in VIEWS_OF[var].items()}

    ad = os.path.join(ARCH, var)
    cd = os.path.join(ad, 'converted')
    os.makedirs(cd, exist_ok=True)
    for f in os.listdir(s):
        dst = os.path.join(ad, f)
        if not os.path.exists(dst):
            shutil.copy2(os.path.join(s, f), dst)

    for k in (1, 2, 3):
        shot, view = f'shot{k}', view_of[f'shot{k}']
        orig = shot_of[shot]
        full = os.path.join(cd, f'frame{k}_{view}_{orig[:-4]}.png')
        thumb = os.path.join(cd, f'frame{k}_{view}_thumb.png')
        img = cv2.imread(os.path.join(PNG, var, f'{shot}.png'), cv2.IMREAD_GRAYSCALE)
        if not os.path.exists(full):
            cv2.imwrite(full, img)
        if not os.path.exists(thumb):
            cv2.imwrite(thumb, cv2.resize(img, (512, 375)))

    idir = os.path.join(INP, var)
    os.makedirs(idir, exist_ok=True)
    for view, shot in VIEWS_OF[var].items():
        dst = os.path.join(idir, f'{view}.png')
        if not os.path.exists(dst):
            shutil.copy2(os.path.join(PNG, var, f'{shot}.png'), dst)
    ls = [f for f in os.listdir(s) if f.upper().endswith('.LS')]
    assert len(ls) == 1, f'{var}: {ls}'
    gt = os.path.join(idir, 'ground_truth.ls')
    if not os.path.exists(gt):
        shutil.copy2(os.path.join(s, ls[0]), gt)
    print(f'{var}: archive/{var}/ + input/archive/{var}/  <- {ls[0]}')

print()
print("Самопроверка: ракурсы после раскладки совпадают с опознанными")
print("-" * 70)
from step03_segment_monochrome import segment_image     # noqa: E402
from step04_fit_3d_pose import build_feature_vector     # noqa: E402

ref = {k: np.array(v) for k, v in
       json.load(open(os.path.join(HERE, 's2_features.json'))).items()}
ok = True
for var in VIEWS_OF:
    masks = {}
    for view in ('back', 'left', 'top'):
        m, _, _, _, b = segment_image(os.path.join(INP, var, f'{view}.png'),
                                      view == 'top')
        assert b != 'otsu', f'{var}/{view}: Otsu'
        masks[view] = m
    d = float(np.abs(build_feature_vector(masks, 'prof') - ref[var]).max())
    ok &= d < 1e-9
    print(f"  {var}: наибольшее расхождение признака {d:.2e}"
          f"{'  OK' if d < 1e-9 else '  РАСХОЖДЕНИЕ'}")
print("\nвсе совпали" if ok else "\nПРОВЕРКА НЕ ПРОШЛА")
