"""Пункты 20+22 вместе: вернуть v14-v16, нормализовав зазор. ЭКСПЕРИМЕНТ.

Отдельно п.22 ничего не даёт (см. exp_surface_model.py): у всех 11 обучающих
вариантов отступ и так ровный, 9.96-10.70 мм. Убирать нечего. Зазор гуляет только
в v13-v16, и v14/v15/v16 сейчас в PENDING.

Здесь: расширяем обучение до 14 вариантов, метки берём в координатах точки реза
(там v14-v16 сопоставимы с остальными), меряем тем же LOO. Held-out (v6, v13)
не читается — dataset.guard_training.

Две метрики, потому что одна врёт:
  * по поверхности    — чистая ошибка позы, к бухгалтерии зазора нечувствительна;
  * по соплу с d варианта — то же в привычных координатах.
Экспорт с d=10 для v14-v16 бессмысленно сравнивать с их записью: они снимались
при другом отступе, разойдётся на 3-6 мм по построению, и это не ошибка модели.
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
from exp_surface_model import (load, icp, fit_gap, pose_between,   # noqa: E402
                               apply_pose, fit_pairs, NOMINAL_D, ANCHOR)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

KIND, LAM = "prof", 100
BASE_SET = dataset.TRAIN
EXTENDED = dataset.TRAIN + dataset.PENDING
dataset.guard_training(EXTENDED)          # упадёт, если сюда просочится held-out

print(f"База:      {len(BASE_SET)} вариантов")
print(f"Расширено: {len(EXTENDED)} вариантов (+{', '.join(dataset.PENDING)})")
print(f"Held-out {dataset.HELDOUT} не читается.\n")

F = features.load(EXTENDED)
D = {v: load(v) for v in EXTENDED}

Pa, Aa = D[ANCHOR]
ref_surface = Pa - NOMINAL_D * Aa
gap, gap_res = {ANCHOR: NOMINAL_D}, {ANCHOR: 0.0}
print("Подбор отступа d:")
for v in EXTENDED:
    if v == ANCHOR:
        continue
    gap[v], gap_res[v] = fit_gap(*D[v], ref_surface)
for v in EXTENDED:
    mark = "  <- был parked" if v in dataset.PENDING else ""
    print(f"  {v:<5} d = {gap[v]:6.2f} мм   остаток формы {gap_res[v]:.2f} мм{mark}")

SURF = {v: D[v][0] - gap[v] * D[v][1] for v in EXTENDED}
NOZZ = {v: D[v][0] for v in EXTENDED}
pivot = NOZZ[ANCHOR].mean(0)

T = {v: icp(SURF[ANCHOR], SURF[v]) for v in EXTENDED}
POSE = {(a, b): pose_between(T[a], T[b], pivot)
        for a in EXTENDED for b in EXTENDED if a != b}


def loo(names):
    """LOO внутри names. Возвращает ошибку по поверхности и по соплу, на вариант."""
    out = {}
    for v in names:
        tr = [u for u in names if u != v]
        W, sx = fit_pairs(tr, F, KIND, LAM, POSE)
        d = {r: np.linalg.norm(features.vec(F[v], "f8") - features.vec(F[r], "f8"))
             for r in tr}
        ref = min(d, key=d.get)
        p = (features.vec(F[v], KIND) - features.vec(F[ref], KIND)) / sx @ W
        S_pred = apply_pose(SURF[ref], p, pivot)
        N_pred = S_pred + gap[v] * D[ref][1]
        out[v] = (float(lsgeom.curve_distance(S_pred, SURF[v]).mean()),
                  float(lsgeom.curve_distance(N_pred, NOZZ[v]).mean()),
                  ref)
    return out


base = loo(BASE_SET)
ext = loo(EXTENDED)

print("\n" + "=" * 74)
print("LOO: ошибка по поверхности (чистая поза) и по соплу, мм")
print("=" * 74)
print(f"{'вар':<6}{'база: пов.':>12}{'база: сопло':>13}"
      f"{'расш.: пов.':>13}{'расш.: сопло':>14}{'сосед':>8}")
for v in EXTENDED:
    b = base.get(v)
    e = ext[v]
    bs = f"{b[0]:>12.2f}{b[1]:>13.2f}" if b else f"{'—':>12}{'—':>13}"
    print(f"{v:<6}{bs}{e[0]:>13.2f}{e[1]:>14.2f}{e[2]:>8}")


def stat(d, keys):
    s = [d[k][0] for k in keys]
    n = [d[k][1] for k in keys]
    return np.mean(s), np.max(s), np.mean(n), np.max(n)

print()
sm, sw, nm, nw = stat(base, BASE_SET)
print(f"База (11 вар., оценка на них же):      "
      f"поверхность {sm:.2f} / худш {sw:.2f}   сопло {nm:.2f} / худш {nw:.2f}")
sm, sw, nm, nw = stat(ext, BASE_SET)
print(f"Расширенная (14), те же 11 вариантов:  "
      f"поверхность {sm:.2f} / худш {sw:.2f}   сопло {nm:.2f} / худш {nw:.2f}")
sm, sw, nm, nw = stat(ext, EXTENDED)
print(f"Расширенная (14), все 14:              "
      f"поверхность {sm:.2f} / худш {sw:.2f}   сопло {nm:.2f} / худш {nw:.2f}")
print("\nСравнивать честно можно только первые две строки — один и тот же набор")
print("оцениваемых вариантов, разный объём обучения.")
