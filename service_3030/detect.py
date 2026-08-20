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

По разметке заказчика (bench.py, пять снимков) выяснилось, что его рука стоит на
ЧЕТВЁРТОМ месте - `edge_lo`, нижний край полосы, где тень переходит в светлый
наплыв. Дно тени для этого не годится: от снимка к снимку оно отстоит от руки на
18-37 px, то есть всё, что отсчитано от него, гуляет вместе с ним. Поэтому край
ищется своим путём: широкое окно находит полосу, мелкий масштаб ставит точку.

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
    min_depth=5,      # ниже этой глубины дно борозды считается ненадёжным
    min_contrast=12,  # перепад яркости на краю, ниже которого точка ненадёжна
    refine=35,        # в каком окне вокруг полосы искать самую крутую точку, px
    fine=2.0,         # масштаб сглаживания при поиске крутизны, px
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


def band_edge_cost(strip, win):
    """Согласованный фильтр на НИЖНИЙ край тёмной полосы.

    Ровно то место, где стоит рука заказчика: над ним тень борозды, под ним
    светлый наплыв. Значение - перепад яркости через окно `win`, в единицах
    яркости, поэтому им же можно мерить надёжность точки.

    Верхний край полосы даёт такой же перепад, но с обратным знаком, и в
    максимум не попадает. Швы и переплетение ткани тоньше окна и дают отклик
    заметно слабее, чем полоса шириной в десятки пикселей.
    """
    k = max(int(win), 3)
    box = cv2.blur(strip, (1, k))              # среднее по k строкам
    half = k // 2 + 1
    below = np.roll(box, -half, axis=0)
    above = np.roll(box, half, axis=0)
    e = below - above
    e[:k + 5, :] = -1e4
    e[-(k + 5):, :] = -1e4
    return e


def refine_edge(strip, path, r, sigma):
    """Уточнить край: самая крутая точка перепада рядом с найденной полосой.

    Широкое окно надёжно находит саму полосу, но ставит точку в середину
    перехода - отсюда постоянный недолёт в десяток пикселей. Рука заказчика
    стоит там, где яркость растёт круче всего, а это мелкий масштаб. Искать
    крутизну по всему кадру нельзя, её хватает и на переплетении ткани;
    поэтому - только в окрестности уже найденной полосы.
    """
    g = np.gradient(cv2.GaussianBlur(strip, (0, 0), float(sigma)), axis=0)
    H, W = strip.shape
    out = np.array(path, np.int32).copy()
    for c in range(W):
        a = max(int(path[c]) - r, 0)
        b = min(int(path[c]) + r + 1, H)
        if b - a < 3:
            continue
        out[c] = a + int(np.argmax(g[a:b, c]))
    return out


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

    # Край наплыва ищется своим путём, а не отступом от дна тени: дно само
    # гуляет от снимка к снимку на десятки пикселей, и всё, что от него
    # отсчитано, гуляет вместе с ним.
    E = band_edge_cost(strip, int(p['win']))
    ep = trace(E, int(p['jump']))
    ep = refine_edge(strip, ep, max(int(p['refine']), 4), float(p['fine']))
    cols = np.arange(E.shape[1])
    contrast = E[ep, cols]
    depth = D[path, cols]

    xs = x0 + np.arange(D.shape[1]) * int(p['step'])
    k = int(p['smooth'])
    return dict(
        x=xs.tolist(),
        center=(y0 + smooth_line(path, k)).tolist(),
        upper=(y0 + smooth_line(up, k)).tolist(),
        lower=(y0 + smooth_line(lo, k)).tolist(),
        edge_lo=(y0 + smooth_line(ep, k)).tolist(),
        depth=depth.tolist(),
        contrast=contrast.tolist(),
        ok=(contrast > float(p['min_contrast'])).tolist(),
        params=p,
    )


def profile_at(img, x, y, half=80):
    """Яркость поперёк линии в точке - чтобы видеть, где на самом деле дно."""
    x = int(np.clip(x, 0, img.shape[1] - 1))
    y0 = int(np.clip(y - half, 0, img.shape[0] - 1))
    y1 = int(np.clip(y + half, 0, img.shape[0]))
    col = cv2.GaussianBlur(img, (7, 7), 0)[y0:y1, x]
    return dict(y0=y0, values=col.astype(int).tolist())
