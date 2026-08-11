"""Шаг A1: работает ли рендер и похож ли CAD на фотографию ВООБЩЕ.

Ничего не подгоняем. Меш в начале координат, три камеры смотрят с трёх
очевидных сторон. Рендер режется по ТОЙ ЖЕ строке, что и фото (иначе сравнение
нечестное - у CAD и у живого шлема низ разный).

Положение и размер выравниваются грубо, потому что здесь проверяется только
ФОРМА обвода: если она не похожа, дальше идти незачем.
"""
import os
import sys
import time
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render as R  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
SCALE = 0.12

C = R.VERTS.mean(0)
print(f"CAD: {R.NTRI} треугольников, габарит "
      f"{(R.VERTS.max(0) - R.VERTS.min(0)).round(1)} мм")

DIRS = {'back': (0, -1, 0), 'left': (-1, 0, 0), 'top': (0, 0, 1)}
DIST = {'back': 2700.0, 'left': 1700.0, 'top': 2000.0}
FOC = {'back': 21928.0, 'left': 22354.0, 'top': 23410.0}


def outline(mask):
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cnts:
        return None
    c = max(cnts, key=cv2.contourArea)
    if cv2.contourArea(c) < 10:
        return None
    p = c[:, 0, :].astype(float)
    return (p - p.mean(0)) / np.sqrt(cv2.contourArea(c))


def radial(c, nb=180):
    a = np.arctan2(c[:, 1], c[:, 0]); r = np.hypot(c[:, 0], c[:, 1])
    o = np.argsort(a)
    g = np.linspace(-np.pi, np.pi, nb, endpoint=False)
    return np.interp(g, a[o], r[o], period=2 * np.pi)


t0 = time.time()
panels, report = [], []
for view, d in DIRS.items():
    real, cut = R.load_mask('v1', view, SCALE)
    if real is None:
        report.append(f"  {view:5s}: нет кэшированной маски")
        continue
    eye = C + np.array(d, float) * DIST[view]
    Rm = R.look_at(eye, C)
    cam = R.Camera(FOC[view], Rm, -Rm @ eye, scale=SCALE)
    ren = cam.silhouette(cutoff_row=cut)

    a, b = outline(ren), outline(real)
    if a is None:
        report.append(f"  {view:5s}: меш не попал в кадр")
        continue
    ra, rb = radial(a), radial(b)
    err, k = min(((np.abs(np.roll(ra, k) - rb).mean() / rb.mean() * 100), k)
                 for k in range(180))
    report.append(f"  {view:5s}: расхождение обвода {err:5.1f} %   "
                  f"(отсечка на строке {cut})")

    h, w = real.shape
    vis = np.zeros((h, w, 3), np.uint8)
    vis[:, :, 2] = ren
    vis[:, :, 1] = real
    vis[cv2.bitwise_and(ren, real) > 0] = (0, 255, 255)
    cv2.putText(vis, f"{view} RED=CAD GREEN=photo", (8, 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    panels.append(vis)

dt = time.time() - t0
print()
print("Форма силуэта: CAD против настоящей маски v1")
print("(обе нормированы по центру и площади - сравнивается только обвод)")
print()
print("\n".join(report))
print()
print(f"три рендера заняли {dt:.2f} с  ->  один рендер ~{dt/3*1000:.0f} мс")

out = os.path.join(HERE, 'a1_sanity.png')
cv2.imwrite(out, np.hstack(panels))
print(f"картинка: {out}")
