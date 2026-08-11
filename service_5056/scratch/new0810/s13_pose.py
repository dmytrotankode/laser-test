"""Шаг 8: где эти шлемы стоят на самом деле.

Отсечка не виновата (s11, s12: оба правила ухудшают LOO). Остаётся вопрос, с
которого стоило начать: а лежат ли позы шести наборов внутри того облака, на
котором модель обучена?

У шести есть ground truth, значит истинная поза считается прямо - ICP их линии
реза к якорю, ровно тем же способом, каким размечены обучающие пары. Тогда
видно, что именно происходит:

  поза внутри облака, а модель промахнулась -> виноваты признаки или регрессия;
  поза вне облака                           -> модель экстраполирует, и лечится
                                               это добором библиотеки, а не
                                               улучшением математики.

Заодно сравнивается предсказанная поправка с истинной - покомпонентно.
"""
import os
import sys
import json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import fit_model   # noqa: E402
import dataset     # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MODEL = json.load(open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8'))
PIVOT = np.array(MODEL['pivot'])
LIB = MODEL['library']
ANCHOR = MODEL['anchor']
SESS = json.load(open(os.path.join(HERE, 's6_sessions.json')))
SESS['v20'] = 'run_20260810_125404'
AXES = ('X', 'Y', 'Z', 'roll', 'pitch', 'yaw')

names = list(LIB)
allv = names + dataset.BLIND
for v in allv:
    fit_model.transform_from_ref(v, ANCHOR)

TRUE = {v: fit_model.pose_between(ANCHOR, v, PIVOT, ANCHOR) for v in dataset.BLIND}
LIBP = np.array([LIB[v]['pose_vs_anchor'] for v in names])

print()
print("Позы относительно якоря: библиотека против шести слепых")
print("=" * 78)
print(f"{'':<10}" + "".join(f"{a:>9}" for a in AXES))
print(f"{'библ. min':<10}" + "".join(f"{x:>9.2f}" for x in LIBP.min(0)))
print(f"{'библ. max':<10}" + "".join(f"{x:>9.2f}" for x in LIBP.max(0)))
print(f"{'библ. σ':<10}" + "".join(f"{x:>9.2f}" for x in LIBP.std(0)))
print("-" * 78)
for v in dataset.BLIND:
    print(f"{v:<10}" + "".join(f"{x:>9.2f}" for x in TRUE[v]))
print("-" * 78)
print("во сколько σ библиотеки выходит поза (0 = внутри диапазона):")
for v in dataset.BLIND:
    out = []
    for k in range(6):
        lo, hi, s = LIBP[:, k].min(), LIBP[:, k].max(), LIBP[:, k].std()
        d = max(lo - TRUE[v][k], TRUE[v][k] - hi, 0.0)
        out.append(d / s if s > 1e-9 else 0.0)
    print(f"{v:<10}" + "".join(f"{x:>9.1f}" for x in out))

print()
print("Предсказанная поправка против истинной, мм и градусы")
print("=" * 78)
for v in dataset.BLIND:
    st4 = json.load(open(os.path.join(BASE, 'results', SESS[v],
                                      'step04_result.json'), encoding='utf-8'))
    nb = st4['etalon']
    d = st4['delta_rel_to_etalon']
    pred = np.array([d['x_mm'], d['y_mm'], d['z_mm'],
                     d['roll_deg'], d['pitch_deg'], d['yaw_deg']])
    true = fit_model.pose_between(nb, v, PIVOT, ANCHOR)
    print(f"\n{v}  (опора {nb})")
    print(f"{'':<12}" + "".join(f"{a:>9}" for a in AXES))
    print(f"{'истина':<12}" + "".join(f"{x:>9.2f}" for x in true))
    print(f"{'предсказ.':<12}" + "".join(f"{x:>9.2f}" for x in pred))
    print(f"{'промах':<12}" + "".join(f"{x:>9.2f}" for x in pred - true))
