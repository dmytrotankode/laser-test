"""Проверка на held-out (v6, v13). ОДИН прогон, после того как выбор сделан по LOO.

Выбор «расширить библиотеку до 14 и учить по точке реза» сделан в exp_extend_library.py
исключительно по LOO внутри TRAIN. Здесь held-out читается первый и единственный раз,
чтобы получить честную цифру. Ничего после этого замера не подбирается — иначе
held-out перестанет быть held-out.

Сравниваются два обучения при полностью одинаковом протоколе (признаки, лямбда,
ближайший сосед, метрика точка->кривая):

    как сейчас  — 11 вариантов, метки и экспорт в координатах сопла
    новое       — 14 вариантов (+v14-v16), метки и экспорт через точку реза

Три колонки ошибки:
    поверхность   — чистая ошибка позы, к зазору нечувствительна
    сопло, d=10   — то, что реально уедет на станок: зазора нового шлема мы не знаем
    сопло, d свой — диагностика; использует зазор held-out варианта, то есть
                    подсматривает, и годится только для разбора, не для отчёта
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

BASE_SET = dataset.TRAIN
EXT_SET = dataset.TRAIN + dataset.PENDING
HELD = dataset.HELDOUT
dataset.guard_training(BASE_SET)
dataset.guard_training(EXT_SET)

ALL = EXT_SET + HELD
F = features.load(ALL)
D = {v: load(v) for v in ALL}

Pa, Aa = D[ANCHOR]
ref_surface = Pa - NOMINAL_D * Aa
gap = {ANCHOR: NOMINAL_D}
for v in ALL:
    if v != ANCHOR:
        gap[v], _ = fit_gap(*D[v], ref_surface)

SURF = {v: D[v][0] - gap[v] * D[v][1] for v in ALL}
NOZZ = {v: D[v][0] for v in ALL}
pivot = NOZZ[ANCHOR].mean(0)

T_s = {v: icp(SURF[ANCHOR], SURF[v]) for v in ALL}
T_n = {v: icp(NOZZ[ANCHOR], NOZZ[v]) for v in ALL}


def poses(names, T):
    return {(a, b): pose_between(T[a], T[b], pivot)
            for a in names for b in names if a != b}


def evaluate(train, T, coords):
    """Обучить на train, оценить каждый held-out. coords: 'nozzle' | 'surface'."""
    W, sx = fit_pairs(train, F, KIND, LAM, poses(train, T))
    out = {}
    for v in HELD:
        d = {r: np.linalg.norm(features.vec(F[v], "f8") - features.vec(F[r], "f8"))
             for r in train}
        ref = min(d, key=d.get)
        p = (features.vec(F[v], KIND) - features.vec(F[ref], KIND)) / sx @ W
        if coords == "nozzle":
            N10 = Nown = apply_pose(NOZZ[ref], p, pivot)
            S = N10 - NOMINAL_D * D[ref][1]
        else:
            S = apply_pose(SURF[ref], p, pivot)
            N10 = S + NOMINAL_D * D[ref][1]
            Nown = S + gap[v] * D[ref][1]
        out[v] = (float(lsgeom.curve_distance(S, SURF[v]).mean()),
                  float(lsgeom.curve_distance(N10, NOZZ[v]).mean()),
                  float(lsgeom.curve_distance(Nown, NOZZ[v]).mean()),
                  ref)
    return out


print(f"Подобранный зазор held-out: " +
      ", ".join(f"{v} = {gap[v]:.2f} мм" for v in HELD))
print(f"(для справки, обучающие: {min(gap[v] for v in BASE_SET):.2f}"
      f"..{max(gap[v] for v in BASE_SET):.2f}; возвращённые: "
      + ", ".join(f"{v} {gap[v]:.2f}" for v in dataset.PENDING) + ")\n")

cur = evaluate(BASE_SET, T_n, "nozzle")
new = evaluate(EXT_SET, T_s, "surface")

print("=" * 78)
print("HELD-OUT, ошибка точка->кривая, мм")
print("=" * 78)
print(f"{'':<22}{'поверхность':>13}{'сопло d=10':>13}{'сопло d свой':>15}{'сосед':>8}")
for v in HELD:
    print(f"-- {v} --")
    for label, res in (("как сейчас (11, сопло)", cur), ("новое (14, поверхность)", new)):
        s, n10, nown, ref = res[v]
        print(f"  {label:<20}{s:>13.2f}{n10:>13.2f}{nown:>15.2f}{ref:>8}")

print()
for col, idx in (("поверхность", 0), ("сопло d=10", 1), ("сопло d свой", 2)):
    a = np.mean([cur[v][idx] for v in HELD])
    b = np.mean([new[v][idx] for v in HELD])
    print(f"{col:<14} как сейчас {a:5.2f}  ->  новое {b:5.2f}   ({b - a:+.2f} мм)")

print("\nКолонка «сопло d свой» подсматривает зазор held-out варианта и приведена")
print("только для разбора. Отчётная цифра — «сопло d=10».")
