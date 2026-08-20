"""Насколько автоматическая линия расходится с ручной. Честная мера.

Раньше расхождение считалось по вертикали при одном x: брали y детектора и y
эталона в той же колонке. Там, где линия идёт полого, это почти то же самое, что
и настоящее расстояние. А у уха, где она валится почти отвесно, вертикаль
завышает ошибку в полтора-два раза, и сам эталон перестаёт быть функцией от x -
две разные точки линии стоят в одной колонке. Именно на этом участке и решается,
работает детектор или нет, поэтому мерить его неправильно нельзя.

Здесь расстояние берётся до ЛОМАНОЙ эталона (до ближайшего отрезка), со знаком:
плюс - линия детектора ниже эталона по кадру.

Запуск:  python bench.py            все размеченные снимки, все кандидаты
"""
import os
import sys
import json
import glob
import numpy as np
import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import detect                                   # noqa: E402
from shots import LINES, MM_PER_PX, img_path, mark_name   # noqa: E402

CANDIDATES = ('upper', 'center', 'lower', 'edge_lo')


def load_marks():
    """Ручная разметка: снимок, ломаная, плотная её версия и нормали."""
    out = []
    for f in sorted(glob.glob(os.path.join(LINES, '*.json'))):
        pts = json.load(open(f, encoding='utf-8')).get('points', [])
        if len(pts) < 3:
            continue
        stem = os.path.basename(f)[:-5]
        variant, view = mark_name(stem)
        p = img_path(variant, view)
        img = cv2.imread(p, cv2.IMREAD_GRAYSCALE) if os.path.exists(p) else None
        if img is None:
            print(f'!! снимок не найден, разметка {stem} пропущена: {p}')
            continue
        out.append(dict(name=stem, view=view, img=img,
                        ref=np.array(pts, float)))
    return out


def dist_to_polyline(P, R):
    """Расстояние от каждой точки P до ломаной R, со знаком (плюс = ниже).

    Знак берётся по нормали ближайшего отрезка, развёрнутой вниз по кадру.
    """
    A, B = R[:-1], R[1:]
    AB = B - A
    L2 = (AB ** 2).sum(1)
    L2[L2 == 0] = 1e-9
    AP = P[:, None, :] - A[None, :, :]
    t = np.clip((AP * AB[None]).sum(2) / L2[None], 0, 1)
    proj = A[None] + t[:, :, None] * AB[None]
    dv = P[:, None, :] - proj
    d = np.hypot(dv[:, :, 0], dv[:, :, 1])
    j = np.argmin(d, axis=1)
    i = np.arange(len(P))
    n = np.c_[-AB[j][:, 1], AB[j][:, 0]]
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    n[n[:, 1] < 0] *= -1                       # нормаль всегда вниз по кадру
    sign = np.sign((dv[i, j] * n).sum(1))
    return d[i, j] * np.where(sign == 0, 1, sign)


def measure(mark, params=None):
    """Метрики по каждому кандидату + покрытие эталона."""
    res = detect.find_lines(mark['img'], **(params or {}))
    if res is None:
        return None
    xs = np.array(res['x'], float)
    ok = np.array(res['ok'], bool)
    ref = mark['ref']
    # считаем только там, где эталон вообще размечен
    inside = (xs >= ref[:, 0].min()) & (xs <= ref[:, 0].max())
    mm = MM_PER_PX.get(mark['view'], 0.09)
    out = {}
    for key in CANDIDATES:
        y = np.array(res[key], float)
        for tag, use in (('всё', inside), ('где уверен', inside & ok)):
            if use.sum() < 10:
                continue
            d = dist_to_polyline(np.c_[xs[use], y[use]], ref)
            a = np.abs(d)
            out[(key, tag)] = dict(
                n=int(use.sum()), med=float(np.median(a)),
                p90=float(np.percentile(a, 90)),
                bias=float(np.median(d)), mm=mm,
                within10=float(np.mean(a <= 10)),
                cover=float(use.sum() / max(inside.sum(), 1)))
    return out


def report(params=None, marks=None):
    marks = marks if marks is not None else load_marks()
    print(f'размечено снимков: {len(marks)} — '
          f"{', '.join(m['name'] for m in marks)}\n")
    rows = {}
    for m in marks:
        r = measure(m, params)
        if r is None:
            print(f"!! {m['name']}: деталь на снимке не найдена")
            continue
        rows[m['name']] = r
    for key in CANDIDATES:
        print(f'--- {key}')
        print(f"    {'снимок':<16}{'выборка':<12}{'медиана':>9}{'мм':>7}"
              f"{'p90':>8}{'в 10px':>8}{'смещение':>10}{'покрытие':>10}")
        for name, r in rows.items():
            for tag in ('всё', 'где уверен'):
                s = r.get((key, tag))
                if not s:
                    continue
                print(f'    {name:<16}{tag:<12}{s["med"]:>9.1f}'
                      f'{s["med"] * s["mm"]:>7.2f}{s["p90"]:>8.1f}'
                      f'{s["within10"] * 100:>7.0f}%{s["bias"]:>+10.1f}'
                      f'{s["cover"] * 100:>9.0f}%')
        print()
    return rows


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    report()
