"""Наскрізна перевірка на РЕАЛЬНІЙ розмітці оператора (набори nabir-1005-001/002 = 05.10).

1. Результат Методу 3 (data/generated/<набір>_method3.LS) проти правильного .LS набору
   (archive/<набір>/ground_truth.ls) - відстань кожної точки до ЛІНІЇ правди, мм.
2. Розмітка оператора проти проекції правильної лінії різу на те саме фото - мм на
   деталі (знак: + = розмітка далі від центру шолома на фото / вище). Показує, скільки
   похибки дає саме розмітка, і чи є систематичний зсув (лінія згину vs лінія різу).
3. Ті самі варіанти підгонки, що в exp_marks_views.py, але на РЕАЛЬНІЙ розмітці:
   жорстко (Метод 3) / + вигин K=2 / + top (top - поки ідеальний, з правди: верхня межа).

    python eval_real_marks.py
"""
import json
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

BASE = os.path.dirname(os.path.abspath(__file__))
S21 = os.path.join(BASE, '..', 'service_2021')
sys.path.insert(0, S21)
sys.path.insert(0, BASE)
import ls_points  # noqa: E402
from pipeline import contour_fit, camera_model as CM  # noqa: E402
import exp_marks_views as X  # noqa: E402

SETS = ('nabir-1005-001', 'nabir-1005-002')


def ring(p):
    return np.array([q[2] for q in ls_points.read_ring(p)])


def line_dist(P, truth):
    return cKDTree(X.dense(truth)).query(P)[0]


def report(tag, d):
    print(f'  {tag:34s} середня {d.mean():.2f}, 90% {np.percentile(d, 90):.2f}, макс {d.max():.2f} мм, <1мм {np.mean(d < 1) * 100:.0f}%, <2мм {np.mean(d < 2) * 100:.0f}%')


if __name__ == '__main__':
    for n in SETS:
        truth = ring(os.path.join(S21, 'archive', n, 'ground_truth.ls'))
        print(f'=== {n}')
        m3 = ring(os.path.join(S21, 'data', 'generated', f'{n}_method3.LS'))
        report('Метод 3 у сервісі', line_dist(m3, truth))
        report('еталон 1010_1 як є (без підгонки)', line_dist(X.REF, truth))

        marks = {}
        for w in ('back', 'left'):
            m = np.array(json.load(open(os.path.join(S21, 'lines', f'{n}_{w}.json'), encoding='utf-8'))['points'], float)
            marks[w] = contour_fit.resample(m, 150)
            vis, z = X.visible(truth, w)
            vis = contour_fit.resample(vis, 300)
            mm = float(np.median(z)) / X.cams[w][1]
            d = CM.dist_to_polyline(marks[w], vis) * mm
            print(f'  розмітка {w:4s} проти проекції правди: середня |d| {np.abs(d).mean():.2f} мм, '
                  f'зі знаком {d.mean():+.2f}, макс {np.abs(d).max():.2f}; точок {len(m)}')
        for views, K, tag in ((('back', 'left'), 0, 'офлайн: back+left жорстко'),
                              (('back', 'left'), 2, 'офлайн: back+left + вигин'),
                              (('back', 'left', 'top'), 0, 'офлайн: + top(ідеальний)'),
                              (('back', 'left', 'top'), 2, 'офлайн: + top(ідеальний) + вигин')):
            mk = dict(marks)
            if 'top' in views:
                mk['top'] = X.marks_of(truth, ('top',))['top']
            report(tag, line_dist(X.fit(mk, K), truth))
