"""Не меряем ли мы вместо формы длину необрезанной юбки?

Отсечка Safe Zone стоит на 58% высоты силуэта от верхушки. Высота включает юбку,
которая у неразрезанного шлема какая получилась. Значит более длинная юбка опускает
линию отсечки ниже по куполу и меняет профиль — а мы засчитаем это как «другая форма».

Проверка: коррелирует ли поперечный остаток (§B) с высотой силуэта.
"""
import os
import sys
import json
import numpy as np
import cv2

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
from step03_segment_monochrome import segment_image   # noqa: E402
import features   # noqa: E402
import dataset    # noqa: E402

KIND = "prof"
with open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8') as f:
    MODEL = json.load(f)
SCALE = np.array(MODEL["knn_scale"], float)
with open(os.path.join(BASE, 'results', '_forms_features.json'), encoding='utf-8') as f:
    NEW = json.load(f)

STAGE = os.path.join(BASE, 'results', '_forms_png')
ARCH = os.path.join(BASE, 'input', 'archive')


def heights(d):
    """Полная высота силуэта (с юбкой) для двух боковых видов, px."""
    out = {}
    for name in ("back", "left"):
        mask, _, _, cutoff_y, _ = segment_image(os.path.join(d, f"{name}.png"), False)
        ys = np.where(mask > 0)[0]
        top = int(ys.min())
        out[name] = (cutoff_y - top) / 0.58      # обратно из отсечки
    return out


rows = []
for v in dataset.ALL:
    rows.append(("arch:" + v, heights(os.path.join(ARCH, v))))
for n in sorted(NEW):
    rows.append((n, heights(os.path.join(STAGE, n))))

print(f"{'образец':<16}{'высота back':>13}{'высота left':>13}")
for n, h in rows:
    print(f"{n:<16}{h['back']:>13.0f}{h['left']:>13.0f}")

arch = np.array([[h['back'], h['left']] for n, h in rows if n.startswith('arch:')])
new = np.array([[h['back'], h['left']] for n, h in rows if not n.startswith('arch:')])
print(f"\nархив: back {arch[:,0].mean():.0f} (разброс {np.ptp(arch[:,0]):.0f}), "
      f"left {arch[:,1].mean():.0f} (разброс {np.ptp(arch[:,1]):.0f})")
print(f"новые: back {new[:,0].mean():.0f} (разброс {np.ptp(new[:,0]):.0f}), "
      f"left {new[:,1].mean():.0f} (разброс {np.ptp(new[:,1]):.0f})")

# поперечный остаток из §B
LIB = dataset.ALL
F = features.load(LIB)
X = np.array([features.vec(F[v], KIND) / SCALE for v in LIB])
mu = X.mean(0)
_, _, Vt = np.linalg.svd(X - mu, full_matrices=False)
P = Vt[:6]
names = sorted(NEW)
orth, hh = [], []
for n in names:
    r = features.vec(NEW[n], KIND) / SCALE - mu
    orth.append(np.linalg.norm(r - P.T @ (P @ r)))
    h = dict(rows)[n]
    hh.append((h['back'] + h['left']) / 2)
orth, hh = np.array(orth), np.array(hh)
print(f"\n{'шлем':<12}{'высота (сред)':>15}{'остаток формы':>16}")
for n, h, o in zip(names, hh, orth):
    print(f"{n:<12}{h:>15.0f}{o:>16.1f}")
c = np.corrcoef(hh, orth)[0, 1]
print(f"\nкорреляция «высота силуэта» ↔ «остаток формы» по 6 шлемам: r = {c:+.2f}")
print("r близко к +1 => мы меряем длину юбки, а не форму. Замер надо переделывать.")
