"""Потолок подхода: что останется, если предсказание позы станет ИДЕАЛЬНЫМ.

Мы берём контур соседа и двигаем его жёстко. Значит даже при безошибочной модели
останется то, что жёстким движением не выражается: разница формы, шум ручной
подгонки, дефекты кевлара. Эта величина и есть предел.

Считаем "оракула" — подгоняем контур соседа прямо к цели (то есть подсматриваем
ответ). Хуже оракула модель быть может, лучше — никогда.

Три уровня свободы, чтобы понять, куда есть смысл двигаться:
  6-DOF          жёсткое движение, как сейчас
  +масштаб       ещё один параметр: шлем чуть больше/меньше
  +лучший сосед  оракул выбирает соседа задним числом, а не k-NN

Ключевая колонка — МАКСИМУМ, а не среднее: допуск на рез поточечный.
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

anchor = lsgeom.load(os.path.join(BASE, 'input', 'archive', 'v1', 'ground_truth.ls'))
REF, _ = lsgeom.cut_surface(anchor, lsgeom.NOMINAL_STANDOFF)


def cutline(path):
    p = lsgeom.load(path)
    so, _ = lsgeom.fit_standoff(p, REF)
    return lsgeom.cut_surface(p, so)[0]


def fit_rigid(A, B, scale=False, iters=60, n=1200):
    """Лучшее преобразование A -> B без соответствий; опционально с масштабом."""
    Bd = lsgeom.resample_closed(np.asarray(B, float), n)
    A = np.asarray(A, float)
    X = A.copy()
    for _ in range(iters):
        j = np.linalg.norm(X[:, None, :] - Bd[None, :, :], axis=2).argmin(1)
        T = Bd[j]
        ca, cb = A.mean(0), T.mean(0)
        P, Q = A - ca, T - cb
        U, S, Vt = np.linalg.svd(P.T @ Q)
        D = np.diag([1.0, 1.0, np.sign(np.linalg.det(Vt.T @ U.T))])
        R = Vt.T @ D @ U.T
        s = float((S * np.diag(D)).sum() / (P * P).sum()) if scale else 1.0
        X = s * (A @ R.T) + (cb - s * (R @ ca))
    return X


LIB = {v: cutline(os.path.join(BASE, 'input', 'archive', v, 'ground_truth.ls'))
       for v in dataset.ALL}
TESTS = {v: LIB[v] for v in dataset.HELDOUT}
TESTS['05.08 цех'] = cutline(os.path.join(BASE, '..', '05082026_test1',
                                          'TOR_XL_LEARN_V6_2.LS'))

print(f"{'случай':<12}{'режим':<26}{'среднее':>9}{'p90':>8}{'МАКСИМУМ':>11}{'<=1.5мм':>10}")
print("=" * 76)
for name, G in TESTS.items():
    pool = [v for v in dataset.TRAIN if not np.array_equal(LIB[v], G)]
    rows = []
    for label, scale, best in (("6-DOF, сосед k-NN-класса", False, False),
                               ("6-DOF, лучший сосед", False, True),
                               ("+ масштаб, лучший сосед", True, True)):
        cands = pool if best else pool
        res = []
        for c in cands:
            X = fit_rigid(LIB[c], G, scale=scale)
            e = lsgeom.curve_distance(X, G)
            res.append((float(e.mean()), float(np.percentile(e, 90)),
                        float(e.max()), float((e <= 1.5).mean())))
        pick = min(res, key=lambda r: r[0]) if best else \
            res[int(np.argmin([r[0] for r in res]))]
        rows.append((label, pick))
    for label, (m, p9, mx, frac) in rows:
        print(f"{name:<12}{label:<26}{m:>9.2f}{p9:>8.2f}{mx:>11.2f}{100*frac:>9.0f}%")
    print("-" * 76)

print()
print("Читать так: строка «+ масштаб, лучший сосед» — абсолютный потолок подхода")
print("«взять чужой контур и подвинуть». Если её МАКСИМУМ выше 1.5 мм, то цель")
print("1-1.5 мм поточечно этим путём недостижима, сколько модель ни улучшай.")
