"""Где по контуру ошибка больше: систематика или шум?

Средняя ошибка 1.9 мм при p90 3.1 означает, что промахи распределены неравномерно.
Вопрос: есть ли участки, где промахи БОЛЬШЕ СИСТЕМАТИЧЕСКИ, или это разные места
у разных шлемов (тогда это шум и чинить нечего).

Чтобы ответ не зависел от двух held-out вариантов, берём все 16:
  * 14 обучающих — предсказание leave-one-out (модель их не видела);
  * v6, v13 — полная модель, как в эксплуатации.

Общая координата — угол вокруг центра контура в плоскости XY станка. Позы вариантов
отличаются на единицы миллиметров и градусов, поэтому угол сопоставим между ними.
"""
import os
import sys
import numpy as np

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import lsgeom     # noqa: E402
import dataset    # noqa: E402
import features   # noqa: E402
import fit_model as fm   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

KIND, LAM = "prof", 100
NSEC = 24                                    # 15° на сектор
TRAIN, HELD = dataset.TRAIN, dataset.HELDOUT
ALL = TRAIN + HELD

F = features.load(ALL)
for v in ALL:
    fm.standoff(v)
piv = np.array([1170.98, 785.15, -191.86])   # как в model_pose.json

print("ICP каждого варианта к якорю...")
for v in ALL:
    fm.transform_from_ref(v, fm.ANCHOR)
POSE = {(a, b): fm.pose_between(a, b, piv, fm.ANCHOR)
        for a in ALL for b in ALL if a != b}


def predict_for(v, pool):
    W, sx = fm.fit_pairs(pool, F, KIND, LAM, POSE)
    ref = fm.nearest(v, pool, F, KIND)
    p = fm.predict(W, sx, F, KIND, ref, v)
    return fm.apply_pose(fm.contour(ref), p, piv), ref


rows = {}
for v in ALL:
    pool = [u for u in TRAIN if u != v]      # для held-out это весь TRAIN
    pred, ref = predict_for(v, pool)
    G = fm.contour(v)
    e = lsgeom.curve_distance(pred, G)
    c = G.mean(0)
    ang = (np.degrees(np.arctan2(G[:, 1] - c[1], G[:, 0] - c[0])) + 360) % 360
    rows[v] = dict(err=e, ang=ang, xy=G[:, :2], z=G[:, 2], ref=ref)
    print(f"  {v:<4} сосед {ref:<4} среднее {e.mean():5.2f}  макс {e.max():5.2f}")

# --- ошибка по секторам ---------------------------------------------------
edges = np.linspace(0, 360, NSEC + 1)
per_var = {}
for v, r in rows.items():
    idx = np.clip(np.digitize(r['ang'], edges) - 1, 0, NSEC - 1)
    per_var[v] = np.array([r['err'][idx == s].mean() if (idx == s).any() else np.nan
                           for s in range(NSEC)])

M = np.array([per_var[v] for v in ALL])
mean_sec = np.nanmean(M, axis=0)
worst_of = np.nanargmax(M, axis=1)           # худший сектор каждого варианта

print("\n" + "=" * 72)
print("Ошибка по секторам (угол вокруг центра контура в XY станка)")
print("=" * 72)
print(f"{'сектор':>10}{'среднее':>10}{'худший из 16':>14}{'у скольких он худший':>22}")
order = np.argsort(-mean_sec)
for s in order:
    cnt = int((worst_of == s).sum())
    bar = "#" * int(round(mean_sec[s] * 8))
    print(f"{int(edges[s]):>4}-{int(edges[s+1]):<5}{mean_sec[s]:>10.2f}"
          f"{np.nanmax(M[:, s]):>14.2f}{cnt:>18} шт  {bar}")

print("\nЕсли худший сектор у большинства вариантов один и тот же — систематика.")
print("Если разбросан — шум, и чинить нечего.")
top = int(order[0])
print(f"\nХудший в среднем сектор {int(edges[top])}-{int(edges[top+1])}°: "
      f"{mean_sec[top]:.2f} мм против {np.nanmin(mean_sec):.2f} в лучшем "
      f"(отношение {mean_sec[top]/np.nanmin(mean_sec):.1f}x). "
      f"Он же худший у {int((worst_of == top).sum())} из {len(ALL)} вариантов.")

# --- где резкие повороты контура (дефект генерации CAM, Q6) ----------------
G = fm.contour(fm.ANCHOR)
d1 = np.roll(G, -1, axis=0) - G
d0 = G - np.roll(G, 1, axis=0)
cosang = (d0 * d1).sum(1) / (np.linalg.norm(d0, axis=1) * np.linalg.norm(d1, axis=1))
turn = np.degrees(np.arccos(np.clip(cosang, -1, 1)))
c = G.mean(0)
ga = (np.degrees(np.arctan2(G[:, 1] - c[1], G[:, 0] - c[0])) + 360) % 360
k = int(turn.argmax())
print(f"\nСамый резкий поворот контура: {turn[k]:.0f}° за шаг, на угле {ga[k]:.0f}°, "
      f"высота Z={G[k, 2]:.0f}")
print(f"Повороты >25°: углы " +
      ", ".join(f"{ga[i]:.0f}°" for i in np.argsort(-turn)[:6] if turn[i] > 25))

np.save(os.path.join(BASE, 'results', '_where_error.npy'),
        np.array({v: rows[v] for v in ALL}, dtype=object), allow_pickle=True)
print("\nсырьё сохранено в results/_where_error.npy")
