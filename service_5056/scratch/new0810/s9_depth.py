"""Шаг 6: калибровка новой отсечки Safe Zone и проверка, что она чинит признаки.

Глубина выбирается ТОЛЬКО по TRAIN, как медиана той глубины, которую нынешнее
правило (0.58 высоты силуэта) даёт на обучающих вариантах. Смысл выбора: на
архиве маски остаются практически теми же, что были, - меняется не сама зона, а
то, к чему она привязана. Значит правка не переучивает систему на другую часть
детали, а лишь перестаёт зависеть от длины юбки.

Ни held-out, ни шесть слепых наборов на выбор глубины не влияют: они здесь только
измеряются.

Проверяемое утверждение: в новых признаках расстояние слепых наборов до
библиотеки должно упасть к масштабу самой библиотеки. Расстояние считается той же
формулой, что в step04, но с knn_scale, пересчитанным по TRAIN на новых признаках
(старый относится к старым маскам и здесь неприменим).
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
import dataset                                          # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SKIRT = json.load(open(os.path.join(HERE, 's4_skirt.json')))
CACHE = os.path.join(HERE, 's9_feats.json')
BLIND = dataset.BLIND
VIEWS = ('back', 'left', 'top')

# --- глубина: медиана нынешней глубины по TRAIN, на каждый боковой вид ---------
DEPTH = {}
for view in ('back', 'left'):
    d = [SKIRT[f'{v}/{view}']['cutoff'] - SKIRT[f'{v}/{view}']['top']
         for v in dataset.TRAIN]
    DEPTH[view] = int(np.median(d))

print("Глубина Safe Zone от верха купола (калибрована по TRAIN, px):")
for view in ('back', 'left'):
    d = np.array([SKIRT[f'{v}/{view}']['cutoff'] - SKIRT[f'{v}/{view}']['top']
                  for v in dataset.TRAIN])
    print(f"  {view}: {DEPTH[view]}   (по TRAIN разброс {d.min()}-{d.max()}, "
          f"σ {d.std():.0f})")

# запас до края юбки: отсечка обязана лежать ВЫШЕ него, иначе в маску попадёт кевлар
print("\nЗапас между новой отсечкой и краем юбки (px, чем больше тем безопаснее):")
for grp, names in (('TRAIN', dataset.TRAIN), ('held-out', dataset.HELDOUT),
                   ('слепые', BLIND)):
    m = []
    for v in names:
        for view in ('back', 'left'):
            s = SKIRT[f'{v}/{view}']
            m.append(s['bottom'] - (s['top'] + DEPTH[view]))
    print(f"  {grp:<9} минимум {min(m):>5.0f}, медиана {np.median(m):>5.0f}")

# --- признаки на новых масках -------------------------------------------------
SRC = {}
for v in dataset.ALL:
    SRC[v] = {w: os.path.join(BASE, 'input', 'archive', v, f'{w}.png') for w in VIEWS}
for v in BLIND:
    SRC[v] = {w: os.path.join(BASE, 'input', 'archive', v, f'{w}.png') for w in VIEWS}

F = {k: np.array(x) for k, x in
     (json.load(open(CACHE)).items() if os.path.exists(CACHE) else [])}
for v, paths in SRC.items():
    if v in F:
        continue
    masks = {}
    for w in VIEWS:
        m, _, _, _, b = segment_image(paths[w], w == 'top', depth_px=DEPTH.get(w))
        assert b != 'otsu', f'{v}/{w}'
        masks[w] = m
    F[v] = build_feature_vector(masks, 'prof')
    print(f'  пересегментирован {v}', flush=True)
json.dump({k: list(map(float, x)) for k, x in F.items()}, open(CACHE, 'w'))

OLD = {k: np.array(x) for k, x in
       json.load(open(os.path.join(HERE, 's2_features.json'))).items()}
MODEL = json.load(open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8'))

scale = np.array([F[v] for v in dataset.TRAIN]).std(0)
scale[scale < 1e-9] = 1.0
old_scale = np.array(MODEL['knn_scale'])
old_lib = {v: np.array(MODEL['library'][v]['feat']) for v in MODEL['library']}


def dist(f, lib, sc):
    return min(float(np.linalg.norm((f - g) / sc)) for g in lib.values())


gaps_new = [min(float(np.linalg.norm((F[a] - F[b]) / scale))
                for b in dataset.TRAIN if b != a) for a in dataset.TRAIN]
gaps_old = [min(float(np.linalg.norm((old_lib[a] - old_lib[b]) / old_scale))
                for b in old_lib if b != a) for a in old_lib]

print()
print("Расстояние до библиотеки: было (доля высоты) -> стало (глубина от купола)")
print("=" * 74)
print(f"{'':<8}{'было':>9}{'стало':>9}     {'порог был':>10}{'порог стал':>12}")
print(f"{'':<8}{'':>9}{'':>9}     {max(gaps_old):>10.2f}{max(gaps_new):>12.2f}")
print("-" * 74)
new_lib = {v: F[v] for v in dataset.TRAIN}
for v in BLIND:
    print(f"{v:<8}{dist(OLD[v], old_lib, old_scale):>9.1f}"
          f"{dist(F[v], new_lib, scale):>9.1f}")
print("-" * 74)
for v in dataset.HELDOUT:
    o = dist(np.array(MODEL['library'][v]['feat']) if v in MODEL['library'] else OLD.get(v),
             old_lib, old_scale) if v in old_lib else None
    print(f"{v:<8}{'—' if o is None else f'{o:>9.1f}'}"
          f"{dist(F[v], new_lib, scale):>9.1f}   (held-out)")
print()
print(f"внутренние разрывы библиотеки: было {min(gaps_old):.2f}-{max(gaps_old):.2f}, "
      f"стало {min(gaps_new):.2f}-{max(gaps_new):.2f}")
