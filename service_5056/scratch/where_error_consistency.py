"""Зона повышенной ошибки — систематика или совпадение?

Проверка в лоб: у скольких из 16 вариантов ошибка в подозрительной дуге выше,
чем их собственная средняя. Если у 8 из 16 — это монетка. Если у 14-16 — систематика.
"""
import os
import sys
import numpy as np

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import dataset   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

raw = np.load(os.path.join(BASE, 'results', '_where_error.npy'), allow_pickle=True).item()
ALL = dataset.TRAIN + dataset.HELDOUT

ARCS = {"315-45 (конец +X)": (315, 45),
        "45-135": (45, 135),
        "135-225 (конец -X, кромка ниже всего)": (135, 225),
        "225-315": (225, 315)}


def in_arc(a, lo, hi):
    return (a >= lo) & (a < hi) if lo < hi else (a >= lo) | (a < hi)


print(f"{'дуга':<40}{'сред. в дуге':>14}{'к общей':>9}{'выше своей средней':>21}")
for name, (lo, hi) in ARCS.items():
    ratios, higher, vals = [], 0, []
    for v in ALL:
        r = raw[v]
        m = in_arc(r['ang'], lo, hi)
        if not m.any():
            continue
        a, o = r['err'][m].mean(), r['err'].mean()
        vals.append(a)
        ratios.append(a / o)
        higher += int(a > o)
    print(f"{name:<40}{np.mean(vals):>14.2f}{np.mean(ratios):>9.2f}x"
          f"{higher:>15} из {len(ALL)}")

print()
lo, hi = ARCS["315-45 (конец +X)"]
print("По вариантам для дуги 315-45°:")
print(f"{'вар':<6}{'в дуге':>9}{'вне дуги':>10}{'отношение':>11}")
worse = 0
for v in ALL:
    r = raw[v]
    m = in_arc(r['ang'], lo, hi)
    a, b = r['err'][m].mean(), r['err'][~m].mean()
    worse += int(a > b)
    mark = "  <-- held-out" if v in dataset.HELDOUT else ""
    print(f"{v:<6}{a:>9.2f}{b:>10.2f}{a/b:>11.2f}x{mark}")
print(f"\nхуже в дуге, чем вне её: {worse} из {len(ALL)} вариантов")
print("8 из 16 = совпадение. 14+ = систематика.")
