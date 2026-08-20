"""Четыре способа получить траекторию реза - на одних данных и одной мерой.

Сравнивать по отдельности бессмысленно: у каждого способа свой протокол, и
цифры между собой не сходятся. Здесь всё считается одинаково.

    1. сосед как есть          что было бы без всякой поправки
    2. модель 5056             нынешний рабочий метод, матрица 150x6
    3. поза по линии + сосед   поправка из двух снимков, форма от соседа
    4. поза по линии + CAD     поправка из двух снимков, форма из модели -
                               БИБЛИОТЕКИ В ПУТИ НЕТ ВООБЩЕ

Мера - `lsgeom.curve_distance` до записанной оператором линии реза, в мм.
Печатаются среднее, максимум и доля точек в допуске 2 мм. Для реза решает
максимум и доля, а не среднее - это выяснилось на глаз раньше цифр.

ЧЕСТНОСТЬ

* камеры считались по разметке обучающих вариантов, поэтому их числа
  оптимистичны. Чистые - `v6`, `v13` (held-out) и `v20`, `v21`, `v24`, `v25`
  (слепые, в подгонке камер не участвовали). Таблица разделена;
* `v22`, `v23` не трогаются: последняя нетронутая проверка;
* для способа 2 матрица обучается без проверяемого варианта;
* выборка перекошена (мастер-шлем против чужих), поэтому итоги считаются
  ОТДЕЛЬНО по группам. Общий агрегат уже дважды прятал провал на чужих.

ПРО ЦЕЛЬ СРАВНЕНИЯ. Записанная линия реза сама выведена из пути сопла вычитанием
подобранного отступа, то есть не измерена. Совпадение кромки CAD с ней требует
поправки отступа +1.16 мм (exp_scale_or_standoff), поэтому для способа 4
печатается и то, и другое: против стандартной цели и против поправленной.
"""
import os
import sys
import json
import numpy as np
import cv2
from scipy.optimize import least_squares

BASE = os.path.dirname(os.path.abspath(__file__))
S5056 = os.path.abspath(os.path.join(BASE, '..', 'service_5056'))
S2020 = os.path.abspath(os.path.join(BASE, '..', 'service_2020'))
sys.path.insert(0, BASE)
sys.path.insert(0, S2020)
sys.path.insert(0, os.path.join(S5056, 'scripts'))

import lsgeom                                            # noqa: E402
import dataset                                           # noqa: E402
import features as f5                                    # noqa: E402
import fit_model                                         # noqa: E402
import scene as S                                        # noqa: E402
import line_features                                     # noqa: E402
import export_scene as XS                                # noqa: E402
import export_ls as X                                    # noqa: E402
import exp_cad_fit as F                                  # noqa: E402
import exp_camera_fit as E                               # noqa: E402
from bench import dist_to_polyline                       # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TRAIN = [v for v in dataset.TRAIN if v != 'v2']
CLEAN = ['v6', 'v13', 'v20', 'v21', 'v24', 'v25']
MASTER = set(TRAIN) | {'v6', 'v13', 'v20'}
STANDOFF_FIX = 1.16          # exp_scale_or_standoff
PIVOT = np.array([1170.98, 785.15, -191.86])


def stat(d):
    return d.mean(), d.max(), 100 * float(np.mean(d <= 2))


def cad_start():
    p = os.path.join(S2020, 'data', 'scenes', 'v1', 'scene.json')
    with open(p, encoding='utf-8') as f:
        pl = json.load(f)['meshes'][0]['placement']
    T = np.array(S.placement_matrix(pl['rot_deg'], pl['translate'], pl['scale']))
    return T[:3, :3], T[:3, 3]


def radial(P):
    """Наружу от оси купола: вдоль этого направления сгиб отстоит от реза.

    Оси инструмента отклонены от вертикали на 55-76 градусов, то есть почти
    горизонтальны, поэтому радиальное направление - хорошее их приближение, а
    своих осей у модели нет.
    """
    c = P.mean(0)
    v = P - c
    v[:, 2] = 0
    return v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-9)


# Смещение от реза к сгибу, замеренное на самой линии реза (v1, отступ 2.3 мм):
# 2.17 мм внутрь по радиусу и 0.68 вверх, разброс по кольцу 0.07 и 0.15 мм.
# Задаётся ЖЁСТКО, а не подбирается.
#
# Подбирать его нельзя, хотя сперва так и было сделано: купол выпуклый, поэтому
# сдвиг модели вдоль её оси почти неотличим от раздувания кромки по радиусу.
# Параметр оказался вырожден с позой и ушёл в +0.07 мм вместо известных 2.3,
# а его роль забрал вертикальный сдвиг - то есть модель садилась не туда, зато
# с красивой невязкой.
FOLD_RADIAL, FOLD_UP = -2.17, +0.68


