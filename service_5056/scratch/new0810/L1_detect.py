"""Лазерная проба, шаг 1: найти пятно на каждом кадре.

Первая версия этого скрипта ошиблась на 8 кадрах из 15, и ошибка была
поучительной: я отбирал кандидатов по "компактности", считая пятно мелким. По
вырезкам оказалось наоборот - настоящее пятно КРУПНОЕ (1400-3500 px, резкий
насыщенный овал), а мелкие яркие кляксы в 30-100 px это блики на плетении
кевлара. Правило отбора было перевёрнутым.

Что различает пятно и блик на самом деле:

  * НАСЫЩЕННОЕ ЯДРО. Пятно засвечивает сенсор до упора: внутри него есть
    сплошная область из пикселей максимального уровня. Блик на матовом кевларе
    рассеянный, до упора доходит редко и точечно;
  * РАЗМЕР ЯДРА. У пятна оно сотни-тысячи пикселей, у блика - единицы;
  * РЕЗКОСТЬ ГРАНИЦЫ. Яркость пятна падает от максимума до фона на десятке
    пикселей; блик спадает плавно.

Решение всё равно подтверждается глазами по вырезкам - в этом проекте
правдоподобные числа уже дважды приводили к неверным выводам.
"""
import os
import sys
import json
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
ROOT = os.path.abspath(os.path.join(BASE, '..'))
DATA = os.path.join(ROOT, 'laserdot_1')
OUT = os.path.join(HERE, 'L1_out')
os.makedirs(OUT, exist_ok=True)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

W, H = 4096, 3000
SAT = 250              # что считаем "до упора"
MIN_CORE = 60          # ядро мельче этого - блик на плетении
MAX_CORE = 20000
TOP_N = 4


def load(path):
    return np.fromfile(path, dtype=np.uint8).reshape(H, W)


def candidates(img):
    core = (img >= SAT).astype(np.uint8)
    core = cv2.morphologyEx(core, cv2.MORPH_CLOSE,
                            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    n, lab, stats, cent = cv2.connectedComponentsWithStats(core, 8)
    out = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if not (MIN_CORE <= area <= MAX_CORE):
            continue
        if max(w, h) > 6 * max(min(w, h), 1):
            continue
        cx, cy = cent[i]
        r = int(max(w, h))
        x0, x1 = max(int(cx) - 3 * r, 0), min(int(cx) + 3 * r, W)
        y0, y1 = max(int(cy) - 3 * r, 0), min(int(cy) + 3 * r, H)
        patch = img[y0:y1, x0:x1].astype(float)
        m = (lab[y0:y1, x0:x1] == i)
        if m.sum() < 10 or (~m).sum() < 50:
            continue
        # резкость: перепад между ядром и фоном вокруг, отнесённый к ширине спада
        far = patch[~m]
        drop = float(patch[m].mean() - np.median(far))
        halo = float(((patch >= np.median(far) + drop * 0.5) & (~m)).sum())
        sharp = drop / (1.0 + halo / max(area, 1))
        out.append(dict(x=float(cx), y=float(cy), core=int(area), w=int(w), h=int(h),
                        drop=drop, sharp=float(sharp), score=float(sharp * np.log(area))))
    out.sort(key=lambda d: -d['score'])
    return out[:TOP_N]


files = sorted([f for f in os.listdir(DATA) if f.endswith('.raw')],
               key=lambda s: (int(s[3:s.index('_')]), s))
res, tiles = {}, []
print(f"{'кадр':<16}{'канд.':>6}{'ядро px':>9}{'перепад':>9}{'резкость':>10}"
      f"{'центр (x, y)':>20}")
print("-" * 72)
for f in files:
    img = load(os.path.join(DATA, f))
    cs = candidates(img)
    res[f[:-4]] = cs
    b = cs[0] if cs else None
    print(f"{f[:-4]:<16}{len(cs):>6}"
          + (f"{b['core']:>9}{b['drop']:>9.0f}{b['sharp']:>10.1f}"
             f"{b['x']:>13.0f},{b['y']:>6.0f}" if b else f"{'—':>48}"))

    vis = cv2.cvtColor(cv2.resize(img, (1024, 750)), cv2.COLOR_GRAY2BGR)
    for k, c in enumerate(cs):
        p = (int(c['x'] / 4), int(c['y'] / 4))
        col = (0, 0, 255) if k == 0 else (0, 200, 255)
        cv2.circle(vis, p, 20, col, 2)
        cv2.putText(vis, str(k + 1), (p[0] + 22, p[1] - 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, col, 2)
    cv2.putText(vis, f[:-4], (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    tiles.append(vis)
    if b:
        cx, cy, s = int(b['x']), int(b['y']), 150
        crop = img[max(cy - s, 0):cy + s, max(cx - s, 0):cx + s]
        cv2.imwrite(os.path.join(OUT, f'crop_{f[:-4]}.png'),
                    cv2.resize(crop, (240, 240), interpolation=cv2.INTER_NEAREST))

json.dump(res, open(os.path.join(HERE, 'L1_candidates.json'), 'w'), indent=1)
while len(tiles) % 4:
    tiles.append(np.zeros_like(tiles[0]))
sheet = np.vstack([np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles), 4)])
cv2.imwrite(os.path.join(HERE, 'L1_marked.png'), cv2.resize(sheet, None, fx=0.5, fy=0.5))
print("\nразметка: L1_marked.png   вырезки: L1_out/crop_*.png")
