"""Шаг A2: похож ли обвод CAD на фотографию, если снять посадку.

В A1 форма и посадка были перепутаны: рендер режется по строке фотографии, а
сколько от него отрежется - зависит от того, где он стоит. Здесь сначала
подгоняются сдвиг и размер (3 числа, перебором), и только потом накладывается
отсечка. Что останется - это уже расхождение самой формы.

Порог для решения: маски одного и того же шлема сходятся почти идеально
(IoU ~0.99), поэтому контроль здесь - соседний вариант из библиотеки. Если CAD
хуже соседа, значит форма CAD и есть узкое место.
"""
import os
import sys
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render as R  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
SCALE = 0.12
C = R.VERTS.mean(0)
DIRS = {'back': (0, -1, 0), 'left': (-1, 0, 0), 'top': (0, 0, 1)}
DIST = {'back': 2700.0, 'left': 1700.0, 'top': 2000.0}
FOC = {'back': 21928.0, 'left': 22354.0, 'top': 23410.0}


def warp(mask, dx, dy, s):
    h, w = mask.shape
    M = np.array([[s, 0, dx + (1 - s) * w / 2],
                  [0, s, dy + (1 - s) * h / 2]], float)
    return cv2.warpAffine(mask, M, (w, h), flags=cv2.INTER_NEAREST)


def best_iou(src, ref, cut, coarse=True):
    """Лучший IoU по сдвигу и масштабу; отсечка применяется ПОСЛЕ подгонки."""
    best = (0.0, None)
    rng_s = np.arange(0.75, 1.35, 0.05) if coarse else np.arange(0.90, 1.11, 0.01)
    for s in rng_s:
        for dy in range(-90, 91, 6):
            for dx in range(-90, 91, 6):
                m = warp(src, dx, dy, s)
                if cut is not None:
                    m = m.copy(); m[int(cut):, :] = 0
                inter = np.count_nonzero(m & ref)
                if inter == 0:
                    continue
                union = np.count_nonzero(m | ref)
                v = inter / union
                if v > best[0]:
                    best = (v, (dx, dy, round(float(s), 3)))
    return best


def contour_gap(a, b):
    """Среднее расстояние от контура a до контура b, в пикселях."""
    ca, _ = cv2.findContours(a, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not ca:
        return float('nan')
    pts = max(ca, key=cv2.contourArea)[:, 0, :]
    dt = cv2.distanceTransform(255 - b, cv2.DIST_L2, 3)
    inside = cv2.distanceTransform(b, cv2.DIST_L2, 3)
    d = np.where(b[pts[:, 1], pts[:, 0]] > 0,
                 inside[pts[:, 1], pts[:, 0]], dt[pts[:, 1], pts[:, 0]])
    return float(np.abs(d).mean())


print("Подгоняются сдвиг и масштаб, отсечка - после. Эталон: маска v1.")
print()
print(f"{'вид':<6}{'источник':<16}{'IoU':>7}{'зазор контура, px':>20}")
print("-" * 50)

for view, d in DIRS.items():
    ref, cut = R.load_mask('v1', view, SCALE)
    if ref is None:
        continue

    eye = C + np.array(d, float) * DIST[view]
    Rm = R.look_at(eye, C)
    cam = R.Camera(FOC[view], Rm, -Rm @ eye, scale=SCALE)
    cad = cam.silhouette()                       # без отсечки, режем после подгонки

    iou, par = best_iou(cad, ref, cut)
    m = warp(cad, *par); m[int(cut):, :] = 0 if cut else None
    if cut is not None:
        m[int(cut):, :] = 0
    print(f"{view:<6}{'CAD':<16}{iou:>7.3f}{contour_gap(m, ref):>20.1f}")

    # контроль: другой вариант того же шлема, та же процедура
    for other in ('v2', 'v9'):
        om, _ = R.load_mask(other, view, SCALE)
        if om is None:
            continue
        iou2, par2 = best_iou(om, ref, cut)
        m2 = warp(om, *par2)
        if cut is not None:
            m2[int(cut):, :] = 0
        print(f"{'':<6}{'фото ' + other:<16}{iou2:>7.3f}{contour_gap(m2, ref):>20.1f}")
    print("-" * 50)
