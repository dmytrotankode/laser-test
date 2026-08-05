"""Поднимет ли усреднение нескольких программ ПОТОЛОК подхода?

Гипотеза. Максимум ошибки держит шум ручной подгонки ОДНОГО соседа: при k=1 мы
копируем его контур целиком, вместе с тем, как он дёрнул каждую отдельную точку.
Усреднение нескольких программ должно этот шум срезать примерно в sqrt(k) раз.

Проверяем именно ПОТОЛОК (оракул — подгонка с подсматриванием ответа), а не пайплайн:
если потолок не двигается, улучшать модель бесполезно, до него всё равно не дойти.

Честность:
  * мастер-контур строится ТОЛЬКО из TRAIN, цель в него не входит;
  * для v6/v13 это весь TRAIN (они в него и так не входят);
  * ключевая колонка — МАКСИМУМ, ради него всё и затевается.
"""
import os
import sys
import numpy as np

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import lsgeom     # noqa: E402
import dataset    # noqa: E402
import features   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ANCHOR = 'v1'
anchor_prog = lsgeom.load(os.path.join(BASE, 'input', 'archive', ANCHOR, 'ground_truth.ls'))
REF, _ = lsgeom.cut_surface(anchor_prog, lsgeom.NOMINAL_STANDOFF)


def cutline_of(path):
    p = lsgeom.load(path)
    so, _ = lsgeom.fit_standoff(p, REF)
    return lsgeom.cut_surface(p, so)[0]


def oracle_fit(A, B, iters=60, n=1200):
    """Наилучшее жёсткое совмещение A -> B (подсматривает ответ)."""
    Bd = lsgeom.resample_closed(np.asarray(B, float), n)
    A = np.asarray(A, float)
    X = A.copy()
    for _ in range(iters):
        j = np.linalg.norm(X[:, None, :] - Bd[None, :, :], axis=2).argmin(1)
        Rm, t = lsgeom.kabsch(A, Bd[j])
        X = A @ Rm.T + t
    return X


def score(A, B):
    e = lsgeom.curve_distance(oracle_fit(A, B), B)
    return float(e.mean()), float(np.percentile(e, 90)), float(e.max()), float((e <= 1.5).mean())


print("Загрузка линий реза...", flush=True)
CUT = {v: cutline_of(os.path.join(BASE, 'input', 'archive', v, 'ground_truth.ls'))
       for v in dataset.ALL}
PROD = cutline_of(os.path.join(BASE, '..', '05082026_test1', 'TOR_XL_LEARN_V6_2.LS'))

# ---- мастер-контур: привести все обучающие к общей системе и усреднить -------
def master(pool):
    """Средняя форма по pool. Каждый контур сначала жёстко совмещается с якорем,
    иначе усреднялись бы разные ПОЗЫ, а не форма."""
    aligned = []
    for v in pool:
        Rm, t = lsgeom.icp(CUT[v], CUT[ANCHOR])
        aligned.append(CUT[v] @ Rm.T + t)
    return lsgeom.blend_contours(aligned, [1.0] * len(aligned))


F = features.load(dataset.ALL)


def nearest_k(target_feat, pool, k):
    lib = np.array([features.vec(F[v], 'prof') for v in pool])
    sc = lib.std(0)
    sc[sc < 1e-9] = 1.0
    d = {v: float(np.linalg.norm((target_feat - features.vec(F[v], 'prof')) / sc))
         for v in pool}
    return sorted(d, key=d.get)[:k]


TESTS = [('v13', CUT['v13'], features.vec(F['v13'], 'prof')),
         ('v6', CUT['v6'], features.vec(F['v6'], 'prof')),
         ('05.08 цех', PROD, None)]

print()
print(f"{'случай':<12}{'источник формы':<34}{'среднее':>9}{'p90':>8}{'МАКС':>9}{'<=1.5':>8}")
print("=" * 80)
for name, G, feat in TESTS:
    pool = [v for v in dataset.TRAIN]
    rows = []

    best = min((score(CUT[c], G) for c in pool), key=lambda r: r[2])
    rows.append(("1 сосед, лучший из 14", best))

    if feat is not None:
        for k in (2, 3, 5):
            nb = nearest_k(feat, pool, k)
            aligned = []
            for v in nb:
                Rm, t = lsgeom.icp(CUT[v], CUT[nb[0]])
                aligned.append(CUT[v] @ Rm.T + t)
            M = lsgeom.blend_contours(aligned, [1.0] * len(aligned))
            rows.append((f"{k} ближайших, усреднены", score(M, G)))

    rows.append(("мастер: среднее по всем 14", score(master(pool), G)))

    for label, (m, p9, mx, fr) in rows:
        print(f"{name:<12}{label:<34}{m:>9.2f}{p9:>8.2f}{mx:>9.2f}{100*fr:>7.0f}%")
    print("-" * 80)

print()
print("Смотреть на колонку МАКС. Если усреднение её не двигает — шум одного соседа")
print("не был ограничением, и k>1 ничего не даст. Если двигает — есть куда расти.")
