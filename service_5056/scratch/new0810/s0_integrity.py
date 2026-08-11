"""Шаг 0 для новых наборов v20-v25: целостность файлов и разброс формы.

Слепоту теста не тратит: смотрим только на данные заказчика (структуру .LS и
геометрию линий реза), ни разу не запуская наш пайплайн и ничего не подбирая.

Что меряем и почему именно так:

  * структура - число точек, число команд движения, замыкающий отрезок кольца.
    У v4 в архиве разрыв 8.92 мм при шаге 10, и если такой же дефект есть здесь,
    он испортит любой замер молча;

  * разброс формы - остаток после ICP между линиями реза. Отступ ФИКСИРОВАН на
    номинале, а не подобран. Подбор отступа - это лишняя степень свободы, которая
    частично съедает настоящую разницу формы (кольцо скользит по куполу, см.
    HANDOFF п.3), поэтому для вопроса "различаются ли детали" он вреден.
    Подобранный отступ печатается рядом отдельно, как диагностика.

Контроль - v1..v12 из архива: это заведомо ОДИН физический шлем, снятый 12 раз,
и их взаимный остаток есть шум метода, с которым сравниваются новые.
"""
import os
import sys
import itertools
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
ROOT = os.path.abspath(os.path.join(BASE, '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import lsgeom  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

NEW_DIR = os.path.join(ROOT, 'Helmet (10.08)')
NEW = {
    'v20': ('v20 form_1', 'TOR_XL_LEARN_V20.LS'),
    'v21': ('v21 form_1', 'TOR_XL_LEARN_V21.LS'),
    'v22': ('v22 form_4', 'TOR_XL_LEARN_V22.LS'),
    'v23': ('v23 form_4', 'TOR_XL_LEARN_V23.LS'),
    'v24': ('v24 form_1', 'TOR_XL_LEARN_V24.LS'),
    'v25': ('v25 form_1', 'TOR_XL_LEARN_V25.LS'),
}
FORM = {'v20': 1, 'v21': 1, 'v22': 4, 'v23': 4, 'v24': 1, 'v25': 1}
CONTROL = [f'v{i}' for i in range(1, 13)]     # один шлем, отступ у всех 9.9-10.6


def load_new(name):
    d, f = NEW[name]
    return lsgeom.load(os.path.join(NEW_DIR, d, f))


def load_arch(name):
    return lsgeom.load(os.path.join(BASE, 'input', 'archive', name, 'ground_truth.ls'))


def shape_gap(A, B):
    """Остаток между двумя линиями реза после снятия жёсткого движения, мм.

    Симметризован: метрика точка->кривая односторонняя, и на v6 односторонний
    замер уже давал 9.09 против 2.90 в обратную сторону (PLAN 3).
    """
    Rm, t = lsgeom.icp(A, B)
    d1 = lsgeom.curve_distance(A @ Rm.T + t, B)
    Rm2, t2 = lsgeom.icp(B, A)
    d2 = lsgeom.curve_distance(B @ Rm2.T + t2, A)
    return max(d1.mean(), d2.mean()), max(d1.max(), d2.max())


print()
print("ШАГ 0. Целостность и разброс формы, наборы 10.08")
print("=" * 78)

progs, cuts = {}, {}
print(f"\n{'вариант':<9}{'форма':>6}{'точек':>7}{'команд':>8}{'контур':>8}"
      f"{'шаг мед.':>10}{'замык.':>9}{'дефекты':>10}")
print("-" * 78)
for name in NEW:
    p = load_new(name)
    ring, ids = lsgeom.cut_ring(p)
    seg = np.linalg.norm(np.diff(ring, axis=0), axis=1)
    close = float(np.linalg.norm(ring[0] - ring[-1]))
    bad = p.problems()
    progs[name] = p
    cuts[name] = lsgeom.cut_surface(p, lsgeom.NOMINAL_STANDOFF)[0]
    print(f"{name:<9}{FORM[name]:>6}{len(p.points):>7}{len(p.order):>8}"
          f"{len(ring):>8}{np.median(seg):>10.2f}{close:>9.2f}"
          f"{('ОК' if not bad else str(len(bad))):>10}")
    for b in bad:
        print(f"           ! {b}")

ctl = {}
for name in CONTROL:
    ctl[name] = lsgeom.cut_surface(load_arch(name), lsgeom.NOMINAL_STANDOFF)[0]

print()
print("Разброс формы, отступ зафиксирован на номинале 10 мм (мм)")
print("-" * 78)

pairs_ctl = [shape_gap(ctl[a], ctl[b]) for a, b in itertools.combinations(CONTROL, 2)]
mc = np.array([x[0] for x in pairs_ctl])
xc = np.array([x[1] for x in pairs_ctl])
print(f"контроль v1..v12 (ОДИН шлем, {len(pairs_ctl)} пар): "
      f"среднее {mc.mean():.2f} (макс из пар {mc.max():.2f}), "
      f"поточечный максимум {xc.max():.2f}")

print()
print("Новые против архивного шлема (v1..v12), среднее по 12 опорам:")
for name in NEW:
    g = [shape_gap(cuts[name], ctl[c]) for c in CONTROL]
    m = np.array([x[0] for x in g])
    print(f"  {name}  форма {FORM[name]}   {m.mean():>6.2f}   "
          f"(разброс {m.min():.2f}-{m.max():.2f})")

print()
print("Новые между собой, среднее расхождение формы:")
names = list(NEW)
print("        " + "".join(f"{n:>8}" for n in names))
M = np.zeros((len(names), len(names)))
for i, a in enumerate(names):
    row = ""
    for j, b in enumerate(names):
        if i == j:
            row += f"{'-':>8}"
            continue
        if M[j, i]:
            M[i, j] = M[j, i]
        else:
            M[i, j] = shape_gap(cuts[a], cuts[b])[0]
        row += f"{M[i, j]:>8.2f}"
    print(f"{a:<8}" + row)

same = [M[i, j] for i in range(6) for j in range(i + 1, 6)
        if FORM[names[i]] == FORM[names[j]]]
diff = [M[i, j] for i in range(6) for j in range(i + 1, 6)
        if FORM[names[i]] != FORM[names[j]]]
print()
print(f"  пары внутри одной формы ({len(same)}): среднее {np.mean(same):.2f}, "
      f"диапазон {min(same):.2f}-{max(same):.2f}")
print(f"  пары разных форм        ({len(diff)}): среднее {np.mean(diff):.2f}, "
      f"диапазон {min(diff):.2f}-{max(diff):.2f}")

print()
print("Диагностика: какой отступ подобрался бы, если его не фиксировать")
print("(далеко от 10 = кольцо не садится на форму архивного шлема)")
print("-" * 78)
REF = cuts['v20'] * 0 + lsgeom.cut_surface(load_arch('v1'), lsgeom.NOMINAL_STANDOFF)[0]
for name in NEW:
    d, r = lsgeom.fit_standoff(progs[name], REF)
    print(f"  {name}   отступ {d:>6.2f} мм,  остаток {r:.2f} мм")
