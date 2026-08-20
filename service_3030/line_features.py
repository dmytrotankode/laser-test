"""Ручная разметка линии прессования -> числа, сравнимые между снимками.

Признаки 5056 - это центроид силуэта и радиальный профиль, то есть только
ОЧЕРТАНИЕ. Линия прессования интересна тем, что она внутренняя: силуэт к
развороту вокруг оси взгляда почти слеп, а линия - нет.

Камеры закреплены, поэтому линия берётся прямо в пикселях кадра, без нормировки:
высота линии в фиксированных колонках. Приводить её к силуэту нельзя - тогда из
признака уйдёт ровно то, ради чего он нужен, взаимное положение линии и купола.

Сетка колонок общая для всех вариантов и лежит внутри размеченного участка
самого короткого из них - иначе край сетки пришлось бы экстраполировать.
"""
import os
import json
import glob
import numpy as np

from shots import LINES, mark_name

N_COLS = 24                       # сколько отсчётов высоты берём с каждого ракурса
VIEWS = ('back', 'left')          # на top линия сгиба не видна


def load_marks():
    """{вариант: {ракурс: массив точек}} из data/lines."""
    out = {}
    for f in sorted(glob.glob(os.path.join(LINES, '*.json'))):
        pts = json.load(open(f, encoding='utf-8')).get('points', [])
        if len(pts) < 3:
            continue
        variant, view = mark_name(os.path.basename(f)[:-5])
        p = np.array(sorted(pts, key=lambda q: q[0]), float)
        out.setdefault(variant, {})[view] = p
    return out


def common_grid(marks, variants):
    """Колонки, размеченные у ВСЕХ вариантов сразу."""
    grid = {}
    for view in VIEWS:
        lo = max(marks[v][view][0, 0] for v in variants)
        hi = min(marks[v][view][-1, 0] for v in variants)
        if hi - lo < 100:
            raise ValueError(f'{view}: общий размеченный участок пуст ({lo}..{hi})')
        grid[view] = np.linspace(lo, hi, N_COLS)
    return grid


def vector(marks, variant, grid):
    """Высота линии в колонках сетки: N_COLS чисел на ракурс."""
    out = []
    for view in VIEWS:
        p = marks[variant][view]
        out.append(np.interp(grid[view], p[:, 0], p[:, 1]))
    return np.concatenate(out)


def build(variants):
    """{вариант: вектор признаков линии} плюс сама сетка."""
    marks = load_marks()
    missing = [v for v in variants if any(w not in marks.get(v, {}) for w in VIEWS)]
    if missing:
        raise ValueError(f'нет разметки: {", ".join(missing)}')
    grid = common_grid(marks, variants)
    return {v: vector(marks, v, grid) for v in variants}, grid
