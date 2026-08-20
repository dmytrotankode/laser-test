"""Одна камера, два независимых источника: лазерные пятна и линия сгиба.

Порознь каждый источник слаб. Пятен всего 7 на `back` при шести неизвестных -
запас в одно уравнение, проверять почти нечем. Разметка сгиба даёт сотни точек,
но тянет за собой неизвестный отступ «сгиб выше реза», который подменяет собой
позу камеры. Вместе они друг друга держат: пятна фиксируют дальность и масштаб,
разметка - ориентацию.

КАК ЗДЕСЬ МЕРЯЕТСЯ ОШИБКА (это важнее самой подгонки)

* всё в МИЛЛИМЕТРАХ НА ДЕТАЛИ, ничего в пикселях. Пиксель переводится точно, по
  глубине точки и фокусу (px * Z / f), а не через общий множитель 0.09 мм/px:
  тот верен только для одной дальности и на боковых ракурсах врёт;
* у источников разный вес. Если просто склеить остатки, 400 точек разметки
  задавят 7 пятен и «совместная» подгонка окажется подгонкой по разметке.
  Поэтому каждый источник нормируется на свой объём, и отдельно печатается,
  что будет при других весах - если вывод от веса зависит, он ненадёжен;
* критерий - только ПРЕДСКАЗАНИЕ невиданного:
    - пятно, исключённое из подгонки (протокол §4e),
    - вариант, чья разметка в подгонке не участвовала;
* контроль на самообман: разметка одного варианта против кольца ДРУГОГО. Кривые
  тут все гладкие и похожие, и если такая пара сойдётся не хуже правильной,
  значит согласие ни о чём не говорит.

service_5056 только читается, ничего не пишется.

    python exp_camera_joint.py
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
sys.path.insert(0, NEW0810)

import line_features                                    # noqa: E402
import dataset                                          # noqa: E402
import fit_model                                        # noqa: E402
from bench import dist_to_polyline                      # noqa: E402
from exp_camera_fit import ring, project, near_arc, LASER_CAMS, IMG_W, IMG_H  # noqa: E402

class _Mute:                       # модуль при импорте печатает свой отчёт
    def write(self, *_):
        return 0

    def flush(self):
        pass

    def reconfigure(self, **_):
        pass


_real, sys.stdout = sys.stdout, _Mute()
import L4_rays                                           # noqa: E402
sys.stdout = _real

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def line_error_mm(p, view, variants, marks, f):
    """Расхождение проекции кольца с разметкой, переведённое в мм НА ДЕТАЛИ.

    Перевод точный: смещение в пикселях умножается на глубину точки и делится на
    фокус. Общий множитель мм/px для этого не годится - он верен лишь для одной
    дальности.
    """
    out = []
    for v in variants:
        X = ring(v, p[6])
        uv, z = project(X, p[:3], p[3:6], f)
        d_px = np.abs(dist_to_polyline(marks[v][view], near_arc(uv, z)))
        out.append(d_px * float(np.median(z)) / f)
    return np.concatenate(out)


def spot_error_mm(p, view, f, keep=None):
    """Кратчайшее расстояние луч робота <-> луч зрения, мм (протокол §4e)."""
    obs = L4_rays.observations(view)
    if keep is not None:
        obs = [o for i, o in enumerate(obs) if i in keep]
    return L4_rays.gap_mm(np.asarray(p[:6], float), obs, f)


def fit(view, variants, marks, f, x0, w_line=1.0, w_spot=1.0, spots=None):
    """Совместная подгонка. Вес каждого источника делится на корень из объёма."""
    def resid(p):
        a = line_error_mm(p, view, variants, marks, f)
        b = spot_error_mm(p, view, f, spots)
        return np.concatenate([w_line * a / np.sqrt(len(a)),
                               w_spot * b / np.sqrt(len(b))])
    return least_squares(resid, x0, method='lm', max_nfev=400).x


def report(view='back'):
    marks = line_features.load_marks()
    train = [v for v in dataset.TRAIN if v != 'v2']
    held = list(dataset.HELDOUT)
    for v in train + held:
        fit_model.standoff(v)
    cam = json.load(open(LASER_CAMS, encoding='utf-8'))[view]
    f = cam['focus']
    x0 = np.r_[cam['x'][:6], 10.0]
    n_spots = len(L4_rays.observations(view))

    print(f'=== камера {view}: фокус {f:.0f} px (закреплён из §4e), '
          f'{len(train)} вариантов разметки + {n_spots} лазерных пятен\n')

    p = fit(view, train, marks, f, x0)
    print(f'Совместное решение: отступ «сгиб выше реза» {p[6]:+.1f} мм')
    print(f'   остаток на разметке  медиана {np.median(line_error_mm(p, view, train, marks, f)):.2f} мм')
    print(f'   остаток на пятнах    медиана {np.median(spot_error_mm(p, view, f)):.2f} мм, '
          f'макс {np.max(spot_error_mm(p, view, f)):.2f}')

    print('\n1. Предсказание пятна, исключённого из подгонки (протокол §4e):')
    errs = []
    for i in range(n_spots):
        keep = set(range(n_spots)) - {i}
        q = fit(view, train, marks, f, x0, spots=keep)
        e = float(spot_error_mm(q, view, f, {i})[0])
        errs.append(e)
        print(f'   пятно {i + 1}: {e:6.2f} мм')
    print(f'   медиана {np.median(errs):.2f} мм   (у §4e по тому же протоколу '
          f'0.18-7.76, медиана 0.88)')

    print('\n2. Предсказание разметки варианта, не участвовавшего в подгонке:')
    errs2 = []
    for v in train:
        rest = [u for u in train if u != v]
        q = fit(view, rest, marks, f, x0)
        e = float(np.median(line_error_mm(q, view, [v], marks, f)))
        errs2.append(e)
    print(f'   по 13 вариантам: медиана {np.median(errs2):.2f} мм, '
          f'худший {np.max(errs2):.2f} мм')
    e_held = [float(np.median(line_error_mm(p, view, [v], marks, f))) for v in held]
    print(f'   held-out {", ".join(held)}: ' + ', '.join(f'{e:.2f} мм' for e in e_held))

    print('\n3. Контроль: разметка одного варианта против кольца другого')
    own = np.median([np.median(line_error_mm(p, view, [v], marks, f)) for v in train])
    wrong = []
    for i, v in enumerate(train):
        u = train[(i + 5) % len(train)]
        X = ring(u, p[6])
        uv, z = project(X, p[:3], p[3:6], f)
        d = np.abs(dist_to_polyline(marks[v][view], near_arc(uv, z)))
        wrong.append(float(np.median(d)) * float(np.median(z)) / f)
    print(f'   своя пара {own:.2f} мм против чужой {np.median(wrong):.2f} мм — '
          f'{"различает" if np.median(wrong) > 3 * own else "НЕ РАЗЛИЧАЕТ, замер пустой"}')

    print('\n4. Чувствительность к весу источников (вывод не должен от него зависеть):')
    for wl, ws in ((1, 1), (3, 1), (1, 3), (10, 1), (1, 10)):
        q = fit(view, train, marks, f, x0, w_line=wl, w_spot=ws)
        print(f'   вес разметка:пятна {wl:>2}:{ws:<2}  отступ {q[6]:+6.1f} мм   '
              f'разметка {np.median(line_error_mm(q, view, train, marks, f)):.2f} мм   '
              f'пятна {np.median(spot_error_mm(q, view, f)):.2f} мм   '
              f'камера сместилась на {np.linalg.norm(q[3:6] - p[3:6]):.0f} мм')


if __name__ == '__main__':
    report('back')
