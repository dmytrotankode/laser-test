"""Наочна перевірка калібровки marker_2026-09-30: куди камера «очікує» лазерну точку.

Для кожної з 40 точок пульта (points_pendant.csv) положення точки на шоломі
= сопло + 10.7 мм уздовж осі інструмента (медіана з калібровки) - ПІКСЕЛІ ФОТО ТУТ НЕ
ВИКОРИСТОВУЮТЬСЯ. Проекція через збережену калібровку -> червоний хрестик з номером.
Зелене коло - де точку підписано на фото (pixels.json; ними калібрували).
Хрестик без кола - точка, яку при калібровці не використали: якщо він сидить на
чорній точці на шоломі - калібровка вгадала її «наосліп».
Показуються лише точки з боку, оберненого до камери.

    python show_calib_points.py   ->  out_calib_check/{back,left,top}.jpg (+ _zoom)
"""
import json
import os

import cv2
import numpy as np

import calib_rays as C

BASE = C.BASE
CAM_DIR = os.path.join(BASE, '..', 'service_2021', 'calib', 'cameras', 'marker_2026-09-30')
OUT = os.path.join(BASE, 'out_calib_check')
T_DOT = 10.7

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    px = json.load(open(os.path.join(BASE, 'pixels.json'), encoding='utf-8'))
    noz = [n for n in C.nozzles() if not n['repeat']]
    for v in C.VIEWS:
        z = np.load(os.path.join(CAM_DIR, f'cam_{v}.npy'))
        img = cv2.cvtColor(cv2.imread(os.path.join(BASE, 'photos', f'{v}.png'), 0), cv2.COLOR_GRAY2BGR)
        P = np.array([n['pos'] + T_DOT * n['dir'] / np.linalg.norm(n['dir']) for n in noz])
        uv, depth = C.project(z[:6], z[6], P)
        mm = float(np.median(depth)) / z[6]
        errs = []
        for n, p, q in zip(noz, P, uv):
            facing = (z[3:6] - p) @ (-n['dir']) > 0          # вісь інструмента - назовні з деталі
            if not facing or not (0 <= q[0] < 4096 and 0 <= q[1] < 3000):
                continue
            lab = n['label']
            u, w = int(q[0]), int(q[1])
            if lab in px.get(v, {}):
                a, b = map(int, px[v][lab])
                cv2.circle(img, (a, b), 26, (0, 220, 0), 4)
                errs.append(np.hypot(q[0] - a, q[1] - b) * mm)
            cv2.drawMarker(img, (u, w), (0, 0, 255), cv2.MARKER_CROSS, 40, 4)
            cv2.putText(img, lab, (u + 22, w - 18), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 0, 255), 4)
        e = np.array(errs)
        cv2.putText(img, f'{v}: chervonyi = de kalibrovka chekaie tochku, zelene kolo = de vona na foto; '
                         f'rozbizhnist {e.mean():.2f} mm (maks {e.max():.2f})',
                    (40, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 255, 255), 4)
        cv2.imwrite(os.path.join(OUT, f'{v}.jpg'), cv2.resize(img, (2048, 1500)))
        # збільшена ділянка навколо шолома
        ys, xs = uv[:, 1], uv[:, 0]
        x0, x1 = int(max(0, np.percentile(xs, 2) - 250)), int(min(4096, np.percentile(xs, 98) + 250))
        y0, y1 = int(max(0, np.percentile(ys, 2) - 250)), int(min(3000, np.percentile(ys, 98) + 250))
        crop = img[y0:y1, x0:x1]
        s = 2000 / max(crop.shape[:2])
        cv2.imwrite(os.path.join(OUT, f'{v}_zoom.jpg'), cv2.resize(crop, None, fx=s, fy=s))
        print(f'{v}: точок з підписом {len(e)}, розбіжність середня {e.mean():.2f} мм, макс {e.max():.2f} мм')
