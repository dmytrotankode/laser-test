"""Масштаб модели или ошибка отступа? Это разные вещи с разными следствиями.

Подгонка кромки CAD к линии реза стабильно просит масштаб 1.007-1.008 на всех
вариантах. Соблазнительно записать это в «шлем больше модели на 0.8 %». Но у
нас нет измеренной линии реза: она выводится из пути сопла вычитанием отступа
вдоль оси инструмента, а сам отступ ПОДОБРАН (`lsgeom.fit_standoff`), и в §4e
подгонка отступа другим способом дала 1.2 мм против рабочих 10.

А оси инструмента почти горизонтальны (55-76 градусов от вертикали), поэтому
ошибка отступа меняет РАДИУС кольца почти один к одному: 1 мм отступа - это
0.95 мм радиуса, то есть 0.7 %. Наши 0.8 % - это 1.2 мм отступа.

Различить их можно: масштаб растягивает всё пропорционально, а отступ ещё и
поднимает кольцо (+0.30 мм на мм) и делает это неравномерно, раз углы осей
разные. Поэтому здесь сравниваются четыре подгонки на одних и тех же данных:

    только поза | поза + масштаб | поза + отступ | поза + оба

Смотреть надо не только на остаток, но и на СОГЛАСОВАННОСТЬ параметра между
вариантами: у мастер-шлема отступ должен быть примерно одинаковым, если это
свойство оснастки, а не случайность подгонки.

Ничего не пишет, service_5056 только читается.
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
import fit_model                                         # noqa: E402
import scene as S                                        # noqa: E402
import export_scene as X                                 # noqa: E402
import exp_cad_fit as F                                  # noqa: E402
import exp_camera_fit as E                               # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

VARIANTS = ['v1', 'v3', 'v8', 'v13', 'v20', 'v21', 'v24', 'v25']
MASTER = {'v1', 'v3', 'v8', 'v13', 'v20'}


def start_pose():
    """Стартовое положение - выставленное руками в 2020.

    Из нуля стартовать нельзя: слепая подгонка уже дважды укладывала модель
    вверх дном при неплохой невязке.
    """
    p = os.path.join(S2020, 'data', 'scenes', 'v1', 'scene.json')
    with open(p, encoding='utf-8') as f:
        pl = json.load(f)['meshes'][0]['placement']
    T = np.array(S.placement_matrix(pl['rot_deg'], pl['translate'], pl['scale']))
    return T[:3, :3], T[:3, 3]


def fit(rim, variant, R0, t0, free_scale, free_standoff):
    def resid(p):
        R = cv2.Rodrigues(p[:3])[0] @ R0
        s = p[6] if free_scale else 1.0
        d = p[7] if free_standoff else 0.0
        cut = E.ring(variant, d)
        P = (rim * s) @ R.T + t0 + p[3:6]
        return np.r_[lsgeom.curve_distance(P, cut), lsgeom.curve_distance(cut, P)]

    r = least_squares(resid, np.r_[np.zeros(6), 1.0, 0.0], method='lm', max_nfev=800)
    R = cv2.Rodrigues(r.x[:3])[0] @ R0
    s = r.x[6] if free_scale else 1.0
    d = r.x[7] if free_standoff else 0.0
    P = (rim * s) @ R.T + t0 + r.x[3:6]
    e = lsgeom.curve_distance(P, E.ring(variant, d))
    return e, s, d


def main():
    rim = X.mesh_rim(F.STL)
    R0, t0 = start_pose()
    for v in VARIANTS:
        fit_model.standoff(v)

    cases = [('только поза', False, False), ('+ масштаб', True, False),
             ('+ отступ', False, True), ('+ оба', True, True)]
    print(f"{'вариант':<7}{'шлем':<9}" + ''.join(f'{c[0]:>22}' for c in cases))
    acc = {c[0]: [] for c in cases}
    par = {c[0]: [] for c in cases}
    for v in VARIANTS:
        row = []
        for name, fs, fd in cases:
            e, s, d = fit(rim, v, R0, t0, fs, fd)
            acc[name].append((e.mean(), e.max()))
            par[name].append((s, d))
            row.append(f'{e.mean():>10.2f}/{e.max():<11.2f}')
        print(f"{v:<7}{'мастер' if v in MASTER else 'чужой':<9}" + ''.join(row))

    print('\nПодобранные параметры:')
    for name, _, _ in cases:
        s = np.array([p[0] for p in par[name]])
        d = np.array([p[1] for p in par[name]])
        a = np.array(acc[name])
        print(f'  {name:<14} масштаб {s.mean():.4f} ± {s.std():.4f}   '
              f'отступ {d.mean():+.2f} ± {d.std():.2f} мм   '
              f'остаток сред {a[:, 0].mean():.2f}, макс {a[:, 1].mean():.2f}')

    print('\nЧитать так: если "+ отступ" объясняет столько же, сколько "+ масштаб", '
          '\nто модель не мала - это наша линия реза смещена, и поправка имеет '
          '\nфизический смысл. Если "+ оба" заметно лучше обоих - работают оба, '
          '\nи разделить их на этих данных нельзя.')


if __name__ == '__main__':
    main()
