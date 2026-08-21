"""Отдать сцену в сервис 2020: камеры, линия реза, линия сгиба, снимки.

Связь между сервисами односторонняя и через файл: 3030 пишет сцену, 2020 её
читает и ничего не знает про 3030. Поэтому импорт здесь только в одну сторону -
из 3030 в формат 2020, а не наоборот.

    python export_scene.py v1 v21

Кладёт в service_2020/data/scenes/<вариант>/.
"""
import os
import sys
import json
import argparse
import numpy as np
import cv2

BASE = os.path.dirname(os.path.abspath(__file__))
S5056 = os.path.abspath(os.path.join(BASE, '..', 'service_5056'))
S2020 = os.path.abspath(os.path.join(BASE, '..', 'service_2020'))
sys.path.insert(0, BASE)
sys.path.insert(0, S2020)
sys.path.insert(0, os.path.join(S5056, 'scripts'))

import scene as S                                        # noqa: E402
import exp_camera_fit as E                               # noqa: E402
import export_ls as X                                    # noqa: E402
import fit_model                                         # noqa: E402
from shots import img_path                               # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PREVIEW_W = 1600            # снимки 4096x3000 браузеру ни к чему


def photo(variant, view, dst):
    img = cv2.imread(img_path(variant, view), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    h = int(img.shape[0] * PREVIEW_W / img.shape[1])
    name = f'{view}.jpg'
    cv2.imwrite(os.path.join(dst, name), cv2.resize(img, (PREVIEW_W, h)),
                [cv2.IMWRITE_JPEG_QUALITY, 88])
    return name


def mesh_rim(stl_path, angle_deg=45):
    """Нижняя кромка модели - НАСТОЯЩАЯ, из геометрии, без сэмплирования.

    Долго ходил вокруг: брал в секторе азимута нижнюю точку, потом самую
    широкую, потом сглаживал - и всякий раз кромка либо шла пилой, либо
    срезала перелом у уха. Всё это было лишним.

    У модели кромка - это резкий перегиб поверхности, а такие рёбра находятся
    точно: берём рёбра, у которых соседние грани разошлись больше чем на
    `angle_deg`, и собираем их в связные контуры. Внизу таких контура ровно
    два, у каждого все вершины степени 2 (то есть это честные замкнутые петли):
    внутренний и наружный края торца, стенка модели около 8 мм. Берём наружный -
    рез ложится на внешнюю поверхность.

    Результат совпадает с моделью в точности, сглаживать нечего.
    """
    from collections import defaultdict
    import exp_cad_fit as F
    tri = F.load_stl(stl_path)
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9

    own = defaultdict(list)
    for i, t in enumerate(np.round(tri, 3)):
        for a, b in ((0, 1), (1, 2), (2, 0)):
            own[tuple(sorted((tuple(t[a]), tuple(t[b]))))].append(i)
    lim = np.cos(np.radians(angle_deg))
    adj = defaultdict(set)
    for e, f in own.items():
        if len(f) == 2 and float(nrm[f[0]] @ nrm[f[1]]) < lim:
            adj[e[0]].add(e[1])
            adj[e[1]].add(e[0])

    seen, loops = set(), []
    for v in adj:
        if v in seen:
            continue
        stack, comp = [v], set()
        while stack:
            u = stack.pop()
            if u in comp:
                continue
            comp.add(u)
            seen.add(u)
            stack.extend(adj[u] - comp)
        if len(comp) > 50 and all(len(adj[u]) == 2 for u in comp):
            loops.append(comp)
    if not loops:
        raise ValueError('замкнутых контуров перегиба не нашлось')

    # нижние контуры - это края торца; из них берём наружный, по радиусу
    def radius(c):
        P = np.array(list(c))
        return np.hypot(P[:, 0] - P[:, 0].mean(), P[:, 1] - P[:, 1].mean()).max()
    low = min(np.array(list(c))[:, 2].mean() for c in loops)
    bottom = [c for c in loops
              if np.array(list(c))[:, 2].mean() < low + 30]
    comp = max(bottom, key=radius)

    start = next(iter(comp))
    order, prev, cur = [start], None, start
    while True:
        nxt = [u for u in adj[cur] if u != prev]
        if not nxt or nxt[0] == start:
            break
        prev, cur = cur, nxt[0]
        order.append(cur)
    return np.array(order, float)


def build(variant):
    fit_model.standoff(variant)
    dst = S.asset_dir(variant)
    foc = json.load(open(E.LASER_CAMS, encoding='utf-8'))

    # Камеры берутся из маркерной калибровки 18.08, если она есть: она считана по
    # 26 точкам с проверкой исключением 0.2-0.6 мм и независимо подтверждена на
    # лазерных пятнах 11.08. Старая калибровка по программам остаётся запасной.
    cams = []
    for view in ('back', 'left', 'top'):
        mk = os.path.join(BASE, 'data', f'cam_{view}_marker.npy')
        old = os.path.join(BASE, 'data', f'cam_{view}.npy')
        if os.path.exists(mk):
            z = np.load(mk)
            p, f = z[:6], float(z[6])
        elif os.path.exists(old):
            p, f = np.load(old)[:6], foc[view]['focus']
        else:
            continue
        cams.append(S.camera(view, position=p[3:6], rotation=p[:3], focal_px=f,
                             image=photo(variant, view, dst)))

    cut = E.ring(variant, 0.0)
    fold = E.ring(variant, X.FOLD_OFFSET)
    curves = [S.curve(f'линия реза {variant}', cut, '#3b82f6', closed=True, width=3),
              S.curve(f'линия сгиба {variant}', fold, '#22c55e', closed=True, width=2)]

    # положения сопла из лазерной пробы: точные точки в тех же координатах
    pts = []
    csv = os.path.join(S5056, '..', 'laserdot_1', 'positions.csv')
    if os.path.exists(csv):
        import csv as _csv
        rows = [r for r in _csv.DictReader(
            l for l in open(csv, encoding='utf-8') if not l.startswith('#'))]
        xyz = [[float(r['x']), float(r['y']), float(r['z'])] for r in rows]
        if xyz:
            pts.append(S.points('сопло, лазерная проба', xyz, '#f59e0b', size=5))

    # CAD ставится АНАЛИТИЧЕСКИ, а не подгонкой по силуэтам: слепая подгонка
    # садилась в ложный оптимум и клала шлем вверх дном, потому что закрытая
    # площадь у перевёрнутого купола почти та же. Здесь модель просто ставится
    # куполом вверх на плоскость линии реза, а точно её доводят руками в 2020.
    #
    # Купол смотрит против нормали кольца: +Z станка направлен ВНИЗ по кадру
    # (проверено проекцией пробной точки), поэтому меш, растущий вверх по своему
    # +Z, надо развернуть.
    # Положение, выставленное руками в 2020, ПЕРЕЖИВАЕТ перевыгрузку. Первая
    # версия его затирала: заказчик выставил модель, нажал сохранить, а
    # следующий прогон вернул всё к аналитическому положению.
    saved = {}
    prev = os.path.join(S2020, 'data', 'scenes', variant, 'scene.json')
    if os.path.exists(prev):
        with open(prev, encoding='utf-8') as f:
            for m in json.load(f).get('meshes', []):
                if m.get('placement'):
                    saved[m['name']] = m['placement']

    meshes = []
    stl = os.path.join(S5056, 'input', 'model_3d', 'helmet_ref.stl')
    if os.path.exists(stl):
        import shutil
        from scipy.spatial.transform import Rotation
        c = cut.mean(0)
        n = np.linalg.svd(cut - c)[2][2]
        n = n if n[2] > 0 else -n              # нормаль вдоль +Z станка
        up = -n                                # куда смотрит купол
        z = np.array([0., 0., 1.])
        v = np.cross(z, up)
        s = np.linalg.norm(v)
        R = (np.eye(3) if s < 1e-9 else
             Rotation.from_rotvec(v / s * np.arctan2(s, float(z @ up))).as_matrix())
        rz, ry, rx = Rotation.from_matrix(R).as_euler('ZYX', degrees=True)
        shutil.copy(stl, os.path.join(dst, 'helmet.stl'))
        rim = mesh_rim(stl)
        name = 'CAD (ставить руками)'
        pl = saved.get(name, dict(rot_deg=(rx, ry, rz), translate=c, scale=1.0))
        meshes.append(S.mesh(name, 'helmet.stl', color='#d6be4a', opacity=0.6,
                             rim=rim,
                             **{k: pl[k] for k in ('rot_deg', 'translate', 'scale')}))
        if name in saved:
            print(f'   положение модели взято из сцены, не пересчитано')

    path = S.write(variant, cameras=cams, curves=curves, point_sets=pts,
                   meshes=meshes,
                   note=f'{variant}: камеры из 3030, линия реза из .LS')
    print(f'{variant}: {path}')
    return path


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('variants', nargs='+')
    a = ap.parse_args()
    for v in a.variants:
        build(v)
