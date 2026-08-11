"""Шаг A5: повторяется ли результат, или подгонка садится куда попало.

Низкий остаток сам по себе ничего не доказывает: семь свободных параметров на
один силуэт могут просто облепить любую картинку. Настоящая проверка - подогнать
НЕЗАВИСИМО к нескольким съёмкам одного шлема и посмотреть на найденные КАМЕРЫ.

  * камеры сошлись (дистанция, фокус, ракурс близки) -> подгонка находит
    настоящую геометрию съёмки, и остаток это правда разница CAD с деталью;
  * камеры разъехались, а остаток мал -> облепливание, и все числа по CAD
    недействительны.

Съёмочная установка между вариантами не двигалась (это проверено отдельно,
Q11 в PLAN.md), поэтому камеры ОБЯЗАНЫ совпасть. Расходиться может только поза
шлема - но она в этой постановке сидит в том же повороте, поэтому смотрим на
дистанцию и фокус, которые от позы шлема не зависят.
"""
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ['A3_QUIET'] = '1'
import render as R                                    # noqa: E402
from scipy.spatial.transform import Rotation as Rot   # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# берём машинерию из a3, но без её главного блока
import importlib.util                                 # noqa: E402
spec = importlib.util.spec_from_file_location(
    'a3mod', os.path.join(HERE, 'a3_bestcase.py'))
src = open(os.path.join(HERE, 'a3_bestcase.py'), encoding='utf-8').read()
src = src.split("store = {}\nif os.path.exists(STORE):")[0]
a3 = importlib.util.module_from_spec(spec)
exec(compile(src, 'a3_bestcase.py', 'exec'), a3.__dict__)

VARIANTS = ['v1', 'v2', 'v9', 'v10']                  # только обучающие

# Полный объём поиска тут не нужен: вопрос не «выжать минимум», а «сходятся ли
# камеры». Полная настройка давала бы ~1.5 часа на 15 подгонок.
a3.N_RANDOM, a3.N_POLISH, a3.MAXITER = 40, 6, 800

print("Независимая подгонка к каждой съёмке. Камеры обязаны совпасть.")
print(f"(объём поиска урезан: {a3.N_RANDOM} случайных стартов, "
      f"{a3.N_POLISH} полировок)")
print()

for view in ('back', 'left', 'top'):
    print(f"--- {view} ---")
    print(f"{'вар':<6}{'остаток':>10}{'дистанция':>12}{'фокус':>12}{'ракурс vs v1':>15}")
    rows, rv0 = [], None
    for v in VARIANTS:
        if R.load_mask(v, view, a3.COARSE)[0] is None:
            continue
        val, par, _, _ = a3.fit_view(view, v, {})
        dist, foc = np.exp(par[3]), np.exp(par[4])
        rv = Rot.from_rotvec(par[:3])
        if rv0 is None:
            rv0, ang = rv, 0.0
        else:
            ang = np.degrees((rv * rv0.inv()).magnitude())
        rows.append((v, val, dist, foc, ang))
        print(f"{v:<6}{val * a3.MM_PER_PX:>7.2f} мм{dist:>10.0f} мм"
              f"{foc:>12.0f}{ang:>13.1f}°")
    if len(rows) > 1:
        d = np.array([r[2] for r in rows]); f = np.array([r[3] for r in rows])
        print(f"{'разброс':<6}{'':>10}{d.std() / d.mean() * 100:>9.1f} %"
              f"{f.std() / f.mean() * 100:>11.1f} %")
    print()

print("Дистанция и фокус не зависят от позы шлема - если они гуляют на десятки")
print("процентов, подгонка облепливает картинку, а не находит съёмку.")
