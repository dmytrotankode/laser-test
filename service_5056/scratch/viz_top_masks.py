"""Верхний вид: контуры масок архивного шлема и новых, чтобы увидеть край."""
import os
import sys
import numpy as np
import cv2

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
from step03_segment_monochrome import segment_image   # noqa: E402

OUT = os.path.join(BASE, 'results', '_forms_png', 'top_masks.png')
ITEMS = [("arch v1", os.path.join(BASE, 'input', 'archive', 'v1')),
         ("form1_h1", os.path.join(BASE, 'results', '_forms_png', 'form1_h1')),
         ("form1_h3", os.path.join(BASE, 'results', '_forms_png', 'form1_h3')),
         ("form4_h1", os.path.join(BASE, 'results', '_forms_png', 'form4_h1')),
         ("form4_h3", os.path.join(BASE, 'results', '_forms_png', 'form4_h3'))]

tiles = []
for label, d in ITEMS:
    mask, gray, _, _, _ = segment_image(os.path.join(d, 'top.png'), True)
    vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(vis, [max(cnts, key=cv2.contourArea)], -1, (0, 80, 255), 6)
    h, w = vis.shape[:2]
    t = cv2.resize(vis, (520, int(520 * h / w)), interpolation=cv2.INTER_AREA)
    cv2.rectangle(t, (0, 0), (520, 30), (25, 25, 25), -1)
    cv2.putText(t, label, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (90, 220, 255), 2)
    tiles.append(t)

hmin = min(t.shape[0] for t in tiles)
cv2.imwrite(OUT, np.hstack([t[:hmin] for t in tiles]))
print(OUT)
