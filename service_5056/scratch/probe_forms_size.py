"""ИНДИКАТИВНЫЙ замер размеров купола: form1 vs form4 vs архивный шлем.

Грубый порог, не пайплайн (rembg тут не зовём) — годится только для СРАВНЕНИЯ
кадров одной съёмки между собой. Меряем верхние 58% силуэта (Safe Zone),
чтобы рваная юбка не влияла.
"""
import os
import numpy as np
import cv2

W, H = 4096, 3000
ROOT = r"C:\Art\Ai projects\Laser2"
VIEWS = ["back", "left", "top"]


def silhouette(img):
    _, m = cv2.threshold(cv2.GaussianBlur(img, (9, 9), 0), 0, 255,
                         cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    if n < 2:
        return None
    k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return (lab == k).astype(np.uint8)


def dome_metrics(m, frac=0.58):
    ys, xs = np.nonzero(m)
    top = ys.min()
    h_full = ys.max() - top
    keep = ys <= top + frac * h_full
    ys, xs = ys[keep], xs[keep]
    return dict(width=xs.max() - xs.min(), height=h_full, area=len(ys))


def measure(get):
    out = {}
    for v in VIEWS:
        m = silhouette(get(v))
        out[v] = dome_metrics(m) if m is not None else None
    return out


def from_raw(d):
    return lambda v: np.fromfile(os.path.join(d, f"{VIEWS.index(v) + 1}.raw"),
                                 dtype=np.uint8).reshape(H, W)


def from_png(d):
    return lambda v: cv2.imread(os.path.join(d, f"{v}.png"), 0)


rows = []
for v in ("v1", "v2", "v3"):
    rows.append((f"arch/{v}", measure(from_png(
        os.path.join(ROOT, "service_5056", "input", "archive", v)))))
for form in ("form1", "form4"):
    for h in ("1", "2", "3"):
        d = os.path.join(ROOT, "forms", form, h)
        if os.path.isdir(d):
            rows.append((f"{form}/{h}", measure(from_raw(d))))

print(f"{'образец':<10} " + "  ".join(f"{v+' Ш':>7}{v+' В':>7}" for v in VIEWS))
for name, m in rows:
    s = "  ".join(f"{m[v]['width']:>7}{m[v]['height']:>7}" if m[v] else f"{'-':>14}"
                  for v in VIEWS)
    print(f"{name:<10} {s}")

print("\nСреднее по группам (ширина купола, px):")
for grp, pref in (("архив v1-v3", "arch/"), ("form1", "form1/"), ("form4", "form4/")):
    sel = [m for n, m in rows if n.startswith(pref)]
    line = "  ".join(f"{v}={np.mean([s[v]['width'] for s in sel]):7.1f}" for v in VIEWS)
    print(f"  {grp:<12} {line}")

print("\nРазброс ВНУТРИ группы (макс-мин ширины, px):")
for grp, pref in (("архив v1-v3", "arch/"), ("form1", "form1/"), ("form4", "form4/")):
    sel = [m for n, m in rows if n.startswith(pref)]
    line = "  ".join(f"{v}={np.ptp([s[v]['width'] for s in sel]):6.1f}" for v in VIEWS)
    print(f"  {grp:<12} {line}")
