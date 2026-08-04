"""Решающий замер: отличимы ли формы ПО КУПОЛУ, без верхнего вида.

Виды back/left проходят через отсечку Safe Zone (верхние 58%), то есть содержат
только гладкую часть купола и не видят необрезанный край. Вид top отсечки не
имеет и показывает внешнюю кромку юбки со всей бахромой — на фото form4 она
хорошо заметна. Если различие форм живёт только в top, оно про обрезку, а не
про геометрию купола.
"""
import os
import sys
import json
import numpy as np

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import features   # noqa: E402
import dataset    # noqa: E402

with open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8') as f:
    SCALE_FULL = np.array(json.load(f)["knn_scale"], float)
with open(os.path.join(BASE, 'results', '_forms_features.json'), encoding='utf-8') as f:
    NEW = json.load(f)

LIB = dataset.ALL
F = features.load(LIB)
NAMES = sorted(NEW)

# порядок в векторе prof: 3 вида по 50 чисел (cx, cy, 48 радиусов)
SLICES = {"купол (back+left)": slice(0, 100),
          "только top": slice(100, 150),
          "все три вида": slice(0, 150)}


def decompose(train, target, k):
    mu = train.mean(0)
    _, _, Vt = np.linalg.svd(train - mu, full_matrices=False)
    P = Vt[:k]
    r = target - mu
    return float(np.linalg.norm(r - P.T @ (P @ r)))


K = 6
for label, sl in SLICES.items():
    sc = SCALE_FULL[sl]
    X = np.array([features.vec(F[v], "prof")[sl] / sc for v in LIB])
    Y = {n: features.vec(NEW[n], "prof")[sl] / sc for n in NAMES}

    floor = [decompose(np.delete(X, i, axis=0), X[i], K) for i in range(len(LIB))]
    print("=" * 66)
    print(f"{label}")
    print("=" * 66)
    print(f"шум метода (тот же шлем, LOO по 16 съёмкам): "
          f"среднее {np.mean(floor):.1f}, макс {max(floor):.1f}")
    vals = {}
    for n in NAMES:
        vals[n] = decompose(X, Y[n], K)
        print(f"  {n:<12}{vals[n]:>8.1f}")
    f1 = [vals[n] for n in NAMES if n.startswith("form1")]
    f4 = [vals[n] for n in NAMES if n.startswith("form4")]
    print(f"  form1: {min(f1):.1f}..{max(f1):.1f}   form4: {min(f4):.1f}..{max(f4):.1f}")
    sep = "РАЗДЕЛЯЮТСЯ" if max(f1) < min(f4) or max(f4) < min(f1) else "ПЕРЕКРЫВАЮТСЯ"
    print(f"  -> формы {sep}\n")
