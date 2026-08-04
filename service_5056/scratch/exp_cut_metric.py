"""Пересчёт под метрику, которая отражает рез: КУДА ПОПАДАЕТ ЛУЧ.

Заказчик 04.08: отступ 10 мм — не требование процесса, а компенсация того, что CAD
и физический шлем не сопоставить; на резе разницы между 10, 8 и 5 мм не заметили.

Геометрия: луч выходит вдоль оси сопла, поэтому сдвиг сопла ВДОЛЬ оси оставляет луч
той же прямой и не двигает точку реза. Значит расстояние между позами сопла — неверная
метрика: она штрафует разницу отступа, которая на рез не влияет. Правильная метрика —
расстояние между линиями реза на поверхности, S = P - d*ось.

Здесь: те же две модели, что в exp_heldout_check.py, но под обеими метриками и
С BASELINE «ничего не делать» — без него любая цифра точности бессмысленна (§2).
Baseline выбирается ТОЛЬКО по TRAIN, как в evaluate.py.
"""
import os
import sys
import numpy as np

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lsgeom     # noqa: E402
import dataset    # noqa: E402
import features   # noqa: E402
from exp_surface_model import (load, icp, fit_gap, pose_between, apply_pose,
                               fit_pairs, NOMINAL_D, ANCHOR, KIND, LAM)   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_SET, EXT_SET, HELD = dataset.TRAIN, dataset.TRAIN + dataset.PENDING, dataset.HELDOUT
dataset.guard_training(EXT_SET)
ALL = EXT_SET + HELD

F = features.load(ALL)
D = {v: load(v) for v in ALL}
Pa, Aa = D[ANCHOR]
gap = {ANCHOR: NOMINAL_D}
for v in ALL:
    if v != ANCHOR:
        gap[v], _ = fit_gap(*D[v], Pa - NOMINAL_D * Aa)
SURF = {v: D[v][0] - gap[v] * D[v][1] for v in ALL}
NOZZ = {v: D[v][0] for v in ALL}
pivot = NOZZ[ANCHOR].mean(0)
T_s = {v: icp(SURF[ANCHOR], SURF[v]) for v in ALL}
T_n = {v: icp(NOZZ[ANCHOR], NOZZ[v]) for v in ALL}


def poses(names, T):
    return {(a, b): pose_between(T[a], T[b], pivot)
            for a in names for b in names if a != b}


def model_pred(train, T, coords, v):
    W, sx = fit_pairs(train, F, KIND, LAM, poses(train, T))
    d = {r: np.linalg.norm(features.vec(F[v], "f8") - features.vec(F[r], "f8"))
         for r in train}
    ref = min(d, key=d.get)
    p = (features.vec(F[v], KIND) - features.vec(F[ref], KIND)) / sx @ W
    if coords == "nozzle":
        N = apply_pose(NOZZ[ref], p, pivot)
        return N, N - gap[ref] * D[ref][1]
    S = apply_pose(SURF[ref], p, pivot)
    return S + NOMINAL_D * D[ref][1], S


def err(pred, target):
    return float(lsgeom.curve_distance(pred, target).mean())


# ---- baseline: гонять одну фиксированную программу, выбранную ТОЛЬКО по TRAIN ----
def pick_baseline(metric):
    """Кандидат из TRAIN, лучший по худшему случаю внутри TRAIN."""
    best, cand = None, None
    for c in BASE_SET:
        worst = max(err(SURF[c] if metric == "surf" else NOZZ[c],
                        SURF[v] if metric == "surf" else NOZZ[v])
                    for v in BASE_SET if v != c)
        if best is None or worst < best:
            best, cand = worst, c
    return cand


print("Подобранный отступ:", ", ".join(f"{v} {gap[v]:.2f}" for v in ALL), "\n")

for metric, label in (("nozz", "СТАРАЯ: расстояние между позами сопла"),
                      ("surf", "НОВАЯ: расстояние между линиями реза на поверхности")):
    tgt = NOZZ if metric == "nozz" else SURF
    bl = pick_baseline(metric)
    print("=" * 76)
    print(f"{label}")
    print("=" * 76)
    print(f"{'':<34}{'v6':>9}{'v13':>9}{'среднее':>11}")

    rows = []
    e = [err(tgt[bl], tgt[v]) for v in HELD]
    rows.append((f"baseline «ничего не делать» ({bl})", e))
    e = [model_pred(BASE_SET, T_n, "nozzle", v)[0 if metric == "nozz" else 1] for v in HELD]
    rows.append(("модель как сейчас (11, сопло)",
                 [err(p, tgt[v]) for p, v in zip(e, HELD)]))
    e = [model_pred(EXT_SET, T_s, "surface", v)[0 if metric == "nozz" else 1] for v in HELD]
    rows.append(("модель новая (14, поверхность)",
                 [err(p, tgt[v]) for p, v in zip(e, HELD)]))

    for name, vals in rows:
        print(f"{name:<34}{vals[0]:>9.2f}{vals[1]:>9.2f}{np.mean(vals):>11.2f}")
    b = np.mean(rows[0][1])
    for name, vals in rows[1:]:
        print(f"{'  выигрыш к baseline':<34}{'':<18}{b / np.mean(vals):>11.2f}x")
    print()
