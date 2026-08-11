"""Поиск линии границы прессования на снимке шлема.

У края детали идёт тёмная полоса - тень в борозде, которая остаётся на границе
прессованной зоны. Оператор, по словам заказчика, ориентируется именно на неё.

Полоса широкая, десятки пикселей, и у неё есть ТРИ разных кандидата на роль
"линии", отстоящих друг от друга на миллиметры:

    upper   верхняя граница тени - где начинается затенение;
    center  самое тёмное место, дно борозды;
    lower   нижняя граница - где тень кончается и начинается наплыв.

Какая из них тот самый ориентир - вопрос к человеку, поэтому считаются все три
и показываются одновременно.

Устойчивость обеспечивается тем, что линия НЕПРЕРЫВНА: соседние столбцы не могут
разойтись на сотни пикселей. Ищется путь через изображение, который идёт по
тёмному и при этом не прыгает (динамическое программирование по столбцам).
Поиск максимума в каждом столбце по отдельности этого не даёт - он срывается на
швы и тени купола, что и произошло в первой версии.
"""
import numpy as np
import cv2

DEFAULTS = dict(
    band_lo=0.45,     # верх полосы поиска, доля высоты детали сверху
    band_hi=1.00,     # низ полосы поиска
    win=25,           # на сколько px вверх/вниз сравнивать яркость, ища борозду
    jump=6,           # максимальный сдвиг линии между соседними столбцами, px
    step=4,           # прореживание по горизонтали
    edge=0.5,         # доля глубины, по которой определяются края полосы
    smooth=9,         # сглаживание итоговой линии, столбцов
    min_depth=5,      # ниже этой глубины точка считается ненадёжной
)


def body_box(img):
    """Прямоугольник детали: она заметно светлее фона."""
    blur = cv2.GaussianBlur(img, (21, 21), 0)
    thr = max(60, int(np.percentile(blur, 60)))
    body = blur > thr
    rows = np.where(body.sum(1) > img.shape[1] * 0.06)[0]
    cols = np.where(body.sum(0) > img.shape[0] * 0.02)[0]
    if len(rows) < 10 or len(cols) < 10:
        return None
    return int(rows.min()), int(rows.max()), int(cols.min()), int(cols.max())


def darkness(img, y0, y1, x0, x1, win, step):
    """Насколько пиксель темнее того, что выше и ниже него на `win`."""
    strip = cv2.GaussianBlur(img[y0:y1, x0:x1], (9, 9), 0).astype(np.float32)
    up = np.roll(strip, win, axis=0)
    dn = np.roll(strip, -win, axis=0)
    d = np.minimum(up - strip, dn - strip)
    d[:win + 5, :] = -1e4
    d[-(win + 5):, :] = -1e4
    return d[:, ::step], strip[:, ::step]


def trace(D, jump):
    """Путь максимальной суммарной темноты с ограничением на скачок."""
    H, W = D.shape
    score = D.copy()
    back = np.zeros((H, W), np.int32)
    idx = np.arange(H)
    for c in range(1, W):
        prev = score[:, c - 1]
        best = prev.copy()
        arg = idx.copy()
        for s in range(1, jump + 1):
            # np.roll(prev, s)[i] == prev[i-s], значит предок строки i это i-s
            for sh, src in ((np.roll(prev, s), idx - s), (np.roll(prev, -s), idx + s)):
                m = sh > best
                best[m] = sh[m]
                arg[m] = src[m]
        score[:, c] += best
        back[:, c] = np.clip(arg, 0, H - 1)
    path = np.zeros(W, np.int32)
    path[-1] = int(np.argmax(score[:, -1]))
    for c in range(W - 1, 0, -1):
        path[c - 1] = back[path[c], c]
    return path


def edges_of_band(strip, path, edge, win):
    """Верх и низ тёмной полосы вокруг найденного дна."""
    H, W = strip.shape
    up = np.zeros(W, np.int32)
    lo = np.zeros(W, np.int32)
    for c in range(W):
        y = int(path[c])
        col = strip[:, c]
        a, b = max(y - 3 * win, 0), min(y + 3 * win, H)
        around = col[a:b]
        if len(around) < 5:
            up[c] = lo[c] = y
            continue
        base = float(np.percentile(around, 85))     # яркость вне тени
        level = col[y] + (base - col[y]) * edge     # где тень наполовину сошла
        i = y
        while i > a and col[i] < level:
            i -= 1
        up[c] = i
        i = y
        while i < b - 1 and col[i] < level:
            i += 1
        lo[c] = i
    return up, lo


def smooth_line(y, k):
    if k < 3:
        return y
    k = int(k) | 1
    pad = np.pad(y.astype(np.float32), (k // 2, k // 2), mode='edge')
    ker = np.ones(k, np.float32) / k
    return np.convolve(pad, ker, mode='valid')


def find_lines(img, **kw):
    """Три линии полосы плюс мера надёжности каждой точки."""
    p = dict(DEFAULTS)
    p.update({k: v for k, v in kw.items() if v is not None})
    box = body_box(img)
    if box is None:
        return None
    top, bot, x0, x1 = box
    h = bot - top
    y0 = top + int(h * float(p['band_lo']))
    y1 = min(top + int(h * float(p['band_hi'])), img.shape[0])
    if y1 - y0 < 60:
        return None

    D, strip = darkness(img, y0, y1, x0, x1, int(p['win']), int(p['step']))
    path = trace(D, int(p['jump']))
    up, lo = edges_of_band(strip, path, float(p['edge']), int(p['win']))
    depth = D[path, np.arange(D.shape[1])]

    xs = x0 + np.arange(D.shape[1]) * int(p['step'])
    k = int(p['smooth'])
    return dict(
        x=xs.tolist(),
        center=(y0 + smooth_line(path, k)).tolist(),
        upper=(y0 + smooth_line(up, k)).tolist(),
        lower=(y0 + smooth_line(lo, k)).tolist(),
        depth=depth.tolist(),
        ok=(depth > float(p['min_depth'])).tolist(),
        params=p,
    )


def profile_at(img, x, y, half=80):
    """Яркость поперёк линии в точке - чтобы видеть, где на самом деле дно."""
    x = int(np.clip(x, 0, img.shape[1] - 1))
    y0 = int(np.clip(y - half, 0, img.shape[0] - 1))
    y1 = int(np.clip(y + half, 0, img.shape[0]))
    col = cv2.GaussianBlur(img, (7, 7), 0)[y0:y1, x]
    return dict(y0=y0, values=col.astype(int).tolist())
