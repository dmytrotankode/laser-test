"""Шаг 7b: третье правило отсечки - фиксированная строка кадра.

Мотивация из s11: привязка к верху купола (depth_px) убивает сигнал о вертикали,
потому что маска едет вместе со шлемом. Фиксированная строка свободна от обоих
пороков: юбка её не двигает, а подъём шлема остаётся видимым, потому что купол
относительно неё смещается.

Строка выбирается по TRAIN - медиана нынешних отсечек. Held-out и слепые здесь
только измеряются.

Критерий тот же, что и раньше: LOO внутри TRAIN. Ниже 1.23 - правило принимается,
выше - отвергается, как отвергся depth_px.
"""
import os
import sys
import json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
from step03_segment_monochrome import segment_image     # noqa: E402
from step04_fit_3d_pose import build_feature_vector     # noqa: E402
import fit_model   # noqa: E402
import features    # noqa: E402
import dataset     # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SKIRT = json.load(open(os.path.join(HERE, 's4_skirt.json')))
CACHE = os.path.join(HERE, 's12_feats.json')
VIEWS = ('back', 'left', 'top')

ABS = {}
for view in ('back', 'left'):
    c = np.array([SKIRT[f'{v}/{view}']['cutoff'] for v in dataset.TRAIN])
    ABS[view] = int(np.median(c))
    print(f"{view}: строка {ABS[view]}  (по TRAIN нынешние отсечки {c.min()}-{c.max()}, "
          f"σ {c.std():.0f})")

F = {k: np.array(v) for k, v in
     (json.load(open(CACHE)).items() if os.path.exists(CACHE) else [])}
for v in dataset.ALL + dataset.BLIND:
    if v in F:
        continue
    masks = {}
    for w in VIEWS:
        m, _, _, _, b = segment_image(
            os.path.join(BASE, 'input', 'archive', v, f'{w}.png'),
            w == 'top', abs_y=ABS.get(w))
        assert b != 'otsu', f'{v}/{w}'
        masks[w] = m
    F[v] = build_feature_vector(masks, 'prof')
    print(f'  пересегментирован {v}', flush=True)
json.dump({k: list(map(float, x)) for k, x in F.items()}, open(CACHE, 'w'))


def as_entry(vec):
    return {'prof': [list(vec[i * 50:(i + 1) * 50]) for i in range(3)]}


MODEL = json.load(open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8'))
PIVOT, LAM, KIND = np.array(MODEL['pivot']), MODEL['lam'], MODEL['feature_kind']
names = dataset.guard_training(dataset.TRAIN)
ref = names[0]
for v in names:
    fit_model.transform_from_ref(v, ref)
POSE = {(x, y): fit_model.pose_between(x, y, PIVOT, ref)
        for x in names for y in names if x != y}

SETS = {
    'нынешняя (0.58 высоты)': features.load(dataset.ALL),
    'глубина от купола': {k: as_entry(np.array(v)) for k, v in
                          json.load(open(os.path.join(HERE, 's9_feats.json'))).items()},
    'фиксированная строка': {k: as_entry(v) for k, v in F.items()},
}

print()
print("LOO внутри TRAIN, мм")
print("=" * 62)
for label, FF in SETS.items():
    per = fit_model.loo_error(names, FF, KIND, LAM, POSE, PIVOT)
    nn = np.array([per[v]['nearest'] for v in names])
    print(f"{label:<26} среднее {nn.mean():>5.2f}   худший {nn.max():>5.2f}")

print()
print("Расстояние до библиотеки при фиксированной строке:")
sc = np.array([F[v] for v in dataset.TRAIN]).std(0)
sc[sc < 1e-9] = 1.0
gaps = [min(float(np.linalg.norm((F[a] - F[b]) / sc))
            for b in dataset.TRAIN if b != a) for a in dataset.TRAIN]
print(f"  порог (наибольший внутренний разрыв): {max(gaps):.2f}")
for v in dataset.BLIND + dataset.HELDOUT:
    d = min(float(np.linalg.norm((F[v] - F[u]) / sc)) for u in dataset.TRAIN)
    print(f"  {v}: {d:.1f}{'  ВНЕ ДИАПАЗОНА' if d > max(gaps) else ''}")
