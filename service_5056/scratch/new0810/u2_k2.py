"""Проверка k=2: помогает ли смешивание двух соседей.

В документах это числится как «стоит проверить, метит в максимум» с 04.08 и до сих
пор не проверено под текущим протоколом. Довод был такой: при k=1 мы наследуем
ручную подгонку ОДНОГО оператора целиком, вместе с его ошибкой в каждой точке, а
усреднение нескольких программ срезало бы её примерно в корень из k раз.

Довод ослаб после замера 10.08: повторяемость оператора 0.37 мм (v1 против v2 -
одна и та же позиция, записанная дважды), то есть шума в таргете мало и срезать
почти нечего. Но проверить дешевле, чем рассуждать.

Критерий объявлен заранее и тот же, что выбирал нынешнюю модель: leave-one-variant-out
внутри TRAIN, ошибка при выборе соседа так же, как в эксплуатации. Смотрим и на
среднее, и на МАКСИМУМ - k=2 метил именно в максимум.

Смешивание - штатное lsgeom.blend_contours (выравнивание по длине дуги, не по
индексам точек). Веса обратно пропорциональны расстоянию в пространстве признаков.

v6/v13 и шесть слепых наборов здесь не читаются вообще.
"""
import os
import sys
import json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import fit_model   # noqa: E402
import features    # noqa: E402
import lsgeom      # noqa: E402
import dataset     # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MODEL = json.load(open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8'))
PIVOT, LAM, KIND = np.array(MODEL['pivot']), MODEL['lam'], MODEL['feature_kind']
ANCHOR = MODEL['anchor']

names = dataset.guard_training(dataset.TRAIN)
F = features.load(names)
for v in names:
    fit_model.transform_from_ref(v, ANCHOR)


def ranked(v, pool):
    """Соседи по тому же правилу, что в step04: расстояние / разброс по библиотеке."""
    lib = np.array([features.vec(F[u], KIND) for u in pool])
    sc = lib.std(0)
    sc[sc < 1e-9] = 1.0
    cur = features.vec(F[v], KIND)
    d = {u: float(np.linalg.norm((cur - features.vec(F[u], KIND)) / sc)) for u in pool}
    return sorted(d.items(), key=lambda kv: kv[1])


print()
print("LOO внутри TRAIN: сколько соседей смешивать")
print("=" * 66)
print(f"{'k':<4}{'среднее':>10}{'МАКСИМУМ':>11}{'p90 по вариантам':>19}")
print("-" * 66)

res = {}
for k in (1, 2, 3):
    per = []
    for v in names:
        tr = [u for u in names if u != v]
        P = {(x, y): fit_model.pose_between(x, y, PIVOT, ANCHOR)
             for x in tr for y in tr if x != y}
        W, sx = fit_model.fit_pairs(tr, F, KIND, LAM, P)
        rk = ranked(v, tr)[:k]
        # веса обратно пропорциональны расстоянию: ближний сосед весит больше
        w = np.array([1.0 / max(d, 1e-6) for _, d in rk])
        w /= w.sum()
        contours = [fit_model.contour(u) for u, _ in rk]
        mixed = (lsgeom.blend_contours(contours, list(w)) if k > 1 else contours[0])
        # поправка считается от ближайшего соседа - он же задаёт опорные признаки
        p = fit_model.predict(W, sx, F, KIND, rk[0][0], v)
        moved = fit_model.apply_pose(mixed, p, PIVOT)
        d = lsgeom.curve_distance(moved, fit_model.contour(v))
        per.append((float(d.mean()), float(d.max())))
    a = np.array(per)
    res[k] = a
    print(f"{k:<4}{a[:, 0].mean():>10.2f}{a[:, 1].max():>11.2f}"
          f"{np.percentile(a[:, 0], 90):>19.2f}")

print()
print("Повариантно, среднее (мм):")
print(f"{'вариант':<9}" + "".join(f"{'k=' + str(k):>8}" for k in (1, 2, 3)))
for i, v in enumerate(names):
    print(f"{v:<9}" + "".join(f"{res[k][i, 0]:>8.2f}" for k in (1, 2, 3)))

print()
best = min(res, key=lambda k: res[k][:, 0].mean())
print(f"Лучшее по среднему: k={best}. "
      f"По максимуму: k={min(res, key=lambda k: res[k][:, 1].max())}.")
print("Напоминание: k=1 выбран не по лени - при одном соседе экспорт побитово")
print("воспроизводит его программу, и любое ухудшение здесь означает, что смешивание")
print("вносит больше, чем убирает.")
