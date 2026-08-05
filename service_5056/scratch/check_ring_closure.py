"""Контур реально замкнут или мы замыкаем разомкнутую дугу?

Метрика curve_distance и вся геометрия трактуют контур как ЗАМКНУТОЕ кольцо
(последняя точка соединяется с первой). Если физически оператор ведёт разомкнутую
дугу, то замыкающий отрезок — выдумка, и он даст и ложный «резкий поворот»,
и завышенную ошибку в этом месте.

Проверяем: длина замыкающего шага против типичного шага реза.
"""
import os
import sys
import numpy as np

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import lsgeom     # noqa: E402
import dataset    # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

print(f"{'вар':<5}{'точек':>7}{'шаг мед.':>10}{'шаг мин':>9}{'шаг макс':>10}"
      f"{'ЗАМЫКАЮЩИЙ':>12}{'угол замык.':>13}")
gaps = []
for v in dataset.ALL:
    prog = lsgeom.load(os.path.join(BASE, 'input', 'archive', v, 'ground_truth.ls'))
    P, ids = lsgeom.cut_ring(prog)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)          # шаги внутри дуги
    close = float(np.linalg.norm(P[0] - P[-1]))               # замыкающий отрезок
    c = P.mean(0)
    ang = (np.degrees(np.arctan2(P[-1][1] - c[1], P[-1][0] - c[0])) + 360) % 360
    gaps.append(close / np.median(seg))
    print(f"{v:<5}{len(P):>7}{np.median(seg):>10.2f}{seg.min():>9.2f}{seg.max():>10.2f}"
          f"{close:>12.2f}{ang:>12.0f}°")

g = np.array(gaps)
print(f"\nЗамыкающий отрезок / типичный шаг: {g.min():.1f}..{g.max():.1f}x")
if g.max() > 2.0:
    print("=> контур РАЗОМКНУТ: замыкание искусственное, оно создаёт ложный угол")
    print("   и завышает ошибку в этом месте. Метрика и split_path это не учитывают.")
else:
    print("=> контур замкнут корректно, замыкающий шаг обычного размера")

# где именно сидит резкий поворот относительно концов дуги
prog = lsgeom.load(os.path.join(BASE, 'input', 'archive', 'v1', 'ground_truth.ls'))
P, ids = lsgeom.cut_ring(prog)
d0 = P - np.roll(P, 1, axis=0)
d1 = np.roll(P, -1, axis=0) - P
cs = (d0 * d1).sum(1) / (np.linalg.norm(d0, axis=1) * np.linalg.norm(d1, axis=1))
turn = np.degrees(np.arccos(np.clip(cs, -1, 1)))
k = int(turn.argmax())
print(f"\nv1: самый резкий поворот {turn[k]:.0f}° на позиции {k} из {len(P)} "
      f"(P[{ids[k]}])")
print(f"   позиция 0 и {len(P)-1} — это концы записанной дуги")
print(f"   повороты по убыванию: " +
      ", ".join(f"поз.{i} {turn[i]:.0f}°" for i in np.argsort(-turn)[:5]))
