"""Відносне суміщення фото згори: «новий шолом проти еталонного шолома» (14.10).

Помилка Методу 3 - переважно в горизонтальній площині (зсув 1-2 мм, поворот 0.3-0.5°,
масштаб 0.5-0.9 %), а саме цю площину найкраще бачить камера згори. Порівняння силуету
згори з 3D-моделлю не спрацювало (модель і край на фото розходяться на 3-7 мм, залежно
від порогу). Тут - порівняння фото з фото: контур нового шолома суміщається з контуром
еталонного шолома ТИМ САМИМ способом (похибки виділення краю однакові й скорочуються).

Перевірка: між 05.10 _1 і _2 правильний відносний рух відомий з їхніх .LS. Проектуємо
обидва правильні кільця в камеру top, знаходимо 2D-перетворення між проекціями -
«правильна відповідь у пікселях»; порівнюємо з тим, що дало суміщення контурів фото.
Похибку рахуємо як розбіжність точок кільця, мм на деталі.

    python exp_top_relative.py
"""
import os
import sys

import cv2
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import exp_top_silhouette as T  # noqa: E402
from pipeline import camera_model as CM  # noqa: E402

pc, f = T.cams['top']


def sim2(p, X, c):
    a, s = p[2], np.exp(p[3])
    R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    return (X - c) @ R.T * s + c + p[:2]


def fit_sim2(A, B, c, robust=True):
    """2D подібність A -> B (зсув, поворот, масштаб) по найближчих точках контуру."""
    tree = cKDTree(B)
    r = least_squares(lambda p: tree.query(sim2(p, A, c))[0], np.zeros(4),
                      loss='soft_l1' if robust else 'linear', f_scale=5.0)
    return r.x


def contour(path, thr):
    os.environ['TOP_THR'] = str(thr)
    T.THR = thr
    c, _ = T.photo_contour(path)
    return T.contour_fit.resample(c, 1500)


if __name__ == '__main__':
    a, b = 'nabir-1005-002', 'nabir-1005-001'       # еталон (відомий) -> новий
    ra = T.ring(os.path.join(T.S21, 'archive', a, 'ground_truth.ls'))
    rb = T.ring(os.path.join(T.S21, 'archive', b, 'ground_truth.ls'))
    ua, za = CM.project(ra, pc[:3], pc[3:6], f)
    ub, zb = CM.project(rb, pc[:3], pc[3:6], f)
    mm = float(np.median(za)) / f
    c = ua.mean(0)
    p_true = fit_sim2(ua, T.dense(np.c_[ub, np.zeros(len(ub))])[:, :2], c, robust=False)
    resid_true = cKDTree(ub).query(sim2(p_true, ua, c))[0].mean() * mm
    print(f'правильний рух у площині фото: зсув {p_true[0]*mm:+.2f}, {p_true[1]*mm:+.2f} мм, поворот {np.degrees(p_true[2]):+.2f}°, '
          f'масштаб {np.exp(p_true[3])*100-100:+.2f}% (що лишається поза 2D-подібністю: {resid_true:.2f} мм - нахил і форма)')
    for thr in (45, 60, 80):
        ca = contour(os.path.join(T.S21, 'archive', a, 'top.png'), thr)
        cb = contour(os.path.join(T.S21, 'archive', b, 'top.png'), thr)
        p = fit_sim2(ca, cb, c)
        d = np.linalg.norm(sim2(p, ua, c) - sim2(p_true, ua, c), axis=1) * mm
        print(f'  поріг {thr}: суміщення фото дало зсув {p[0]*mm:+.2f}, {p[1]*mm:+.2f} мм, поворот {np.degrees(p[2]):+.2f}°, '
              f'масштаб {np.exp(p[3])*100-100:+.2f}% -> розбіжність з правильним рухом: середня {d.mean():.2f}, макс {d.max():.2f} мм')
