"""Подбор линии и параметров по разметке заказчика.

До сих пор детектор настраивался на глаз, и вывод "легла точно" оказался
неверным. Здесь у него появляется объективная мера: линия, размеченная руками
в интерфейсе 3030, и расхождение с ней в пикселях и миллиметрах.

Перебираются все три кандидата (верхняя граница тени, дно борозды, нижняя
граница) на сетке параметров. Отдельно печатается, что получается на КАЖДОМ
размеченном снимке - потому что подобрать под один и обрадоваться легко, а
интерес представляет то, что переносится на другие.
"""
import os
import sys
import json
import glob
import itertools
import numpy as np
import cv2

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import detect  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ARCHIVE = os.path.abspath(os.path.join(BASE, '..', 'service_5056', 'input', 'archive'))
MM = {'back': 0.09, 'left': 0.082, 'top': 0.12}

GRID = dict(
    win=[10, 15, 25, 40],
    edge=[0.2, 0.35, 0.5, 0.7],
    band_lo=[0.35, 0.45, 0.6],
    jump=[3, 6, 12],
)


def load_marks():
    out = []
    for f in sorted(glob.glob(os.path.join(BASE, 'data', 'lines', '*.json'))):
        d = json.load(open(f, encoding='utf-8'))
        pts = sorted(d.get('points', []), key=lambda q: q[0])
        if len(pts) < 3:
            continue
        name = os.path.basename(f)[:-5]
        variant, view = name.rsplit('_', 1)
        img = cv2.imread(os.path.join(ARCHIVE, variant, f'{view}.png'),
                         cv2.IMREAD_GRAYSCALE)
        out.append(dict(name=name, view=view, img=img,
                        px=np.array([q[0] for q in pts], float),
                        py=np.array([q[1] for q in pts], float)))
    return out


def score(mark, params):
    res = detect.find_lines(mark['img'], **params)
    if res is None:
        return None
    xs = np.array(res['x'], float)
    ok = np.array(res['ok'], bool)
    inside = (xs >= mark['px'].min()) & (xs <= mark['px'].max())
    use = inside & ok
    if use.sum() < 10:
        return None
    ref = np.interp(xs[use], mark['px'], mark['py'])
    out = {}
    for key in ('upper', 'center', 'lower'):
        d = np.array(res[key], float)[use] - ref
        out[key] = dict(med=float(np.median(np.abs(d))),
                        p90=float(np.percentile(np.abs(d), 90)),
                        bias=float(np.median(d)),
                        cover=float(use.sum() / max(inside.sum(), 1)))
    return out


marks = load_marks()
print(f"размечено снимков: {len(marks)} — {', '.join(m['name'] for m in marks)}")

keys = list(GRID)
combos = [dict(zip(keys, c)) for c in itertools.product(*(GRID[k] for k in keys))]
print(f"перебор {len(combos)} комбинаций параметров\n")

rows = []
for p in combos:
    per = {}
    for m in marks:
        s = score(m, p)
        if s is None:
            per = None
            break
        per[m['name']] = s
    if per:
        rows.append((p, per))

print("Лучшее по СРЕДНЕЙ медиане расхождения на всех размеченных снимках")
print("=" * 88)
print(f"{'линия':<14}{'win':>5}{'edge':>6}{'band':>6}{'jump':>6}"
      f"{'медиана px':>12}{'мм':>7}{'p90 px':>9}{'покрытие':>10}")
print("-" * 88)
best = {}
for key in ('upper', 'center', 'lower'):
    scored = []
    for p, per in rows:
        med = np.mean([per[n][key]['med'] for n in per])
        p90 = np.mean([per[n][key]['p90'] for n in per])
        cov = np.mean([per[n][key]['cover'] for n in per])
        scored.append((med, p90, cov, p, per))
    scored.sort(key=lambda t: t[0])
    med, p90, cov, p, per = scored[0]
    best[key] = (p, per)
    mm = np.mean([MM[m['view']] for m in marks])
    print(f"{key:<14}{p['win']:>5}{p['edge']:>6}{p['band_lo']:>6}{p['jump']:>6}"
          f"{med:>12.1f}{med * mm:>7.2f}{p90:>9.1f}{cov * 100:>9.0f}%")

print()
print("Как та же настройка ложится на каждый снимок по отдельности")
print("=" * 88)
for key in ('upper', 'center', 'lower'):
    p, per = best[key]
    print(f"\n{key} (win={p['win']}, edge={p['edge']}, band={p['band_lo']}, "
          f"jump={p['jump']}):")
    for m in marks:
        s = per[m['name']][key]
        mm = MM[m['view']]
        print(f"   {m['name']:<12} медиана {s['med']:>6.1f} px = {s['med'] * mm:>5.2f} мм"
              f"   p90 {s['p90']:>6.1f}   смещение {s['bias']:>+7.1f} px"
              f"   покрытие {s['cover'] * 100:>3.0f}%")

json.dump({k: dict(params=v[0], per={n: v[1][n][k] for n in v[1]})
           for k, v in best.items()},
          open(os.path.join(BASE, 'data', 'tuned.json'), 'w'), indent=1)
print("\nсохранено в data/tuned.json")
