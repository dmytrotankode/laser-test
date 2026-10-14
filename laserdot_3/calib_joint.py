"""Спільна калібровка трьох камер за маркерними точками 30.09 (основний метод).

Чому не лише calib_rays.py (промені по кожній камері окремо): у top вісь
інструмента на маківці майже паралельна променю зору - «перетин двох прямих»
там майже нічого не обмежує, і підгонка сідала в рішення, де точка за 18-36 мм
від сопла (на back/left - стабільно ~10.5 мм). Повтори точок на top розходились
на 4-6 мм.

Тут кожна точка - одна спільна 3D-позиція для всіх камер:
    точка = сопло + t * (вісь інструмента),  t ~ 10.5 мм (м'який пріор ±2 мм)
і всі три камери підганяються разом за відхиленням у пікселях (переведеним у мм
на деталі). Невідомі: 3 пози камер + t для кожної точки. Фокуси закріплені:
відстань і фокус по цих даних нерозрізнені (перевірено - вільний фокус лише
міняє одне на інше).

    python calib_joint.py           -> підгонка + перевірка виключенням
    python calib_joint.py --save    -> + запис у service_2021/calib/cameras/marker_2026-09-30/
"""
import json
import os
import sys

import numpy as np
from scipy.optimize import least_squares

import calib_rays as C

BASE = C.BASE
OUT_DIR = os.path.join(BASE, '..', 'service_2021', 'calib', 'cameras', 'marker_2026-09-30')
T0, SIG = 10.5, 2.0   # відступ точки від сопла вздовж осі, мм


def load():
    px = json.load(open(os.path.join(BASE, 'pixels.json'), encoding='utf-8'))
    return px, {n['label']: n for n in C.nozzles()}


def dot3d(n, t):
    d = n['dir'] / np.linalg.norm(n['dir'])
    return n['pos'] + t * d


def gather(px, skip=None):
    obs = [(v, lab, np.asarray(uv, float)) for v in C.VIEWS for lab, uv in px[v].items()
           if (v, lab) != skip]
    return obs, sorted({o[1] for o in obs})


def err_mm(cam, v, n, t, uv):
    f = C.FOCUS[v]
    q, z = C.project(cam, f, dot3d(n, t)[None])
    return (q[0] - uv) * z[0] / f


def fit(px, N, cams0, skip=None):
    obs, labs = gather(px, skip)

    def unpack(x):
        return {v: x[6 * i:6 * i + 6] for i, v in enumerate(C.VIEWS)}, dict(zip(labs, x[18:]))

    def res(x):
        cams, t = unpack(x)
        out = [err_mm(cams[v], v, N[l], t[l], uv) for v, l, uv in obs]
        return np.r_[np.concatenate(out), [(t[l] - T0) / SIG * 0.3 for l in labs]]

    x0 = np.r_[np.concatenate([cams0[v] for v in C.VIEWS]), np.full(len(labs), T0)]
    cams, t = unpack(least_squares(res, x0, method='trf', loss='soft_l1', f_scale=1.0).x)
    return cams, t, obs


def initial(px, N):
    """Старт: back/left - промені (calib_rays.solve); top - фіксований відступ T0."""
    noz = list(N.values())
    cams = {v: C.solve(C.observations(v, px, noz), C.FOCUS[v]) for v in ('back', 'left')}
    o = C.observations('top', px, noz)
    P = np.array([x[1] + T0 * x[2] / np.linalg.norm(x[2]) for x in o])
    uv = np.array([x[3] for x in o])
    f = C.FOCUS['top']
    cams['top'] = least_squares(lambda p: (C.project(p, f, P)[0] - uv).ravel(),
                                C.solve(o, f), method='lm').x
    return cams


def main(save=False):
    px, N = load()
    cams, t, obs = fit(px, N, initial(px, N))
    ts = np.array(list(t.values()))
    print(f'відступ точки від сопла: медіана {np.median(ts):.1f} мм, {ts.min():.1f}..{ts.max():.1f}')
    report = {}
    for v in C.VIEWS:
        e = {l: float(np.linalg.norm(err_mm(cams[v], v, N[l], t[l], uv))) for vv, l, uv in obs if vv == v}
        loo = {}
        for l, uv in px[v].items():
            c2, t2, _ = fit(px, N, cams, skip=(v, l))
            loo[l] = float(np.linalg.norm(err_mm(c2[v], v, N[l], t2.get(l, T0), np.asarray(uv))))
        a, b = np.array(list(e.values())), np.array(list(loo.values()))
        worst = sorted(loo, key=lambda k: -loo[k])[:3]
        print(f'=== {v}: {len(e)} точок, позиція {cams[v][3:6].round(0)}')
        print(f'   остаток медіана {np.median(a):.2f} мм, макс {a.max():.2f}')
        print(f'   ПЕРЕВІРКА виключенням: медіана {np.median(b):.2f}, макс {b.max():.2f}, '
              f'найгірші {[(k, round(loo[k], 2)) for k in worst]}')
        report[v] = dict(points=len(e), resid_median_mm=round(float(np.median(a)), 2),
                         resid_max_mm=round(float(a.max()), 2),
                         loo_median_mm=round(float(np.median(b)), 2), loo_max_mm=round(float(b.max()), 2))
    if save:
        os.makedirs(OUT_DIR, exist_ok=True)
        for v in C.VIEWS:
            np.save(os.path.join(OUT_DIR, f'cam_{v}.npy'), np.r_[cams[v], C.FOCUS[v]].astype(np.float64))
        meta = {
            'created': '2026-10-14',
            'method': 'joint marker calibration of all three cameras (laserdot_3/calib_joint.py): '
                      'each dot = nozzle + t * tool axis, t shared across views (prior 10.5 +- 2 mm), '
                      'reprojection error in mm, fixed focal lengths',
            'source': 'laserdot_3/photos (30.09.2026) + laserdot_3/points_pendant.csv + laserdot_3/pixels.json',
            'format': '[rvec(3), position(3), focal_px] as float64, numpy.save',
            'rig': 'helmet rotated 180 deg, back camera moved to the opposite side, left/top unchanged; '
                   'robot user frame differs from marker_2026-08-21 (~70 mm offset)',
            'quality': report,
            'notes': 'NOT valid for scenes shot before 30.09.2026 (old rig) - those use marker_2026-08-21.',
        }
        json.dump(meta, open(os.path.join(OUT_DIR, 'meta.json'), 'w', encoding='utf-8'),
                  indent=2, ensure_ascii=False)
        print('записано ->', os.path.normpath(OUT_DIR))
    return cams


if __name__ == '__main__':
    main(save='--save' in sys.argv)
