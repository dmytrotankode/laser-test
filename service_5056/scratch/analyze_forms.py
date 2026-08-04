"""Этап 4b, шаг 2: отличимы ли формы, и что из различий НЕ лечится позой.

Идея замера. У нас есть 16 съёмок одного и того же шлема в разных позах — это
готовый образец того, "как выглядит изменение позы" в пространстве признаков.
Натягиваем на них подпространство (PCA) и раскладываем отклонение нового шлема:

    вдоль подпространства  -> объяснимо позой, наша коррекция это чинит
    поперёк подпространства -> НЕ объяснимо никакой позой = разница формы

Порог доверия берём не с потолка: тем же способом меряем сами архивные варианты
(leave-one-out). Это заведомо один и тот же шлем, поэтому их поперечный остаток —
шум метода. Всё, что заметно выше него, — настоящее различие.
"""
import os
import sys
import json
import numpy as np

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import features   # noqa: E402
import dataset    # noqa: E402

KIND = "prof"

with open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8') as f:
    MODEL = json.load(f)
SCALE = np.array(MODEL["knn_scale"], float)
THRESH = MODEL["out_of_range_threshold"]

with open(os.path.join(BASE, 'results', '_forms_features.json'), encoding='utf-8') as f:
    NEW = json.load(f)

LIB = dataset.ALL
F = features.load(LIB)
X = np.array([features.vec(F[v], KIND) / SCALE for v in LIB])
Y = {n: features.vec(NEW[n], KIND) / SCALE for n in sorted(NEW)}
NAMES = sorted(Y)

print("=" * 78)
print("A. Расстояние до библиотеки (то же пространство, что у out_of_range)")
print("=" * 78)
gaps = [min(np.linalg.norm(X[i] - X[j]) for j in range(len(LIB)) if j != i)
        for i in range(len(LIB))]
print(f"Разрывы до ближайшего соседа ВНУТРИ библиотеки: "
      f"{min(gaps):.1f} .. {max(gaps):.1f}   (порог out_of_range = {THRESH:.1f})")
print(f"\n{'шлем':<12}{'до ближайшего':>15}{'кто ближайший':>16}{'вердикт':>22}")
for n in NAMES:
    d = [np.linalg.norm(Y[n] - X[i]) for i in range(len(LIB))]
    k = int(np.argmin(d))
    verdict = "ВНЕ диапазона" if d[k] > THRESH else "в диапазоне"
    print(f"{n:<12}{d[k]:>15.1f}{LIB[k]:>16}{verdict:>22}")

print()
print("=" * 78)
print("B. Разложение: сколько объясняется позой, сколько остаётся формой")
print("=" * 78)


def decompose(train_rows, target, k):
    mu = train_rows.mean(0)
    U, S, Vt = np.linalg.svd(train_rows - mu, full_matrices=False)
    P = Vt[:k]
    r = target - mu
    par = P.T @ (P @ r)
    return float(np.linalg.norm(par)), float(np.linalg.norm(r - par))


for k in (3, 6, 10):
    print(f"\n--- подпространство позы: {k} компонент ---")
    print(f"{'шлем':<12}{'вдоль (поза)':>14}{'поперёк (форма)':>17}")

    floor = []
    for i, v in enumerate(LIB):
        rest = np.delete(X, i, axis=0)
        _, orth = decompose(rest, X[i], k)
        floor.append(orth)
    print(f"{'— шум метода: тот же шлем, leave-one-out по 16 съёмкам —':<43}")
    print(f"{'архив v1..v16':<12}{'':>14}{np.mean(floor):>10.1f} сред"
          f"  (макс {max(floor):.1f})")
    print(f"{'— новые шлемы —':<43}")
    for n in NAMES:
        par, orth = decompose(X, Y[n], k)
        print(f"{n:<12}{par:>14.1f}{orth:>17.1f}")

K = 6
print()
print("=" * 78)
print(f"C. Общий сдвиг всей новой съёмки (контроль на сессию/ригу), k={K}")
print("=" * 78)
mu = X.mean(0)
U, S, Vt = np.linalg.svd(X - mu, full_matrices=False)
P = Vt[:K]
orth_vec = {}
for n in NAMES:
    r = Y[n] - mu
    orth_vec[n] = r - P.T @ (P @ r)
common = np.mean([orth_vec[n] for n in NAMES], axis=0)
print(f"Общая для всех 6 часть поперечного остатка: {np.linalg.norm(common):.1f}")
print(f"Индивидуальные отклонения от неё:")
for n in NAMES:
    print(f"  {n:<12}{np.linalg.norm(orth_vec[n] - common):>8.1f}")
print("\nЕсли общая часть велика, а индивидуальные малы — это свойство СЪЁМКИ")
print("(сдвинулась рига / другая длина юбки), а не различие шлемов между собой.")

print()
print("=" * 78)
print("D. Внутри формы против между формами (по остатку формы)")
print("=" * 78)
res = {n: orth_vec[n] - common for n in NAMES}
within, between = [], []
for i, a in enumerate(NAMES):
    for b in NAMES[i + 1:]:
        d = float(np.linalg.norm(res[a] - res[b]))
        (within if a.split('_')[0] == b.split('_')[0] else between).append((a, b, d))
for lab, pairs in (("ВНУТРИ одной формы", within), ("МЕЖДУ формами", between)):
    vals = [d for _, _, d in pairs]
    print(f"\n{lab}: среднее {np.mean(vals):.1f}, диапазон {min(vals):.1f}..{max(vals):.1f}")
    for a, b, d in pairs:
        print(f"   {a} — {b}: {d:.1f}")
