"""Шаг 7: решает ли новая отсечка задачу - LOO внутри TRAIN.

Критерий выбора один и он объявлен заранее: leave-one-variant-out ВНУТРИ TRAIN,
той же функцией fit_model.loo_error, что выбирала нынешнюю модель. Held-out и
шесть слепых здесь не читаются.

Сравниваются два набора признаков на одних и тех же метках поз и одном и том же
коде: старые маски (доля высоты силуэта) против новых (глубина от верха купола).
Всё остальное - точка поворота, lambda, правило выбора соседа - не трогается,
иначе сравнение перестанет быть про отсечку.
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
PIVOT = np.array(MODEL['pivot'])
LAM = MODEL['lam']
KIND = MODEL['feature_kind']
names = dataset.guard_training(dataset.TRAIN)


def as_entry(vec):
    """Плоский вектор 150 -> формат features.load для kind='prof'."""
    return {'prof': [list(vec[i * 50:(i + 1) * 50]) for i in range(3)]}


NEW = {k: as_entry(np.array(v)) for k, v in
       json.load(open(os.path.join(HERE, 's9_feats.json'))).items()}
OLD = features.load(dataset.ALL)

print("Метки поз (ICP по линиям реза) — общие для обоих наборов, считаются один раз")
ref = names[0]
for v in names:
    fit_model.transform_from_ref(v, ref)
POSE = {(x, y): fit_model.pose_between(x, y, PIVOT, ref)
        for x in names for y in names if x != y}

print()
print("LOO внутри TRAIN, мм (ошибка при выборе соседа так же, как в эксплуатации)")
print("=" * 70)
for label, F in (('нынешняя отсечка (0.58 высоты)', OLD),
                 ('новая отсечка (глубина от купола)', NEW)):
    per = fit_model.loo_error(names, F, KIND, LAM, POSE, PIVOT)
    nn = np.array([per[v]['nearest'] for v in names])
    print(f"{label:<38} среднее {nn.mean():>5.2f}   худший {nn.max():>5.2f}")
