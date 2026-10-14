"""Метод 4 (14.10.2026) - Метод 3 + край шолома на фото ЗГОРИ як третій ракурс.

Чому (докладно - laserdot_3/README.md, розділи від 14.10):
  * Метод 3 (еталон, жорстко підігнаний під розмітку back+left) помиляється переважно
    в ГОРИЗОНТАЛЬНІЙ площині - зсув 1-2 мм, поворот 0.3-0.5°, масштаб 0.5-0.9 % -
    бо дві камери збоку/ззаду цих напрямків майже не бачать («кільце ковзає по куполу»).
    Саме горизонтальну площину найкраще бачить камера згори.
  * Розмічати ще й згори - зайва робота оператора. Натомість край шолома на фото згори
    знаходиться автоматично: поруч з проекцією поточної лінії, вздовж нормалей, місце
    найрізкішого перепаду яскравості. Перевірено на 05.10: край згори лежить від
    правильної лінії в середньому за ~1 мм (як і ручна розмітка), з викидами (волокна
    юбки) - тому їх вплив обмежено.
  * НЕ силует 3D-моделі і НЕ поріг яскравості: обидва перевірені й не годяться
    (модель і край на фото розходились на 3-7 мм, поріг різав сам шолом).

Що робить:
  1. Старт - те саме, що Метод 3: еталон з рецепта, 7 параметрів (поворот, зсув,
     масштаб) під розмітку back+left.
  2. Двічі: знайти край згори біля проекції поточної лінії -> підігнати ті самі 7
     параметрів під back + left + край згори.
  3. Опційно (--bend так) - ще плавний вигин еталона (довжина/ширина/висота вух, 2
     гармоніки за кутом навколо шолома, обмежено ±8 мм). На двох наборах 05.10 дав
     змішаний результат - тому за замовчуванням вимкнено.
Одна відмінність від Методу 3 у нев'язці: «лінія -> розмітка» не рахується для точок
лінії, найближчих до КІНЦІВ розмітки (5 % з кожного боку). Інакше видимі, але не
розмічені оператором ділянки тягнуться до кінця розмітки (з вигином це давало до 7 мм).

СТАТУС - ЕКСПЕРИМЕНТ (14.10). Перевірка на 7 шоломах з відомим правильним .LS
(laserdot_3/eval_methods.py, реальна розмітка, без підглядання у відповідь):
  нові 05.10 (nabir-1005-001/002): Метод 3 1.78/2.08 мм -> Метод 4 1.58/1.45 мм,
    найгірші точки 3.8/5.0 -> 4.0/2.7, частка <2 мм 69/63 % -> 74/80 %;
  старі v21-v25 (стара розстановка): середня майже та сама, <2 мм краще (35 -> 49 %),
    але НАЙГІРШІ точки гірші (5.8 -> 8.5 мм). Причини: на старих шоломах згори видно
    фланець, що стирчить на 3-5 мм за лінію згину (тоді край - не лінія згину), і
    пошук краю часом чіпляється за шов на куполі.
  --top one (край лише «не пускає за силует») і asym - гірші за two (через шви).
  + РОЗТЯГ по довжині/ширині (--stretch так, за замовчуванням з 14.10; загальний масштаб
    тоді ±2 %, розтяг ±3 %): 1005-001 1.44 мм / найгірша 2.74 / <2 мм 86 %,
    1005-002 1.34 / 2.63 / 85 %; по 7 шоломах 2.21 / 5.9 / 59 % (Метод 3: 2.53 / 5.4 / 44 %).
    Найгірші точки на старих v23/v25 - там, де згори фланець і волокна (див. картинку
    «що побачив метод»).

Точки, кути інструмента (W/P/R), підвід/відвід - з еталона; рухаються всі разом.

Контракт: python run.py --variant <ім'я> --in <папка> --out <.LS> --recipe <рецепт> --bend ні|так
Читає з --in: back.png/left.png/top.png, cam_*.npy, marks_back.json, marks_left.json.
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

BASE = os.path.dirname(os.path.abspath(__file__))
SERVICE_ROOT = os.path.abspath(os.path.join(BASE, '..', '..'))
sys.path.insert(0, SERVICE_ROOT)

DEFAULT_REF = os.path.join(SERVICE_ROOT, 'methods', 'method3', 'TOR_XL_1009.LS')
EDGE_SEARCH_PX = 60        # ±60 px вздовж нормалі (~±5 мм на деталі згори)
EDGE_CLIP_MM = 3.0         # далі цього край вважається викидом (волокна) і вже не тягне
END_TRIM = 0.05            # частка розмітки з кожного кінця, де «лінія -> розмітка» не рахується
BEND_HARMONICS = 2
BEND_LIMIT_MM = 8.0


def dense(P, n):
    """Рівномірно передискретизоване замкнене кільце (n точок)."""
    Q = np.r_[P, P[:1]]
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
    t = np.linspace(0, d[-1], n, endpoint=False)
    return np.c_[[np.interp(t, d, Q[:, i]) for i in range(Q.shape[1])]].T


def near_idx(z):
    """Індекси найдовшої суцільної ділянки z < медіани (та сама логіка, що
    camera_model.near_arc, але з індексами)."""
    m = z < np.median(z)
    n = len(m)
    best = cur = start = bs = 0
    for i in range(2 * n):
        if m[i % n]:
            if cur == 0:
                start = i
            cur += 1
            if cur > best:
                best, bs = cur, start
        else:
            cur = 0
    return np.array([(bs + i) % n for i in range(min(best, n))])


def edge_points(img_blur_grads, uv):
    """Для кожної точки замкненої 2D-кривої uv - точка найрізкішого перепаду
    «світле всередині -> темне назовні» вздовж нормалі (край шолома згори)."""
    gx, gy = img_blur_grads
    c = uv.mean(0)
    s = np.arange(-EDGE_SEARCH_PX, EDGE_SEARCH_PX + 1)
    out = []
    for i, p in enumerate(uv):
        t = uv[(i + 1) % len(uv)] - uv[i - 1]
        nrm = np.array([-t[1], t[0]]) / (np.linalg.norm(t) + 1e-9)
        if nrm @ (p - c) < 0:
            nrm = -nrm
        q = p + s[:, None] * nrm
        x = np.clip(q[:, 0], 0, gx.shape[1] - 1).astype(int)
        y = np.clip(q[:, 1], 0, gx.shape[0] - 1).astype(int)
        g = -(gx[y, x] * nrm[0] + gy[y, x] * nrm[1])
        out.append(p + s[int(np.argmax(g))] * nrm)
    return np.array(out)


def save_debug(path, in_dir, cams, marks, edge, start, final):
    """Картинка «що побачив Метод 4» - три фото поруч (обрізані навколо шолома):
    рожева - розмітка оператора, червона - старт (як Метод 3), блакитна - результат;
    згори: зелені точки - знайдений край, який ВРАХОВАНО, помаранчеві - край далі 3 мм
    від результату (вважається викидом - волокна, шов, фланець - і майже не впливає)."""
    from pipeline import camera_model as CM
    tiles = []
    for w in ('back', 'left', 'top'):
        img = cv2.cvtColor(cv2.imread(os.path.join(in_dir, f'{w}.png'), cv2.IMREAD_GRAYSCALE), cv2.COLOR_GRAY2BGR)
        pc, f = cams[w]
        lines = []
        for P, col, th in ((start, (0, 0, 255), 3), (final, (255, 220, 0), 4)):
            uv, z = CM.project(dense(P, 800), pc[:3], pc[3:6], f)
            if w != 'top':
                k = near_idx(z)
                uv = uv[np.sort(k)]
            lines.append(uv)
            for p in uv:
                cv2.circle(img, (int(p[0]), int(p[1])), th, col, -1)
        if w in marks:
            cv2.polylines(img, [marks[w].astype(np.int32)], False, (255, 0, 255), 4)
        if w == 'top':
            uvf, z = CM.project(dense(final, 800), pc[:3], pc[3:6], f)
            mm = float(np.median(z)) / f
            d = cKDTree(uvf).query(edge)[0] * mm
            for p, dd in zip(edge, d):
                cv2.circle(img, (int(p[0]), int(p[1])), 7, (0, 200, 0) if dd <= EDGE_CLIP_MM else (0, 140, 255), -1)
        a = np.vstack(lines)
        x0, y0 = np.maximum(a.min(0) - 200, 0).astype(int)
        x1, y1 = np.minimum(a.max(0) + 200, [img.shape[1], img.shape[0]]).astype(int)
        crop = img[y0:y1, x0:x1]
        crop = cv2.resize(crop, None, fx=1400 / crop.shape[1], fy=1400 / crop.shape[1])
        cv2.putText(crop, w, (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 255, 255), 4)
        tiles.append(crop)
    legend = np.zeros((150, 1400, 3), np.uint8)
    for i, (txt, col) in enumerate((('rozheva: vasha rozmitka   chervona: start (yak Metod 3)   blakytna: rezultat Metodu 4', (255, 255, 255)),
                                    ('zgory: zeleni - znaidenyi krai, vrakhovano;  pomaranchevi - dali 3 mm, ignoruietsia', (255, 255, 255)))):
        cv2.putText(legend, txt, (15, 50 + 60 * i), cv2.FONT_HERSHEY_SIMPLEX, 1.0, col, 2)
    cv2.imwrite(path, np.vstack(tiles + [legend]), [cv2.IMWRITE_JPEG_QUALITY, 85])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--variant', required=True)
    ap.add_argument('--in', dest='in_dir', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--recipe', default='production_2026-08-27')
    ap.add_argument('--bend', default='ні', choices=['ні', 'так'])
    ap.add_argument('--stretch', default='так', choices=['ні', 'так'],
                    help='окремий масштаб уздовж і впоперек шолома (±3 %%): шоломи відрізняються '
                         'пропорціями на 1-2 %%; розтяг уздовж майже не рухає вуха')
    ap.add_argument('--top', default='two', choices=['two', 'one', 'asym'],
                    help='two - край тягне в обидва боки; one - лише не пускає лінію ЗА край '
                         '(фланець може стирчати назовні - тоді край не лінія згину); '
                         'asym - назовні тягне не більше ніж на 1.5 мм')
    args = ap.parse_args()

    from pipeline import generate as gen, camera_model as CM, contour_fit, geometry, neighbor, ls_template

    # --- вхід: усе з --in (контракт methods/README.md)
    marks = {}
    for w in ('back', 'left'):
        p = os.path.join(args.in_dir, f'marks_{w}.json')
        if os.path.exists(p):
            pts = json.load(open(p, encoding='utf-8')).get('points', [])
            if len(pts) >= 3:
                marks[w] = contour_fit.resample(np.array(pts, float), 200)
    if len(marks) < 2:
        print('Потрібна розмітка лінії згину з ОБОХ ракурсів (back і left).', file=sys.stderr)
        sys.exit(1)
    top_path = os.path.join(args.in_dir, 'top.png')
    if not os.path.exists(top_path):
        print('Потрібне фото згори (top) - з нього метод бере край шолома.', file=sys.stderr)
        sys.exit(1)
    cams = {}
    for w in ('back', 'left', 'top'):
        z = np.load(os.path.join(args.in_dir, f'cam_{w}.npy'))
        cams[w] = (z[:6], float(z[6]))

    recipe = gen.load_recipe(args.recipe)
    ref_path = (os.path.join(SERVICE_ROOT, recipe['method3_reference'])
                if recipe.get('method3_reference') else DEFAULT_REF)
    prog = geometry.load(ref_path)
    if recipe.get('method3_standoff_mm') is not None:
        standoff = float(recipe['method3_standoff_mm'])
    else:
        standoff, _ = geometry.fit_standoff(prog, neighbor._anchor_surface())
    cut_full, ids_full = geometry.cut_surface(prog, standoff, full=True)
    cut_full = np.asarray(cut_full, float)
    axis_by_id = dict(zip(ids_full, geometry.tool_axes(prog, ids_full)))
    center = cut_full.mean(0)
    ring, _ = geometry.cut_surface(prog, standoff, full=False)
    ring = np.asarray(ring, float)

    # плавний вигин: радіальний і висотний зсув як ряд Фур'є за кутом навколо шолома
    K = BEND_HARMONICS if args.bend == 'так' else 0
    rc = ring.mean(0)
    th = np.arctan2(ring[:, 1] - rc[1], ring[:, 0] - rc[0])
    radial = np.c_[np.cos(th), np.sin(th), 0 * th]
    F = (np.c_[[np.ones_like(th)] + [g(k * th) for k in range(1, K + 1) for g in (np.cos, np.sin)]].T
         if K else np.zeros((len(th), 0)))
    nb = F.shape[1]
    # Розтяг по осях шолома: e1 - довжина (лоб-потилиця), e2 - ширина (вухо-вухо), з SVD кільця.
    # Масштаб від центру: уздовж e1 найбільше рухаються лоб і потилиця, вуха (біля центру
    # по довжині) - майже ні; ширина рухає вуха ~1 мм на 1 %.
    ns = 2 if args.stretch == 'так' else 0
    _, _, Vt = np.linalg.svd(ring - rc)
    i_s = 7 + 2 * nb                          # індекс перших параметрів розтягу

    def deform(p):
        X = ring.copy()
        if nb:
            X = X + radial * (F @ p[7:7 + nb])[:, None]
            X[:, 2] += F @ p[7 + nb:i_s]
        if ns:
            L = (X - rc) @ Vt.T
            L[:, 0] *= np.exp(p[i_s])
            L[:, 1] *= np.exp(p[i_s + 1])
            X = L @ Vt + rc
        return X

    def rigid(p, X):
        R = cv2.Rodrigues(np.asarray(p[:3], float))[0]
        return (X - center) @ R.T * np.exp(p[6]) + center + p[3:6]

    def shape(p):
        return rigid(p, deform(p))

    g = cv2.GaussianBlur(cv2.imread(top_path, cv2.IMREAD_GRAYSCALE).astype(np.float32), (0, 0), 2.0)
    grads = (cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3))

    def residual_fn(targets, vis_idx, with_top):
        def res(p):
            P = shape(p)
            D = dense(P, 600)
            out = []
            for w, mk in targets.items():
                pc, f = cams[w]
                uv, z = CM.project(D, pc[:3], pc[3:6], f)
                mm = float(np.median(z)) / f
                d1 = cKDTree(uv).query(mk)[0]
                if w == 'top' and args.top != 'two':
                    # зі знаком: s > 0 - край НАЗОВНІ від лінії (лінія всередині силуету),
                    # s < 0 - лінія вилізла ЗА край шолома (фізично неможливо)
                    cu = uv.mean(0)
                    _, j = cKDTree(uv).query(mk)
                    t = uv[(j + 1) % len(uv)] - uv[j - 1]
                    nrm = np.c_[-t[:, 1], t[:, 0]] / (np.linalg.norm(t, axis=1, keepdims=True) + 1e-9)
                    nrm *= np.sign(((uv[j] - cu) * nrm).sum(1))[:, None]
                    sd = ((mk - uv[j]) * nrm).sum(1) * mm
                    inside = np.clip(sd, 0, None)
                    r = np.minimum(np.clip(-sd, 0, None), EDGE_CLIP_MM)
                    if args.top == 'asym':
                        r = r + np.minimum(inside, 1.5)
                    out.append(r / np.sqrt(len(r)) * 10)
                    continue
                if w == 'top':
                    d1 = np.minimum(d1, EDGE_CLIP_MM / mm)
                    uvr, _ = CM.project(P, pc[:3], pc[3:6], f)
                    d2 = np.minimum(cKDTree(mk).query(uvr)[0], EDGE_CLIP_MM / mm)
                else:
                    uvr, _ = CM.project(P[vis_idx[w]], pc[:3], pc[3:6], f)
                    d2, j = cKDTree(mk).query(uvr)
                    k = len(mk)
                    d2 = d2 * ((j > END_TRIM * k) & (j < (1 - END_TRIM) * k))
                out.append(np.r_[d1 / np.sqrt(len(d1)), d2 / np.sqrt(len(d2))] * mm * 10)
            out.append(p[7:i_s] * 0.05)
            out.append(p[i_s:] * 5.0)            # розтяг: м'яко тримати біля нуля (1 % ~ 0.05 мм нев'язки)
            return np.concatenate(out)
        return res

    n_par = 7 + 2 * nb + ns
    # Загальний масштаб і розтяг по осях частково дублюють одне одного: без обмеження
    # підгонка на v25 «схитрувала» - загальний 95 % + ширина +3 % (тобто шолом на 5 %
    # коротший; реальні шоломи відрізняються на 1-2 %). Тому з розтягом загальний - ±2 %.
    s_lim = 0.02 if ns else 0.35
    lo = np.r_[[-0.6] * 3, [-150.0] * 3, -s_lim, [-BEND_LIMIT_MM] * (2 * nb), [-0.03] * ns]
    hi = np.r_[[0.6] * 3, [150.0] * 3, s_lim, [BEND_LIMIT_MM] * (2 * nb), [0.03] * ns]

    def solve(targets, x0, vis_idx):
        x0 = np.clip(np.r_[x0, np.zeros(n_par - len(x0))][:n_par], lo + 1e-9, hi - 1e-9)
        return least_squares(residual_fn(targets, vis_idx, 'top' in targets), x0,
                             method='trf', bounds=(lo, hi), max_nfev=3000).x

    def visible(P):
        out = {}
        for w in ('back', 'left'):
            pc, f = cams[w]
            _, z = CM.project(P, pc[:3], pc[3:6], f)
            out[w] = near_idx(z)
        return out

    # 1. старт як Метод 3 (жорстко, лише back+left)
    x = np.zeros(7)
    x = solve(dict(marks), x, visible(ring))[:7]
    x = np.r_[x, np.zeros(n_par - 7)]
    start = shape(x)
    # 2. двічі: край згори біля поточної лінії -> підгонка під три ракурси
    for _ in range(2):
        P = shape(x)
        pc, f = cams['top']
        uv, _ = CM.project(dense(P, 400), pc[:3], pc[3:6], f)
        targets = dict(marks, top=edge_points(grads, uv))
        x = solve(targets, x, visible(P))

    final = shape(x)
    try:
        save_debug(args.out + '.debug.jpg', args.in_dir, cams, marks, targets['top'], start, final)
    except Exception as e:                  # картинка - лише для перегляду, розрахунок не ламає
        print(f'debug image: {e}', file=sys.stderr)
    disp_by_id = {}
    ring_ids = geometry.cut_surface(prog, standoff, full=False)[1]
    for pid, X in zip(ring_ids, final):
        disp_by_id[pid] = X
    xr = x.copy()

    def point_fn(point_id, orig_xyz):
        if point_id not in axis_by_id:
            return None
        if point_id in disp_by_id:          # точка кільця - з вигином
            X = disp_by_id[point_id]
        else:                               # підвід/відвід - лише жорсткий рух, як у Методі 3
            X = rigid(xr, np.asarray(dict(zip(ids_full, cut_full))[point_id])[None])[0]
        return X + geometry.NOMINAL_STANDOFF * np.asarray(axis_by_id[point_id])

    out_dir = os.path.dirname(args.out) or '.'
    os.makedirs(out_dir, exist_ok=True)
    tmp_out = ls_template.write_ls(ref_path, out_dir, point_fn, f'method4_{args.variant}')
    if tmp_out != args.out:
        os.replace(tmp_out, args.out)
    print(f'rot(deg)={np.degrees(x[:3]).round(3).tolist()} scale={np.exp(x[6]) * 100:.2f}% '
          f'shift={x[3:6].round(2).tolist()} bend={x[7:i_s].round(2).tolist()} '
          f'stretch(len,wid)%={(np.exp(x[i_s:]) * 100 - 100).round(2).tolist()}', file=sys.stderr)
    print(args.out)


if __name__ == '__main__':
    main()
