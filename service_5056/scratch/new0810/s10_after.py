"""Шаг 6b: что осталось от расхождения после привязки отсечки к верху купола.

Разложение то же, что в s3 (центр, размер, форма), но на новых масках. Если
после правки размер силуэта всё равно больше библиотечного, значит дело не в
том, какая часть детали попала в маску, и гипотезу про юбку надо снимать.
"""
import os
import sys
import json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import dataset   # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
F = {k: np.array(v) for k, v in json.load(open(os.path.join(HERE, 's9_feats.json'))).items()}
VIEWS = ('back', 'left', 'top')


def parts(vec):
    return {v: (vec[i * 50], vec[i * 50 + 1], vec[i * 50 + 2:(i + 1) * 50])
            for i, v in enumerate(VIEWS)}


P = {k: parts(v) for k, v in F.items()}

for view in VIEWS:
    cx = np.array([P[v][view][0] for v in dataset.TRAIN])
    cy = np.array([P[v][view][1] for v in dataset.TRAIN])
    rr = np.array([P[v][view][2].mean() for v in dataset.TRAIN])
    print(f"\n--- {view} ---   библиотека: cx {cx.mean():.0f}±{cx.std():.1f}  "
          f"cy {cy.mean():.0f}±{cy.std():.1f}  радиус {rr.mean():.0f}±{rr.std():.1f}")
    print(f"{'':<6}{'cx, σ':>9}{'cy, σ':>9}{'радиус, σ':>11}{'форма %':>10}")
    for v in dataset.BLIND + dataset.HELDOUT:
        a, b, r = P[v][view]
        rn = r / r.mean()
        shape = min(np.abs(rn - P[o][view][2] / P[o][view][2].mean()).mean() * 100
                    for o in dataset.TRAIN)
        print(f"{v:<6}{(a - cx.mean()) / cx.std():>9.1f}"
              f"{(b - cy.mean()) / cy.std():>9.1f}"
              f"{(r.mean() - rr.mean()) / rr.std():>11.1f}{shape:>10.2f}")
    ctl = []
    for i, a in enumerate(dataset.TRAIN):
        ra = P[a][view][2] / P[a][view][2].mean()
        for b in dataset.TRAIN[i + 1:]:
            ctl.append(np.abs(ra - P[b][view][2] / P[b][view][2].mean()).mean() * 100)
    print(f"{'контр.':<6}{'':>29}{np.mean(ctl):>10.2f}  <- среднее внутри библиотеки")
