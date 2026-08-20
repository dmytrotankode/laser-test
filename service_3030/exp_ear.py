"""Сколько стоит ухо: что будет, если исключить его из подгонки.

Худшая точка и у разметки, и у подгонки садится на крутой спуск у уха - там,
где линия плохо видна и где заказчик размечает по догадке. Вопрос простой:
этот участок помогает найти позу или только вносит шум?

Ухо определяется по геометрии разметки, а не на глаз: участок, где линия круто
падает (|dy/dx| выше порога). Никакой ручной вырезки координат.
"""
import sys
import numpy as np
import cv2
from scipy.optimize import least_squares
sys.path.insert(0, '../service_5056/scripts')
import lsgeom, features as f5                            # noqa: E402
import export_ls as X, exp_camera_fit as E               # noqa: E402
import line_features, dataset, fit_model                 # noqa: E402
from bench import dist_to_polyline                       # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MASTER = [v for v in dataset.TRAIN if v != 'v2'] + ['v6', 'v13', 'v20']
OTHER = ['v21', 'v24', 'v25']
STEEP = 0.5

marks = line_features.load_marks()
train = [v for v in dataset.TRAIN if v != 'v2']
cams = X.cameras()


def flat_part(m):
    """Точки разметки вне крутого спуска."""
    g = np.gradient(m[:, 1]) / np.maximum(np.abs(np.gradient(m[:, 0])), 1e-6)
    return m[np.abs(g) < STEEP]


def solve(v, nb, drop_ear):
    ref = E.ring(nb, X.FOLD_OFFSET)

    def r(p6):
        R = cv2.Rodrigues(p6[:3])[0]
        Y = ref @ R.T + p6[3:6]
        out = []
        for w in ('back', 'left'):
            pc, f = cams[w]
            uv, z = E.project(Y, pc[:3], pc[3:6], f)
            m = X.resample(marks[v][w])
            if drop_ear and w == 'left':
                m = X.resample(flat_part(m))
            out.append(np.abs(dist_to_polyline(m, E.near_arc(uv, z)))
                       * float(np.median(z)) / f)
        return np.concatenate(out)
    return least_squares(r, np.zeros(6), method='lm', max_nfev=300).x


share = []
for v in MASTER + OTHER:
    m = X.resample(marks[v]['left'])
    share.append(1 - len(flat_part(m)) / len(m))
print(f'на крутой спуск приходится {100 * np.mean(share):.0f}% точек разметки left\n')

for drop in (False, True):
    acc = {}
    for v in MASTER + OTHER:
        pool = [u for u in train if u != v]
        for u in pool + [v]:
            fit_model.standoff(u)
        nb = fit_model.nearest(v, pool, f5.load(pool + [v]), 'prof')
        p = solve(v, nb, drop)
        R = cv2.Rodrigues(p[:3])[0]
        d = lsgeom.curve_distance(E.ring(nb, 0.0) @ R.T + p[3:6], E.ring(v, 0.0))
        acc[v] = (d.mean(), d.max(), 100 * np.mean(d <= 2))
    label = 'без уха' if drop else 'с ухом '
    for name, group in (('мастер', MASTER), ('чужие', OTHER)):
        a = np.array([acc[v] for v in group])
        print(f'{label} {name:<8} среднее {a[:, 0].mean():5.2f}  макс {a[:, 1].mean():5.2f}  '
              f'в допуске {a[:, 2].mean():4.0f}%')
    if drop:
        for v in OTHER:
            print(f'         {v}: макс {acc[v][1]:.2f} мм, в допуске {acc[v][2]:.0f}%')
    print(flush=True)
