"""Какая функция потерь годится: чужой шлем отличается ФОРМОЙ, а не только позой.

Минимакс на мастер-шлеме помогает, а на чужих ломает подгонку: он заставляет
обслуживать участок, который несовместим по форме. Устойчивая потеря должна,
наоборот, такой участок игнорировать. Проверяем три варианта на одних и тех же
наборах и смотрим ОТДЕЛЬНО по мастер-шлему и по чужим - агрегат уже один раз
это различие спрятал.
"""
import sys
import numpy as np
import cv2
from scipy.optimize import least_squares, minimize
sys.path.insert(0, '../service_5056/scripts')
import lsgeom, features as f5                            # noqa: E402
import export_ls as X, exp_camera_fit as E               # noqa: E402
import line_features, dataset, fit_model                 # noqa: E402
from bench import dist_to_polyline                       # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MASTER = [v for v in dataset.TRAIN if v != 'v2'] + ['v6', 'v13', 'v20']
OTHER = ['v21', 'v24', 'v25']
marks = line_features.load_marks()
train = [v for v in dataset.TRAIN if v != 'v2']
cams = X.cameras()


def resid_fn(v, nb):
    ref = E.ring(nb, X.FOLD_OFFSET)

    def r(p6):
        R = cv2.Rodrigues(p6[:3])[0]
        Y = ref @ R.T + p6[3:6]
        out = []
        for w in ('back', 'left'):
            pc, f = cams[w]
            uv, z = E.project(Y, pc[:3], pc[3:6], f)
            out.append(np.abs(dist_to_polyline(X.resample(marks[v][w]), E.near_arc(uv, z)))
                       * float(np.median(z)) / f)
        return np.concatenate(out)
    return r


def solve(r, mode):
    p = least_squares(r, np.zeros(6), method='lm', max_nfev=300).x
    if mode == 'устойчивая':
        p = least_squares(r, p, loss='soft_l1', f_scale=0.5, max_nfev=300).x
    elif mode == 'минимакс':
        def sm(q, T=0.05):
            a = r(q)
            m = float(np.max(a))
            return m + T * np.log(np.mean(np.exp((a - m) / T)))
        p = minimize(sm, p, method='Powell',
                     options=dict(maxiter=4000, xtol=1e-4, ftol=1e-6)).x
    return p


for mode in ('МНК', 'устойчивая', 'минимакс'):
    acc = {}
    for v in MASTER + OTHER:
        pool = [u for u in train if u != v]
        for u in pool + [v]:
            fit_model.standoff(u)
        nb = fit_model.nearest(v, pool, f5.load(pool + [v]), 'prof')
        p = solve(resid_fn(v, nb), mode)
        R = cv2.Rodrigues(p[:3])[0]
        d = lsgeom.curve_distance(E.ring(nb, 0.0) @ R.T + p[3:6], E.ring(v, 0.0))
        acc[v] = (d.mean(), d.max(), 100 * np.mean(d <= 2))
    for label, group in (('мастер-шлем', MASTER), ('чужие шлемы', OTHER)):
        a = np.array([acc[v] for v in group])
        print(f'{mode:<12}{label:<14} среднее {a[:, 0].mean():5.2f}  '
              f'макс {a[:, 1].mean():5.2f}  в допуске {a[:, 2].mean():4.0f}%')
    print(flush=True)
