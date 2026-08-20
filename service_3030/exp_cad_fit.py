"""Ставим CAD в координаты станка по силуэтам на снимках - и заодно проверяем его.

Подогнать край основания меша к линии реза нельзя: меш замкнут, дно закрыто
крышкой, и никакого края там нет. Зато есть две откалиброванные камеры и
сегментированные силуэты. Ищем положение и масштаб меша так, чтобы его проекция
совпала с силуэтом на обоих ракурсах.

Мера - IoU (доля пересечения к объединению) между проекцией меша и маской.
Сравнивается только верхняя часть силуэта, ровно та, что оставляет штатная
отсечка 5056: ниже идёт необрезанная юбка, которой у готового CAD и не должно
быть.

Итог сам по себе есть ответ на вопрос "годится ли CAD как источник формы":
если лучшее совпадение силуэтов плохое, значит модель не описывает реальный шлем,
и строить на ней нечего.
"""
import os
import sys
import struct
import numpy as np
import cv2
from scipy.optimize import minimize

BASE = os.path.dirname(os.path.abspath(__file__))
S5056 = os.path.abspath(os.path.join(BASE, '..', 'service_5056'))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(S5056, 'scripts'))

import exp_camera_fit as E                               # noqa: E402
import export_ls as X                                    # noqa: E402
import fit_model                                         # noqa: E402
from step03_segment_monochrome import segment_image      # noqa: E402
from shots import img_path                               # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

STL = os.path.join(S5056, 'input', 'model_3d', 'helmet_ref.stl')
SCALE = 4                       # во сколько раз мельче считаем маски
VIEWS = ('back', 'left')


def load_stl(path):
    b = open(path, 'rb').read()
    n = struct.unpack('<I', b[80:84])[0]
    tri = np.empty((n, 3, 3), np.float32)
    for i in range(n):
        tri[i] = np.frombuffer(b, np.float32, 9, 84 + i * 50 + 12).reshape(3, 3)
    return tri.astype(float)


def masks(variant):
    out = {}
    for v in VIEWS:
        m, _, _, _, _ = segment_image(img_path(variant, v), False)
        out[v] = cv2.resize(m, (4096 // SCALE, 3000 // SCALE),
                            interpolation=cv2.INTER_NEAREST) > 0
    return out


def render(tri, p, cams, view, shape):
    """Силуэт меша в кадре: растеризуем проекции треугольников."""
    R = cv2.Rodrigues(p[:3])[0]
    V = tri.reshape(-1, 3) * p[6] @ R.T + p[3:6]
    pc, f = cams[view]
    uv, z = E.project(V, pc[:3], pc[3:6], f)
    uv = (uv / SCALE).astype(np.int32).reshape(-1, 3, 2)
    ok = (z.reshape(-1, 3) > 1).all(1)
    img = np.zeros(shape, np.uint8)
    # Одной заливкой нельзя: в уменьшенном кадре часть треугольников тоньше
    # пикселя, fillPoly их пропускает, и силуэт получается дырявым. По такому
    # решету IoU занижен, и подгонка гонится за испорченной мерой - первый заход
    # так и сел мимо. Дорисовываем рёбра и закрываем остатки.
    cv2.fillPoly(img, uv[ok], 1)
    cv2.polylines(img, uv[ok], True, 1, 1)
    # Даже с рёбрами часть треугольников тоньше пикселя, и силуэт остаётся
    # дырявым. Купол односвязен, поэтому берём внешний контур и заливаем его -
    # дыр тогда не бывает по построению, а не по счастью.
    cnts, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    img[:] = 0
    if cnts:
        cv2.drawContours(img, [max(cnts, key=cv2.contourArea)], -1, 1, -1)
    return img > 0


def score(p, tri, cams, M):
    bad = 0.0
    for v in VIEWS:
        m = M[v]
        rows = np.where(m.any(1))[0]
        s = render(tri, p, cams, v, m.shape)
        band = slice(0, rows.max() + 1)          # ниже отсечки сравнивать нечего
        a, b = m[band], s[band]
        inter = np.count_nonzero(a & b)
        union = np.count_nonzero(a | b)
        bad += 1.0 - inter / max(union, 1)
    return bad / len(VIEWS)


def main(variant='v1'):
    tri = load_stl(STL)
    print(f'меш: {len(tri)} треугольников')
    fit_model.standoff(variant)
    cams = X.cameras()
    M = masks(variant)
    ring = E.ring(variant, 0.0)
    c = ring.mean(0)

    # старт: центр меша в центр кольца, ось Z вверх, перебор поворота вокруг Z
    base = tri.reshape(-1, 3).mean(0)
    best = None
    for yaw in np.radians(np.arange(0, 360, 15)):
        for dz in (-60, 0, 60):
            p0 = np.r_[0, 0, yaw, c - base + [0, 0, dz], 1.0]
            s = score(p0, tri, cams, M)
            if best is None or s < best[0]:
                best = (s, p0)
    print(f'лучший старт: несовпадение {best[0]:.3f}')

    # Сначала при масштабе 1: CAD обязан быть в натуральную величину, и если
    # оптимизатор его ужимает, это признак плохого положения, а не размера.
    fixed = minimize(lambda q: score(np.r_[q, 1.0], tri, cams, M), best[1][:6],
                     method='Powell', options=dict(maxiter=4000, xtol=1e-3, ftol=1e-4))
    print(f'при масштабе 1: несовпадение {fixed.fun:.3f}  (IoU {1 - fixed.fun:.3f})')
    # Масштаб отпускаем лишь чуть-чуть: CAD обязан быть в натуральную величину,
    # и свобода тут нужна не для подгонки размера, а для запаса на неточность
    # фокуса. Без ограничения оптимизатор ужимал меш до 0.83 и заваливал его
    # набок, лишь бы закрыть площадь.
    def bounded(q):
        return score(np.r_[q[:6], np.clip(q[6], 0.95, 1.05)], tri, cams, M)
    r = minimize(bounded, np.r_[fixed.x, 1.0], method='Powell',
                 options=dict(maxiter=6000, xtol=1e-3, ftol=1e-4))
    p = np.r_[r.x[:6], np.clip(r.x[6], 0.95, 1.05)]
    if score(p, tri, cams, M) > fixed.fun:
        p = np.r_[fixed.x, 1.0]
    print(f'после подгонки: несовпадение {r.fun:.3f}  (IoU {1 - r.fun:.3f})')
    print(f'масштаб {p[6]:.3f}, центр {np.round(p[3:6], 1)}')
    for v in VIEWS:
        m = M[v]
        s = render(tri, p, cams, v, m.shape)
        rows = np.where(m.any(1))[0]
        a, b = m[:rows.max() + 1], s[:rows.max() + 1]
        iou = np.count_nonzero(a & b) / max(np.count_nonzero(a | b), 1)
        print(f'   {v}: IoU {iou:.3f}')
    np.save(os.path.join(BASE, 'data', f'cad_{variant}.npy'), p)
    return p


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'v1')
