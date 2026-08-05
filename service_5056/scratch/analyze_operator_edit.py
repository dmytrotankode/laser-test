"""Первая прямая проверка на производстве: насколько оператор правил НАШУ программу.

05.08 заказчику отдали программу, сгенерированную по свежей съёмке (шлем, которого
модель никогда не видела). Оператор загрузил её и подогнал руками. Разница между
двумя файлами — это ровно наша ошибка, измеренная на реальном шлеме, а не на
архивных вариантах, которые уже многократно смотрелись.

Ничего не подбирается и не обучается: только сравнение двух файлов.
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

SRC = os.path.abspath(os.path.join(BASE, '..', '05082026_test1'))
OURS = os.path.join(SRC, 'TOR_XL_LEARN_V6.ls')
THEIRS = os.path.join(SRC, 'TOR_XL_LEARN_V6_2.LS')

ours, theirs = lsgeom.load(OURS), lsgeom.load(THEIRS)

print("=" * 74)
print("СТРУКТУРА")
print("=" * 74)
for name, p in (("наш", ours), ("правка оператора", theirs)):
    print(f"  {name:<18} точек {len(p.points):>3}, команд движения {len(p.order):>3}, "
          f"проблемы: {p.problems() or 'нет'}")
same_ids = set(ours.points) == set(theirs.points)
same_order = ours.order == theirs.order
print(f"  один набор точек: {same_ids} | один порядок обхода: {same_order}")
if not same_ids:
    print("  ВНИМАНИЕ: наборы точек различаются, поточечное сравнение некорректно")

# ---------------------------------------------------------------- поточечно
ids = [i for i in ours.order if i in theirs.points]
seen, uniq = set(), []
for i in ids:
    if i not in seen:
        seen.add(i)
        uniq.append(i)
A = np.array([ours.points[i][:3] for i in uniq])
B = np.array([theirs.points[i][:3] for i in uniq])
WA = np.array([ours.points[i][3:] for i in uniq])
WB = np.array([theirs.points[i][3:] for i in uniq])
d = np.linalg.norm(B - A, axis=1)

print()
print("=" * 74)
print("НА СКОЛЬКО ОПЕРАТОР ПОДВИНУЛ КАЖДУЮ ТОЧКУ (мм)")
print("=" * 74)
print(f"  среднее {d.mean():.2f} | p90 {np.percentile(d, 90):.2f} | максимум {d.max():.2f}")
print(f"  не тронул вообще (<0.01 мм): {int((d < 0.01).sum())} из {len(d)}")
for t in (0.5, 1.0, 2.0, 3.0):
    print(f"  сдвиг <= {t:.1f} мм: {int((d <= t).sum()):>3} из {len(d)}  ({100*(d<=t).mean():.0f} %)")

print()
print("Углы W/P/R оператор трогал?")
dw = np.abs(WB - WA).max(axis=1)
print(f"  максимальное изменение угла: {dw.max():.3f}°, "
      f"точек с изменением >0.01°: {int((dw > 0.01).sum())} из {len(dw)}")

# ---------------------------------------------------------------- по линии реза
print()
print("=" * 74)
print("ОШИБКА ПО ЛИНИИ РЕЗА (метрика отчёта: точка -> кривая)")
print("=" * 74)
so_ours = lsgeom.NOMINAL_STANDOFF
anchor = lsgeom.load(os.path.join(BASE, 'input', 'archive', 'v1', 'ground_truth.ls'))
ref, _ = lsgeom.cut_surface(anchor, lsgeom.NOMINAL_STANDOFF)
so_theirs, res_theirs = lsgeom.fit_standoff(theirs, ref)
so_ours_fit, res_ours = lsgeom.fit_standoff(ours, ref)
print(f"  отступ в нашем файле:      подобран {so_ours_fit:.2f} мм "
      f"(писали номинальные {so_ours:.0f}), остаток формы {res_ours:.2f} мм")
print(f"  отступ после правки:       подобран {so_theirs:.2f} мм, "
      f"остаток формы {res_theirs:.2f} мм")

C, _ = lsgeom.cut_surface(ours, so_ours)
G, _ = lsgeom.cut_surface(theirs, so_theirs)
e = lsgeom.curve_distance(C, G)
print()
print(f"  среднее {e.mean():.2f} | p90 {np.percentile(e, 90):.2f} | максимум {e.max():.2f} мм")
for t in (1.0, 2.0, 3.0):
    print(f"  точек в допуске {t:.0f} мм: {100*(e<=t).mean():.0f} %")

# ---------------------------------------------------------------- база
print()
print("=" * 74)
print("С ЧЕМ СРАВНИВАТЬ: «ничего не делать» на этом же шлеме")
print("=" * 74)
best = None
for c in dataset.TRAIN:
    p = lsgeom.load(os.path.join(BASE, 'input', 'archive', c, 'ground_truth.ls'))
    so, _ = lsgeom.fit_standoff(p, ref)
    Cc, _ = lsgeom.cut_surface(p, so)
    ec = lsgeom.curve_distance(Cc, G)
    if best is None or ec.mean() < best[1]:
        best = (c, float(ec.mean()), float(ec.max()))
    print(f"  {c:<5} среднее {ec.mean():6.2f}  макс {ec.max():6.2f}")
print(f"\n  лучшая фиксированная программа: {best[0]} -> {best[1]:.2f} мм "
      f"(это НЕ честная база: выбрана уже зная ответ)")
print(f"  наш результат: {e.mean():.2f} мм")
