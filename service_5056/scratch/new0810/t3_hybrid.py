"""Тест B: гибрид - пять степеней свободы от k-NN, высота от силуэта.

Основание (t2): подгонка силуэта надёжно даёт ТОЛЬКО Z - наклон регрессии 0.99,
корреляция 0.97, остаток 0.27 мм. По X она сползает в одно место (корреляция
0.10), наклоны не определяет вовсе. Поэтому берётся ровно одна величина, а не
поза целиком - именно попытка взять всё и провалилась в прошлой сессии.

k-NN, наоборот, по Z слеп по построению: в обучающих парах высота почти не
меняется (sigma 0.32 мм), и учиться этой степени свободы не на чем.

Постоянное смещение 3D (+0.20 мм) НЕ калибруется: калибровать его по этим же
шести значило бы подглядеть ответ, а величина всё равно мала на фоне остатка.

Мера - штатная: контур выбранной опоры двигается поправкой и меряется до
настоящей линии реза. Рядом всегда прежний пайплайн и потолок подхода.
"""
import os
import sys
import json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import fit_model   # noqa: E402
import lsgeom      # noqa: E402
import dataset     # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MODEL = json.load(open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8'))
PIVOT, ANCHOR = np.array(MODEL['pivot']), MODEL['anchor']
SESS = json.load(open(os.path.join(HERE, 's6_sessions.json')))
SESS['v20'] = 'run_20260810_125404'
Z3D = {k: v['vec'][2] for k, v in
       json.load(open(os.path.join(HERE, 't2_results.json'))).items()}
CASES = dataset.BLIND + ['v6', 'v13']

for v in CASES + list(MODEL['library']):
    fit_model.transform_from_ref(v, ANCHOR)


def knn_delta(v):
    """Поправка, которую выдал пайплайн, и опора, которую он выбрал."""
    if v in SESS:
        d = json.load(open(os.path.join(BASE, 'results', SESS[v],
                                        'step04_result.json'),
                           encoding='utf-8'))
        return d['etalon'], np.array([d['delta_rel_to_etalon'][k] for k in
                                      ('x_mm', 'y_mm', 'z_mm', 'roll_deg',
                                       'pitch_deg', 'yaw_deg')])
    # v6/v13 через ту же машинерию, что эксплуатация: сосед по признакам, W из модели
    import features
    F = features.load(dataset.TRAIN + [v])
    nb = fit_model.nearest(v, dataset.TRAIN, F, MODEL['feature_kind'])
    P = {(x, y): fit_model.pose_between(x, y, PIVOT, ANCHOR)
         for x in dataset.TRAIN for y in dataset.TRAIN if x != y}
    W, sx = fit_model.fit_pairs(dataset.TRAIN, F, MODEL['feature_kind'],
                                MODEL['lam'], P)
    return nb, fit_model.predict(W, sx, F, MODEL['feature_kind'], nb, v)


def stat(pred, G):
    d = lsgeom.curve_distance(pred, G)
    return d.mean(), d.max(), (d <= 2.0).mean() * 100


print()
print("Гибрид: X/Y/наклоны от k-NN, высота от силуэта")
print("=" * 86)
print(f"{'':<7}{'опора':>6}{'Z: k-NN':>9}{'Z: 3D':>8}{'Z истина':>10}"
      f"{'':<3}{'пайплайн':>10}{'гибрид':>9}{'потолок':>9}{'≤2мм':>13}")
print("-" * 86)

rows = {}
for v in CASES:
    nb, d = knn_delta(v)
    G = fit_model.contour(v)
    ref = fit_model.contour(nb)
    true = fit_model.pose_between(nb, v, PIVOT, ANCHOR)

    # высота опоры относительно якоря, чтобы перевести абсолютный Z из 3D в поправку
    z_nb = fit_model.pose_between(ANCHOR, nb, PIVOT, ANCHOR)[2]
    hyb = d.copy()
    hyb[2] = Z3D[v] - z_nb

    a = stat(fit_model.apply_pose(ref, d, PIVOT), G)
    b = stat(fit_model.apply_pose(ref, hyb, PIVOT), G)
    c = stat(fit_model.apply_pose(ref, true, PIVOT), G)
    rows[v] = (a, b, c)
    print(f"{v:<7}{nb:>6}{d[2]:>9.2f}{hyb[2]:>8.2f}{true[2]:>10.2f}{'':<3}"
          f"{a[0]:>10.2f}{b[0]:>9.2f}{c[0]:>9.2f}"
          f"{a[2]:>7.0f}%→{b[2]:.0f}%")

print("-" * 86)
for grp, names in (('шесть слепых', dataset.BLIND), ('v6, v13', ['v6', 'v13'])):
    m = [np.mean([rows[v][i][0] for v in names]) for i in range(3)]
    mx = [max(rows[v][i][1] for v in names) for i in range(3)]
    print(f"{grp:<16} среднее: пайплайн {m[0]:.2f}  гибрид {m[1]:.2f}  "
          f"потолок {m[2]:.2f}   |   худший максимум: {mx[0]:.2f} / {mx[1]:.2f} / {mx[2]:.2f}")
