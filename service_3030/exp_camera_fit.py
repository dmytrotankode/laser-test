"""Где стоят камеры: калибровка по записанным программам, без доски.

Доска ChArUco провалилась (PLAN §15: RMS 2.2-2.9 px, дисторсия мусор) - A4 с
квадратом 27 мм слишком мала для 75 мм объектива на 2.5 м. Но калибровочный
объект у нас уже есть: РОБОТ САМ записал сотни точных координат на поверхности
шлема. `.LS` - это путь сопла, а `lsgeom.cut_surface` переводит его в место, куда
садится луч, с учётом отступа и наклона 15°.

Итого на каждый вариант: трёхмерная кривая в координатах станка (UFRAME 2) и она
же, размеченная на снимке. Камера одна для всех вариантов, значит каждый вариант
- независимое уравнение на одни и те же числа камеры.

ЧТО ВЫЯСНИЛОСЬ ПРИ ПЕРВОМ ЗАХОДЕ. Отпускать все параметры сразу нельзя. Кольцо
реза почти плоское (286 x 262 мм при разбросе по высоте 42 мм), и фокус с
расстоянием на такой мишени меняются согласованно, давая ту же картинку:
свободная подгонка поставила камеру на 0.49 м с фокусом 1413 px и "отступом
сгиба" -188 мм. Поэтому фокус берётся закреплённым из лазерной пробы §4e
(22656 px для back, 22767 для left) - она меряет его независимо, и обе камеры
дали почти одно число, как и положено одинаковым объективам.

Свободными остаются поза камеры (6 чисел) и один общий отступ `d` вдоль оси
инструмента: линия сгиба идёт не по резу, а выше него на срезаемую юбку.

Соответствие точек не нужно: обе стороны - кривые, невязка меряется от
размеченной точки до ПРОЕКЦИИ кривой (точка-отрезок).

Дисциплина: подгонка только по dataset.TRAIN; v6/v13 держатся для проверки.
service_5056 только читается.

    python exp_camera_fit.py
"""
import os
import sys
import json
import numpy as np
import cv2
from scipy.optimize import least_squares

BASE = os.path.dirname(os.path.abspath(__file__))
S5056 = os.path.abspath(os.path.join(BASE, '..', 'service_5056'))
NEW0810 = os.path.join(S5056, 'scratch', 'new0810')
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(S5056, 'scripts'))

import line_features                                    # noqa: E402
import dataset                                          # noqa: E402
import fit_model                                        # noqa: E402
import lsgeom                                           # noqa: E402
from bench import dist_to_polyline                      # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

IMG_W, IMG_H = 4096, 3000
MM_PER_PX = 0.09
LASER_CAMS = os.path.join(NEW0810, 'L4_cameras.json')

_RING = {}


def ring(variant, extra):
    """Линия реза варианта, сдвинутая вдоль оси инструмента ещё на `extra` мм.

    Точки и оси инструмента считаются один раз: внутри оптимизатора меняется
    только `extra`, а пересчёт cut_surface на каждом шаге съедал всё время.
    """
    if variant not in _RING:
        prog = fit_model.program(variant)
        P, ids = lsgeom.cut_ring(prog)
        _RING[variant] = (np.asarray(P, float),
                          np.asarray(lsgeom.tool_axes(prog, ids), float))
    P, ax = _RING[variant]
    return P - (fit_model.standoff(variant) + extra) * ax


def project(X, rvec, C, f):
    """Дырочная камера в координатах станка; соглашение как в L4_rays.

    `C` - центр камеры, главная точка в середине кадра, дисторсии нет.
    """
    R = cv2.Rodrigues(np.asarray(rvec, float))[0]
    Xc = (np.asarray(X, float) - np.asarray(C, float)) @ R.T
    z = np.maximum(Xc[:, 2], 1e-6)
    return np.c_[f * Xc[:, 0] / z + IMG_W / 2, f * Xc[:, 1] / z + IMG_H / 2], Xc[:, 2]


def near_arc(uv, z):
    """Ближняя половина кольца: дальняя к камере не повёрнута.

    Берётся самый длинный непрерывный кусок по кольцу, иначе проекция дальней
    половины притягивала бы к себе размеченные точки.
    """
    m = z < np.median(z)
    n = len(m)
    best = cur = start = bs = 0
    for i in range(2 * n):
        if m[i % n]:
            if cur == 0:
                start = i
            cur += 1
            if cur > best:
                best, bs = cur, start
        else:
            cur = 0
    return uv[[(bs + i) % n for i in range(min(best, n))]]


def residuals(p, view, variants, marks, f):
    """Расхождение проекции кольца с ручной разметкой, px."""
    out = []
    for v in variants:
        uv, z = project(ring(v, p[6]), p[:3], p[3:6], f)
        out.append(np.abs(dist_to_polyline(marks[v][view], near_arc(uv, z))))
    return np.concatenate(out)


def fit(view, variants, marks):
    """Поза камеры и отступ сгиба; фокус и старт - из лазерной пробы §4e."""
    cam = json.load(open(LASER_CAMS, encoding='utf-8'))[view]
    f = cam['focus']
    r = least_squares(residuals, np.r_[cam['x'][:6], 20.0],
                      args=(view, variants, marks, f), method='lm', max_nfev=300)
    return r.x, f, np.array(cam['x'][:6])


def laser_check(p6, view, f):
    """Объясняет ли эта камера лазерные пятна - данные, ничего не знающие о сгибе.

    Мера - кратчайшее расстояние между лучом робота и лучом зрения, сразу в мм.
    """
    sys.path.insert(0, NEW0810)
    import L4_rays                                       # noqa: E402
    return L4_rays.gap_mm(np.asarray(p6, float), L4_rays.observations(view), f)


def main():
    marks = line_features.load_marks()
    train = [v for v in dataset.TRAIN if v != 'v2']
    held = list(dataset.HELDOUT)
    print(f'Подгонка по {len(train)} вариантам, проверка на {", ".join(held)}\n')
    for v in train + held:
        fit_model.standoff(v)

    for view in ('back',):
        p, f, x4e = fit(view, train, marks)
        print(f'--- {view}: фокус закреплён {f:.0f} px')
        print(f'    отступ «сгиб выше реза»: {p[6]:+.1f} мм')
        print(f'    отклонение от решения §4e: {np.linalg.norm(p[3:6] - x4e[3:6]):.0f} мм, '
              f'{np.degrees(np.linalg.norm(p[:3] - x4e[:3])):.2f}°')
        for label, names in (('обучающие', train), ('held-out', held)):
            q = residuals(p, view, names, marks, f)
            print(f'    {label:10s} медиана {np.median(q):5.1f} px = '
                  f'{np.median(q) * MM_PER_PX:.2f} мм, p90 {np.percentile(q, 90):5.1f} px')
        print(f'    лазерные пятна, мм: §4e  {np.round(laser_check(x4e, view, f), 2)}')
        print(f'                        наша {np.round(laser_check(p[:6], view, f), 2)}')


if __name__ == '__main__':
    main()
