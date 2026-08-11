"""Шаг 5: потолок на шести слепых наборах.

Вопрос, который разделяет два совершенно разных диагноза:

  поза определена неверно      -> оракул (подгонка с подсматриванием ответа) даст
                                  мало, и чинить надо признаки;
  чужой контур не ложится      -> оракул даст много, и тогда перенос контура с
  на другой экземпляр             одного шлема на другой не работает в принципе.

Три режима, чтобы разделить ещё и вклад выбора соседа:

  фактический сосед   тот, кого выбрал k-NN. Идеальная поза при нынешнем выборе;
  лучший сосед        оракул выбирает опору задним числом;
  + масштаб           седьмой параметр: шлем чуть крупнее или мельче.

Контроль - v13 и цеховая съёмка 05.08: их потолок уже измерен (максимум 1.40 и
2.51 мм, PLAN 3). Если здесь получится то же, измеритель считает то, что нужно.
"""
import os
import sys
import json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
ROOT = os.path.abspath(os.path.join(BASE, '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
sys.path.insert(0, os.path.join(BASE, 'scratch'))
import lsgeom      # noqa: E402
import evaluate    # noqa: E402
import dataset     # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def fit_rigid(A, B, scale=False, iters=60, n=1200):
    """Лучшее преобразование A -> B без соответствий (копия ceiling.fit_rigid)."""
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


def score(X, G):
    e = lsgeom.curve_distance(X, G)
    return (float(e.mean()), float(np.percentile(e, 90)), float(e.max()),
            float((e <= 2.0).mean() * 100))


RES = json.load(open(os.path.join(HERE, 's7_results.json')))
LIB = {v: evaluate.gt_contour(v) for v in dataset.TRAIN}

CASES = {v: (evaluate.gt_contour(v), RES[v]['nb']) for v in
         ('v20', 'v21', 'v22', 'v23', 'v24', 'v25')}
CASES['v13 (контр.)'] = (evaluate.gt_contour('v13'), 'v5')
shop = lsgeom.load(os.path.join(ROOT, '05082026_test1', 'TOR_XL_LEARN_V6_2.LS'))
so, _ = lsgeom.fit_standoff(shop, evaluate.gt_contour('v1'))
CASES['цех 05.08 (контр.)'] = (lsgeom.cut_surface(shop, so)[0], 'v12')

print()
print("ПОТОЛОК: что останется при ИДЕАЛЬНОМ предсказании позы, мм")
print("=" * 84)
print(f"{'случай':<20}{'режим':<26}{'среднее':>9}{'p90':>7}{'МАКСИМУМ':>10}{'≤2мм':>7}")
print("-" * 84)

out = {}
for name, (G, nb) in CASES.items():
    pool = [v for v in dataset.TRAIN if not np.array_equal(LIB[v], G)]
    r_nb = score(fit_rigid(LIB[nb], G), G)
    best = min((score(fit_rigid(LIB[c], G), G) for c in pool), key=lambda r: r[0])
    bestS = min((score(fit_rigid(LIB[c], G, scale=True), G) for c in pool),
                key=lambda r: r[0])
    out[name] = dict(nb=r_nb, best=best, best_scale=bestS)
    for label, r in ((f'сосед k-NN ({nb})', r_nb), ('лучший сосед', best),
                     ('+ масштаб', bestS)):
        print(f"{name if label.startswith('сосед') else '':<20}{label:<26}"
              f"{r[0]:>9.2f}{r[1]:>7.2f}{r[2]:>10.2f}{r[3]:>6.0f}%")
    print("-" * 84)

new = [k for k in CASES if k.startswith('v2')]
print()
print("Свод по шести слепым (режим «+ масштаб» = абсолютный потолок подхода):")
for key, label in (('nb', 'при нынешнем выборе соседа'), ('best', 'лучший сосед'),
                   ('best_scale', '+ масштаб')):
    m = np.mean([out[k][key][0] for k in new])
    mx = max(out[k][key][2] for k in new)
    w = np.mean([out[k][key][3] for k in new])
    print(f"  {label:<28} среднее {m:>5.2f}   худший максимум {mx:>5.2f}   "
          f"в допуске {w:>3.0f}%")

print()
print("Фактический результат пайплайна для сравнения: среднее "
      f"{np.mean([RES[k]['ours']['mean'] for k in new]):.2f}, "
      f"сосед как есть {np.mean([RES[k]['neigh']['mean'] for k in new]):.2f}")