def pose_cad(variant, rim, marks, cams, R0, t0):
    """Поза модели по разметке сгиба на двух снимках. Смещение сгиба закреплено."""
    nrm = radial(rim)
    off = FOLD_RADIAL * nrm
    off[:, 2] += FOLD_UP

    def resid(p):
        R = cv2.Rodrigues(p[:3])[0] @ R0
        fold = (rim + off) @ R.T + t0 + p[3:6]
        out = []
        for w in ('back', 'left'):
            pc, f = cams[w]
            uv, z = E.project(fold, pc[:3], pc[3:6], f)
            d = np.abs(dist_to_polyline(X.resample(marks[variant][w]), E.near_arc(uv, z)))
            out.append(d * float(np.median(z)) / f)
        return np.concatenate(out)

    r = least_squares(resid, np.zeros(6), method='lm', max_nfev=600)
    R = cv2.Rodrigues(r.x[:3])[0] @ R0
    return rim @ R.T + t0 + r.x[3:6], float(np.median(np.abs(r.fun))), float(np.max(np.abs(r.fun)))


def model_5056(variant, F_all, POSE):
    """Предсказание нынешней модели: k-NN сосед плюс матрица 150x6."""
    pool = [u for u in TRAIN if u != variant]
    W, sx = fit_model.fit_pairs(pool, F_all, 'prof', 100, POSE)
    nb = fit_model.nearest(variant, pool, F_all, 'prof')
    p = fit_model.predict(W, sx, F_all, 'prof', nb, variant)
    return fit_model.apply_pose(E.ring(nb, 0.0), p, PIVOT), nb


def main():
    marks = line_features.load_marks()
    rim = XS.mesh_rim(F.STL)
    cams = X.cameras()
    R0, t0 = cad_start()
    every = TRAIN + CLEAN
    for v in every:
        fit_model.standoff(v)
    F_all = f5.load(every)
    ref = TRAIN[0]
    for v in TRAIN:
        fit_model.transform_from_ref(v, ref)
    POSE = {(a, b): fit_model.pose_between(a, b, PIVOT, ref)
            for a in TRAIN for b in TRAIN if a != b}

    rows = {}
    folds = []
    for v in every:
        own = E.ring(v, 0.0)
        own_fix = E.ring(v, STANDOFF_FIX)
        pool = [u for u in TRAIN if u != v]
        nb = fit_model.nearest(v, pool, F_all, 'prof')
        r = {}
        r['1 сосед как есть'] = stat(lsgeom.curve_distance(E.ring(nb, 0.0), own))
        try:
            pred, _ = model_5056(v, F_all, POSE)
            r['2 модель 5056'] = stat(lsgeom.curve_distance(pred, own))
        except Exception as e:
            r['2 модель 5056'] = (np.nan, np.nan, np.nan)
        R, t, _ = X.pose_from_line(v, nb, marks, cams)
        r['3 линия + сосед'] = stat(lsgeom.curve_distance(E.ring(nb, 0.0) @ R.T + t, own))
        P, d, res = pose_cad(v, rim, marks, cams, R0, t0)
        folds.append(d)
        r['4 линия + CAD'] = stat(lsgeom.curve_distance(P, own))
        r['4 то же, отступ поправлен'] = stat(lsgeom.curve_distance(P, own_fix))
        rows[v] = r
        print(f'  {v} посчитан (сосед {nb}, остаток на снимках {d:.2f} мм)', flush=True)

    keys = ['1 сосед как есть', '2 модель 5056', '3 линия + сосед',
            '4 линия + CAD', '4 то же, отступ поправлен']
    print('\nПодобранный отступ сгиба по всем вариантам: '
          f'{np.mean(folds):+.2f} ± {np.std(folds):.2f} мм '
          f'(независимая оценка тех же 2-3 мм — самопроверка)')

    for label, group in (('обучающие (камеры их видели, числа оптимистичны)', TRAIN),
                         ('ЧИСТЫЕ: held-out и слепые', CLEAN)):
        print(f'\n=== {label}')
        print(f"{'способ':<28}{'мастер-шлем: сред/макс/в допуске':>38}"
              f"{'чужие: сред/макс/в допуске':>34}")
        for k in keys:
            a = np.array([rows[v][k] for v in group if v in MASTER])
            b = np.array([rows[v][k] for v in group if v not in MASTER])
            sa = (f'{a[:, 0].mean():>10.2f}/{a[:, 1].mean():<7.2f}{a[:, 2].mean():>6.0f}%'
                  if len(a) else f'{"":>24}')
            sb = (f'{b[:, 0].mean():>10.2f}/{b[:, 1].mean():<7.2f}{b[:, 2].mean():>6.0f}%'
                  if len(b) else f'{"—":>24}')
            print(f'{k:<28}{sa:>38}{sb:>34}')

    print('\nПо каждому варианту, максимум в мм:')
    print(f"{'вариант':<8}" + ''.join(f'{k[:16]:>18}' for k in keys))
    for v in every:
        print(f'{v:<8}' + ''.join(f'{rows[v][k][1]:>18.2f}' for k in keys))


if __name__ == '__main__':
    main()
