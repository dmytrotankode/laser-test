"""Проверка двух признаков, которые Safe Zone сейчас выбрасывает.

Нынешний вектор - центр масс и радиальный профиль маски ПОСЛЕ отсечки. Два числа
на вид при этом теряются, и оба, судя по замерам 10.08, несут информацию:

  верх купола (абсолютная строка кадра). Устойчив: по архиву разброс 2-6 px, тогда
    как низ силуэта гуляет на десятки. Несёт положение детали и, в отличие от cy,
    не зависит от длины юбки;

  низ силуэта (край необрезанного кевлара). Сейчас считается помехой - именно из-за
    него отсечка ползёт по куполу. Но замер показал: у новых деталей купол на месте,
    а низ уходит на 8-15 мм, то есть это свойство КОНКРЕТНОЙ детали. Возможно, оно
    предсказывает, где оператор поставит рез - тогда это признак, а не помеха.

Проверяются по отдельности и вместе, критерий прежний: LOO внутри TRAIN той же
функцией fit_model.loo_error. Признаки берутся из уже посчитанного s4_skirt.json
(штатная сегментация), held-out и слепые наборы не читаются.

Масштабирование: добавляемые числа - пиксели, как и всё остальное в векторе, так
что отдельная нормировка не нужна - fit_pairs делит на разброс сам.
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
SKIRT = json.load(open(os.path.join(HERE, 's4_skirt.json')))

names = dataset.guard_training(dataset.TRAIN)
BASEF = features.load(names)
for v in names:
    fit_model.transform_from_ref(v, ANCHOR)
POSE = {(x, y): fit_model.pose_between(x, y, PIVOT, ANCHOR)
        for x in names for y in names if x != y}


def extended(add_top, add_bottom):
    """Копия признаков с дописанными числами в конец профиля первого вида."""
    out = {}
    for v in names:
        e = {k: [list(r) for r in rows] for k, rows in BASEF[v].items()}
        tail = []
        for view in ('back', 'left'):
            if add_top:
                tail.append(float(SKIRT[f'{v}/{view}']['top']))
            if add_bottom:
                tail.append(float(SKIRT[f'{v}/{view}']['bottom']))
        e['prof'][0] = list(e['prof'][0]) + tail
        out[v] = e
    return out


print()
print("LOO внутри TRAIN, мм. Что добавляем к нынешним 150 признакам")
print("=" * 68)
print(f"{'набор признаков':<38}{'среднее':>10}{'худший':>10}")
print("-" * 68)

for label, F in (
        ("нынешний (150)", BASEF),
        ("+ верх купола (back, left)", extended(True, False)),
        ("+ низ силуэта (back, left)", extended(False, True)),
        ("+ оба", extended(True, True)),
):
    per = fit_model.loo_error(names, F, KIND, LAM, POSE, PIVOT)
    nn = np.array([per[v]['nearest'] for v in names])
    print(f"{label:<38}{nn.mean():>10.2f}{nn.max():>10.2f}")

print()
print("Отдельно: несёт ли низ силуэта информацию о позе (архив, один шлем)")
print("-" * 68)
Z = {v: fit_model.pose_between(ANCHOR, v, PIVOT, ANCHOR) for v in names}
for view in ('back', 'left'):
    b = np.array([SKIRT[f'{v}/{view}']['bottom'] for v in names])
    for i, ax in enumerate(('X', 'Y', 'Z', 'roll', 'pitch', 'yaw')):
        z = np.array([Z[v][i] for v in names])
        r = np.corrcoef(b, z)[0, 1]
        if abs(r) > 0.5:
            print(f"  {view}: низ силуэта против {ax}: корреляция {r:+.2f}")
print("  (показаны только связи сильнее 0.5; если пусто - низ силуэта позу не видит)")
