"""Шаг 1a: .raw -> .png для наборов 10.08 + контактный лист для опознания ракурсов.

Ракурс НЕ выводится из порядка файлов. В именах только время съёмки, а прецедент
уже был: в forms/ PNG назывались по индексу камеры, и порядок там другой
(cam_0=left, cam_1=top, cam_2=back). Поэтому здесь файлы раскладываются по
времени в имени как shot1/2/3, а какой из них какой ракурс - решается глазами по
контактному листу и записывается в s1_views.json отдельным шагом.

Ничего не пишется в input/: у этих наборов есть ground truth, и класть их рядом с
обучающими вариантами - ровно тот путь, которым held-out однажды уже протёк.
"""
import os
import re
import sys
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
ROOT = os.path.abspath(os.path.join(BASE, '..'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

NEW_DIR = os.path.join(ROOT, 'Helmet (10.08)')
OUT = os.path.join(BASE, 'results', '_new0810')
W, H = 4096, 3000

dirs = sorted(d for d in os.listdir(NEW_DIR) if os.path.isdir(os.path.join(NEW_DIR, d)))
tiles, labels = [], []

for d in dirs:
    var = d.split()[0]
    raws = sorted(f for f in os.listdir(os.path.join(NEW_DIR, d)) if f.endswith('.raw'))
    assert len(raws) == 3, f'{d}: {len(raws)} raw-файлов'
    vd = os.path.join(OUT, var)
    os.makedirs(vd, exist_ok=True)
    for k, f in enumerate(raws, 1):
        stamp = re.search(r'Image_(\d{14})', f).group(1)
        dst = os.path.join(vd, f'shot{k}.png')
        if not os.path.exists(dst):
            a = np.fromfile(os.path.join(NEW_DIR, d, f), dtype=np.uint8)
            assert a.size == W * H, f'{f}: {a.size} байт, ожидалось {W * H}'
            cv2.imwrite(dst, a.reshape(H, W))
        img = cv2.imread(dst, cv2.IMREAD_GRAYSCALE)
        tiles.append(cv2.resize(img, (410, 300)))
        labels.append(f'{var} shot{k} {stamp[8:10]}:{stamp[10:12]}:{stamp[12:14]}')
        print(f'{var} shot{k}  <- {f}')

rows = []
for i in range(0, len(tiles), 3):
    row = []
    for j in range(3):
        t = cv2.cvtColor(tiles[i + j], cv2.COLOR_GRAY2BGR)
        cv2.putText(t, labels[i + j], (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    (0, 0, 255), 2)
        row.append(t)
    rows.append(np.hstack(row))
sheet = np.vstack(rows)
cv2.imwrite(os.path.join(HERE, 's1_contact.png'), sheet)
print(f'\nконтактный лист: s1_contact.png  ({sheet.shape[1]}x{sheet.shape[0]})')
