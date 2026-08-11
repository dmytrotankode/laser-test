"""Канавка, шаг 3: предсказывает ли она линию реза?

Трассировка (G2) даёт устойчивую линию: нижний путь ложится точно по борозде,
включая вырез уха. Вопрос теперь один - несёт ли её положение информацию о том,
куда оператор ставит рез, или это просто красивая линия.

Тест тот же, которым были отвергнуты верх купола, низ силуэта, k=2 и обе правки
Safe Zone: leave-one-variant-out ВНУТРИ TRAIN, той же функцией fit_model.loo_error.
Если канавка - настоящий ориентир оператора, добавка обязана улучшить LOO. Если
не улучшит, идея закрывается так же честно, как предыдущие.

Признак: положение канавки по высоте в 16 равномерных долях ширины детали, на
каждый боковой вид. Берётся нижняя (настоящая) линия из G2. Held-out и слепые
наборы не читаются.
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
import dataset     # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MODEL = json.load(open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8'))
PIVOT, LAM, KIND = np.array(MODEL['pivot']), MODEL['lam'], MODEL['feature_kind']
ANCHOR = MODEL['anchor']
LINES = json.load(open(os.path.join(HERE, 'G2_lines.json')))
NBINS = 16

names = dataset.guard_training(dataset.TRAIN)
BASEF = features.load(names)
for v in names:
    fit_model.transform_from_ref(v, ANCHOR)
POSE = {(x, y): fit_model.pose_between(x, y, PIVOT, ANCHOR)
        for x in names for y in names if x != y}


def groove_vec(v):
    """Высота канавки в 16 долях ширины, на каждый боковой вид."""
    out = []
    for view in ('back', 'left'):
        k = f'{v}_{view}'
        if k not in LINES:
            return None
        x = np.array(LINES[k]['x'], float)
        y = np.array(LINES[k]['lower'], float)
        s = np.array(LINES[k]['s_lower'], float)
        good = s > 5
        if good.sum() < NBINS * 2:
            return None
        x, y = x[good], y[good]
        grid = np.linspace(x.min(), x.max(), NBINS)
        out.extend(np.interp(grid, x, y))
    return np.array(out)


G = {v: groove_vec(v) for v in names}
missing = [v for v, g in G.items() if g is None]
if missing:
    print(f"канавка не найдена для: {missing}")
    names = [v for v in names if G[v] is not None]

print()
print(f"Канавка найдена для {len(names)} обучающих вариантов, "
      f"{NBINS} точек на вид")

# насколько канавка вообще двигается между вариантами - есть ли что использовать
M = np.array([G[v] for v in names])
print(f"разброс её положения по вариантам: {M.std(0).mean():.1f} px "
      f"(для сравнения, разброс признаков силуэта того же порядка величины)")


def extended(F):
    out = {}
    for v in names:
        e = {k: [list(r) for r in rows] for k, rows in F[v].items()}
        e['prof'][0] = list(e['prof'][0]) + list(G[v])
        out[v] = e
    return out


print()
print("LOO внутри TRAIN, мм")
print("=" * 60)
for label, F in (("нынешние признаки", {v: BASEF[v] for v in names}),
                 ("+ канавка", extended(BASEF))):
    per = fit_model.loo_error(names, F, KIND, LAM, POSE, PIVOT)
    nn = np.array([per[v]['nearest'] for v in names])
    print(f"{label:<26}среднее {nn.mean():>6.2f}   худший {nn.max():>6.2f}")

print()
print("Отдельно: связана ли канавка с позой напрямую (архив, один шлем)")
print("-" * 60)
Z = {v: fit_model.pose_between(ANCHOR, v, PIVOT, ANCHOR) for v in names}
for i, ax in enumerate(('X', 'Y', 'Z', 'roll', 'pitch', 'yaw')):
    z = np.array([Z[v][i] for v in names])
    # средняя высота канавки по обоим видам
    h = np.array([G[v].mean() for v in names])
    r = np.corrcoef(h, z)[0, 1]
    if abs(r) > 0.4:
        print(f"  средняя высота канавки против {ax}: корреляция {r:+.2f}")
