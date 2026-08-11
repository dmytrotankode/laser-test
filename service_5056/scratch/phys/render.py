"""Силуэт CAD-меша под заданной камерой. Ничего из пайплайна не трогает.

Модель камеры намеренно бедная: фокус + положение + поворот, главная точка в
центре кадра, дисторсии нет. Так задумано - калибровка из calib2 показала, что
дисторсию и главную точку эти данные не определяют (k2 = 38, cy = 3500 при
высоте 3000), а фокусы при этом сошлись правдоподобно. Брать оттуда только то,
что данные действительно держат.
"""
import os
import sys
import numpy as np
import cv2

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if os.path.join(BASE, 'scripts') not in sys.path:
    sys.path.insert(0, os.path.join(BASE, 'scripts'))

FULL_W, FULL_H = 4096, 3000

# --------------------------------------------------------------------- меш
_raw = np.fromfile(os.path.join(BASE, 'input', 'model_3d', 'helmet_ref.stl'), dtype=np.uint8)
_n = int(np.frombuffer(_raw[80:84], dtype='<u4')[0])
TRI = np.frombuffer(_raw[84:84 + _n * 50].reshape(_n, 50)[:, 12:48].tobytes(),
                    dtype='<f4').reshape(_n, 3, 3).astype(np.float64)
VERTS = TRI.reshape(-1, 3)
NTRI = _n

# плотная выборка поверхности: вершины + центроид + середины рёбер.
# Медианное ребро 7.1 мм, в уменьшенном кадре это 1-3 px, так что такой
# россыпи хватает, чтобы после смыкания получить сплошной силуэт.
SURF = np.vstack([VERTS, TRI.mean(1),
                  (TRI[:, 0] + TRI[:, 1]) / 2,
                  (TRI[:, 1] + TRI[:, 2]) / 2,
                  (TRI[:, 2] + TRI[:, 0]) / 2])


def look_at(eye, target, up=(0, 0, 1)):
    """Матрица поворота мира в систему камеры (камера смотрит вдоль +Z)."""
    eye = np.asarray(eye, float)
    f = np.asarray(target, float) - eye
    f /= np.linalg.norm(f)
    up = np.asarray(up, float)
    if abs(f @ up) > 0.999:                      # взгляд вдоль up - берём другой
        up = np.array([1.0, 0.0, 0.0])
    r = np.cross(up, f); r /= np.linalg.norm(r)
    u = np.cross(f, r)
    return np.stack([r, u, f])                   # строки: x, y, z камеры


class Camera:
    """f в пикселях полного кадра; R,t переводят точку мира в систему камеры."""

    def __init__(self, f, R, t, scale=1.0):
        self.f = float(f)
        self.R = np.asarray(R, float).reshape(3, 3)
        self.t = np.asarray(t, float).reshape(3)
        self.scale = float(scale)                # во сколько уменьшен кадр

    @property
    def size(self):
        return int(round(FULL_W * self.scale)), int(round(FULL_H * self.scale))

    def project(self, P):
        """(N,3) мир -> (N,2) пиксели уменьшенного кадра. Z<=0 отбраковывается."""
        Q = P @ self.R.T + self.t
        z = Q[:, 2]
        bad = z <= 1e-6
        z = np.where(bad, 1e-6, z)
        w, h = self.size
        f = self.f * self.scale
        u = f * Q[:, 0] / z + w / 2.0
        v = f * Q[:, 1] / z + h / 2.0
        return np.stack([u, v], 1), bad

    def silhouette(self, pose_R=None, pose_t=None, cutoff_row=None):
        """Бинарная маска меша, поставленного в позу (pose_R, pose_t).

        Треугольники рисуются ПО ОДНОМУ. Одним вызовом cv2.fillPoly нельзя -
        там правило чётности, и перекрывающиеся грани закрытой поверхности
        взаимно вычитаются, меш выходит дырявым. Прошлый обход этой беды -
        россыпь точек поверхности со смыканием - оказался хуже: реально
        закрашивалось 17 тыс. px из 96 тыс. итоговых, обвод держался на редких
        крайних точках, а заливка «крупнейшего контура» соединяла разрывы
        напрямую и лепила прямые грани там, где у детали плавный бок.
        """
        V = TRI.reshape(-1, 3)
        if pose_R is not None:
            V = V @ np.asarray(pose_R, float).T
        if pose_t is not None:
            V = V + np.asarray(pose_t, float)
        uv, bad = self.project(V)
        w, h = self.size
        mask = np.zeros((h, w), np.uint8)

        polys = uv.reshape(NTRI, 3, 2)
        keep = ~bad.reshape(NTRI, 3).any(1)
        mn, mx = polys.min(1), polys.max(1)
        keep &= (mx[:, 0] >= 0) & (mn[:, 0] < w) & (mx[:, 1] >= 0) & (mn[:, 1] < h)
        polys = np.clip(polys[keep], -1e4, 1e4).astype(np.int32)
        for p in polys:
            cv2.fillConvexPoly(mask, p, 255)

        if cutoff_row is not None:
            mask[int(cutoff_row):, :] = 0
        return mask


def load_mask(variant, view, scale):
    """Маска из кэша пайплайна (results/_ref_masks) плюс строка отсечки.

    Возвращает (маска, cutoff_row). Safe Zone у боковых видов уже применена при
    сегментации, поэтому нижняя занятая строка и есть линия отсечки. Рендер надо
    резать по ЭТОЙ строке, а не по своим «58 % высоты»: у CAD и у живого шлема
    низ разный (необрезанная юбка), и одинаковая доля высоты легла бы на разной
    физической высоте.
    """
    p = os.path.join(BASE, 'results', '_ref_masks', f'{variant}_{view}.png')
    if not os.path.exists(p):
        return None, None
    m = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
    w, h = int(round(FULL_W * scale)), int(round(FULL_H * scale))
    m = cv2.resize(m, (w, h), interpolation=cv2.INTER_NEAREST)
    rows = np.where(m.max(1) > 0)[0]
    if len(rows) == 0:
        return m, None
    cut = int(rows.max()) + 1
    return m, (cut if cut < h - 1 else None)
