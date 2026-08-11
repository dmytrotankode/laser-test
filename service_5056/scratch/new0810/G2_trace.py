"""Канавка, шаг 2: устойчивая трассировка вместо поиска по столбцам.

Разведка (G1) показала, что борозда видна - на боковых видах она читается
непрерывно, включая вырез уха. Но поиск минимума в каждом столбце независимо
даёт срывы: на куполе есть швы и тени, которые локально темнее, и точка
перескакивает на них.

Здесь используется то, что канавка - НЕПРЕРЫВНАЯ линия: соседние столбцы не
могут отличаться на сотни пикселей. Ищется путь через изображение, который
одновременно идёт по тёмному и не прыгает. Это обычное динамическое
программирование по столбцам, без обучения и без подгонки под ответ.

Дополнительно линий может быть две (верхняя граница прессования и нижний край
детали), поэтому трассируются обе: сначала лучшая, затем лучшая из оставшихся
на удалении от неё.
"""
import os
import sys
import json
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(HERE, 'G2_out')
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import dataset  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

JUMP = 6            # на сколько строк путь может сместиться между соседними столбцами
STEP = 4            # прореживание по горизонтали, для скорости


def band(img):
    blur = cv2.GaussianBlur(img, (21, 21), 0)
    body = blur > max(60, int(np.percentile(blur, 60)))
    rows = np.where(body.sum(1) > img.shape[1] * 0.06)[0]
    cols = np.where(body.sum(0) > img.shape[0] * 0.02)[0]
    if len(rows) < 10 or len(cols) < 10:
        return None
    top, bot = int(rows.min()), int(rows.max())
    return top + int((bot - top) * 0.45), bot, int(cols.min()), int(cols.max())


def darkness_map(img, y0, y1, x0, x1):
    strip = cv2.GaussianBlur(img[y0:y1, x0:x1], (9, 9), 0).astype(np.float32)
    up = np.roll(strip, 25, axis=0)
    dn = np.roll(strip, -25, axis=0)
    d = np.minimum(up - strip, dn - strip)
    d[:30, :] = -999
    d[-30:, :] = -999
    return d[:, ::STEP]


def trace(D, forbid=None):
    """Путь максимальной суммарной темноты с ограничением на скачок между столбцами."""
    H, Wc = D.shape
    score = D.copy()
    if forbid is not None:
        for c in range(Wc):
            lo, hi = max(forbid[c] - 60, 0), min(forbid[c] + 60, H)
            score[lo:hi, c] = -999
    back = np.zeros((H, Wc), np.int32)
    idx = np.arange(H)
    for c in range(1, Wc):
        prev = score[:, c - 1]
        best = prev.copy()
        arg = idx.copy()
        for s in range(1, JUMP + 1):
            # np.roll(prev, s)[i] == prev[i - s], значит предок строки i это i - s
            for sh, src in ((np.roll(prev, s), idx - s), (np.roll(prev, -s), idx + s)):
                m = sh > best
                best[m] = sh[m]
                arg[m] = src[m]
        score[:, c] += best
        back[:, c] = np.clip(arg, 0, H - 1)
    path = np.zeros(Wc, np.int32)
    path[-1] = int(np.argmax(score[:, -1]))
    for c in range(Wc - 1, 0, -1):
        path[c - 1] = back[path[c], c]
    return path


def groove(img):
    b = band(img)
    if b is None:
        return None
    y0, y1, x0, x1 = b
    D = darkness_map(img, y0, y1, x0, x1)
    p1 = trace(D)
    p2 = trace(D, forbid=p1)
    xs = x0 + np.arange(D.shape[1]) * STEP
    s1 = D[p1, np.arange(D.shape[1])]
    s2 = D[p2, np.arange(D.shape[1])]
    lines = [(y0 + p1, s1), (y0 + p2, s2)]
    lines.sort(key=lambda t: np.median(t[0]))        # верхняя первой
    return xs, lines


print()
print("Трассировка канавки: две линии, верхняя и нижняя")
print("=" * 74)
print(f"{'вариант':<9}{'вид':<7}{'верхняя: глубина':>18}{'нижняя: глубина':>18}"
      f"{'разрыв, px':>13}")
print("-" * 74)

res = {}
for v in dataset.TRAIN + dataset.HELDOUT + dataset.BLIND:
    for view in ('back', 'left'):
        p = os.path.join(BASE, 'input', 'archive', v, f'{view}.png')
        if not os.path.exists(p):
            continue
        img = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
        g = groove(img)
        if g is None:
            continue
        xs, lines = g
        (yu, su), (yl, sl) = lines
        res[f'{v}_{view}'] = dict(x=xs.tolist(), upper=yu.tolist(),
                                  lower=yl.tolist(),
                                  s_upper=su.tolist(), s_lower=sl.tolist())
        if v in ('v1', 'v13', 'v20', 'v25'):
            print(f"{v:<9}{view:<7}{np.median(su):>18.0f}{np.median(sl):>18.0f}"
                  f"{np.median(yl - yu):>13.0f}")
            vis = cv2.cvtColor(cv2.resize(img, (1024, 750)), cv2.COLOR_GRAY2BGR)
            for x, y in zip(xs, yu):
                cv2.circle(vis, (x // 4, y // 4), 1, (0, 0, 255), -1)
            for x, y in zip(xs, yl):
                cv2.circle(vis, (x // 4, y // 4), 1, (255, 200, 0), -1)
            cv2.putText(vis, f'{v} {view}', (8, 26), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 255, 0), 2)
            cv2.imwrite(os.path.join(OUT, f'{v}_{view}.png'), vis)

json.dump(res, open(os.path.join(HERE, 'G2_lines.json'), 'w'))
print(f"\nнайдено линий для {len(res)} снимков, картинки в G2_out/")
print("красным - верхняя линия, синим - нижняя")
