"""Откуда на силуэте угловатые выступы: разбор рендера по стадиям.

Рендер устроен так: рассыпать точки поверхности -> сомкнуть морфологией ->
взять крупнейший внешний контур -> залить. Каждая стадия может дать артефакт,
и по итоговой картинке не видно, какая именно. Здесь они выводятся отдельно.
"""
import os
import sys
import json
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render as R  # noqa: E402
from a3_bestcase import make_cam, COARSE  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(os.path.join(HERE, 'bestcase.json'), encoding='utf-8') as f:
    store = json.load(f)

for view in ('top', 'left'):
    p = np.array(store[view]['p'])
    cam = make_cam(p, COARSE)
    ref, cut = R.load_mask('v1', view, COARSE)

    # стадия 1: сырая россыпь спроецированных точек поверхности
    uv, bad = cam.project(R.SURF)
    w, h = cam.size
    raw = np.zeros((h, w), np.uint8)
    u = np.round(uv[:, 0]).astype(int); v = np.round(uv[:, 1]).astype(int)
    ok = (~bad) & (u >= 0) & (u < w) & (v >= 0) & (v < h)
    raw[v[ok], u[ok]] = 255
    n_off = int((~ok).sum())

    # стадия 2: после смыкания
    closed = cv2.morphologyEx(raw, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

    # стадия 3: заливка крупнейшего внешнего контура
    cnts, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    areas = sorted((cv2.contourArea(c) for c in cnts), reverse=True)
    solid = np.zeros_like(raw)
    if cnts:
        cv2.drawContours(solid, [max(cnts, key=cv2.contourArea)], -1, 255, -1)
    final = solid.copy()
    if cut is not None:
        final[int(cut):, :] = 0

    print(f"--- {view} ---")
    print(f"  точек вне кадра / за камерой: {n_off} из {len(R.SURF)}")
    print(f"  отдельных пятен после смыкания: {len(cnts)}"
          f"   площади: {[int(a) for a in areas[:5]]}")
    print(f"  площадь: россыпь {np.count_nonzero(raw)}, "
          f"сомкнуто {np.count_nonzero(closed)}, залито {np.count_nonzero(solid)}")
    add = np.count_nonzero(solid) - np.count_nonzero(closed)
    print(f"  заливка добавила {add} px "
          f"({add / max(np.count_nonzero(solid), 1) * 100:.0f} % итога)")

    # сколько красного «лишнего» относительно фото и где оно
    extra = cv2.bitwise_and(final, cv2.bitwise_not(ref))
    print(f"  CAD вне фото: {np.count_nonzero(extra)} px")

    panel = np.hstack([
        cv2.cvtColor(raw, cv2.COLOR_GRAY2BGR),
        cv2.cvtColor(closed, cv2.COLOR_GRAY2BGR),
        cv2.cvtColor(solid, cv2.COLOR_GRAY2BGR),
    ])
    for i, name in enumerate(('1 rassyp', '2 somknuto', '3 zalito')):
        cv2.putText(panel, name, (10 + i * w, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    cv2.imwrite(os.path.join(HERE, f'a4_stages_{view}.png'), panel)

print()
print("картинки: a4_stages_top.png, a4_stages_left.png")
