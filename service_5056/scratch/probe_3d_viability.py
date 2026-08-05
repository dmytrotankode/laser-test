"""Годится ли путь «строить контур из 3D-модели»? Два дешёвых факта.

ФАКТ 1. Плоская ли линия реза?
  Оператор в CAM выбирает ПЛОСКОСТЬ реза. Если записанный контур после его ручной
  подгонки остался плоским, то генерация тривиальна: пересечение плоскости с
  поверхностью. Если нет — линия реза сложнее, и одной плоскостью её не задать.

ФАКТ 2. Ложится ли CAD-меш на записанные линии реза?
  Линия реза лежит НА поверхности шлема. Значит меш можно подогнать к ней жёстко,
  без всяких камер. Если остаток мал — CAD соответствует реальному шлему, и заодно
  找 получена связь «координаты меша <-> координаты станка», которой сейчас нет.
  Если остаток велик — CAD не соответствует, и генерировать по нему контур нельзя.

Ничего не обучается, только замер.
"""
import os
import sys
import numpy as np

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import lsgeom     # noqa: E402
import dataset    # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

anchor = lsgeom.load(os.path.join(BASE, 'input', 'archive', 'v1', 'ground_truth.ls'))
REF, _ = lsgeom.cut_surface(anchor, lsgeom.NOMINAL_STANDOFF)


def cutline(v):
    p = lsgeom.load(os.path.join(BASE, 'input', 'archive', v, 'ground_truth.ls'))
    so, _ = lsgeom.fit_standoff(p, REF)
    return lsgeom.cut_surface(p, so)[0]


# ------------------------------------------------------------------ ФАКТ 1
print("=" * 72)
print("ФАКТ 1. Плоская ли линия реза?")
print("=" * 72)
print(f"{'вар':<6}{'отклонение от плоскости, мм':>30}{'наклон плоскости':>20}")
for v in dataset.ALL[:6] + ['v13']:
    P = cutline(v)
    c = P.mean(0)
    _, S, Vt = np.linalg.svd(P - c)
    n = Vt[2]                       # нормаль наилучшей плоскости
    dev = np.abs((P - c) @ n)
    tilt = np.degrees(np.arccos(abs(n[2])))
    print(f"{v:<6}{dev.mean():>15.2f} сред / {dev.max():>6.2f} макс{tilt:>17.1f}°")

# ------------------------------------------------------------------ ФАКТ 2
print()
print("=" * 72)
print("ФАКТ 2. Ложится ли CAD-меш на записанную линию реза?")
print("=" * 72)

stl_path = os.path.join(BASE, 'input', 'model_3d', 'helmet_ref.stl')
if not os.path.exists(stl_path):
    sys.exit(f"нет {stl_path}")

data = np.fromfile(stl_path, dtype=np.uint8)
if data[:5].tobytes().lower() == b'solid' and b'facet' in data[:512].tobytes():
    sys.exit("STL в текстовом формате — здесь ожидается бинарный")
ntri = int(np.frombuffer(data[80:84], dtype='<u4')[0])
rec = data[84:84 + ntri * 50].reshape(ntri, 50)
tri = np.frombuffer(rec[:, 12:48].tobytes(), dtype='<f4').reshape(ntri, 3, 3).astype(float)
print(f"меш: {ntri} треугольников, габариты "
      f"{np.ptp(tri.reshape(-1,3), axis=0).round(1)}")

# плотное облако по поверхности: вершины + центроиды + середины рёбер
pts = [tri.reshape(-1, 3), tri.mean(1)]
for a, b in ((0, 1), (1, 2), (2, 0)):
    pts.append((tri[:, a] + tri[:, b]) / 2)
for w in ((0.6, 0.2, 0.2), (0.2, 0.6, 0.2), (0.2, 0.2, 0.6)):
    pts.append(tri[:, 0] * w[0] + tri[:, 1] * w[1] + tri[:, 2] * w[2])
CLOUD = np.unique(np.vstack(pts).round(3), axis=0)
print(f"облако поверхности: {len(CLOUD)} точек, "
      f"среднее расстояние между соседями ~{np.ptp(CLOUD,axis=0).max()/len(CLOUD)**0.5:.2f} мм")

try:
    from scipy.spatial import cKDTree
    tree = cKDTree(CLOUD)
    query = lambda X: tree.query(X)[0]
except Exception:
    query = lambda X: np.linalg.norm(X[:, None, :] - CLOUD[None, :, :], axis=2).min(1)


def fit_mesh_to_curve(P, iters=80):
    """Жёстко двигаем ОБЛАКО МЕША так, чтобы кривая P легла на его поверхность."""
    C = CLOUD.copy()
    # старт: совместить центры и посадить по высоте
    C = C - C.mean(0) + P.mean(0)
    best = None
    for _ in range(iters):
        if 'tree' in dir():
            t = cKDTree(C)
            j = t.query(P)[1]
        else:
            j = np.linalg.norm(P[:, None, :] - C[None, :, :], axis=2).argmin(1)
        Rm, tv = lsgeom.kabsch(C[j], P)
        C = C @ Rm.T + tv
        if 'tree' in dir():
            d = cKDTree(C).query(P)[0]
        else:
            d = np.linalg.norm(P[:, None, :] - C[None, :, :], axis=2).min(1)
        if best is None or d.mean() < best[0]:
            best = (float(d.mean()), float(np.percentile(d, 90)), float(d.max()))
    return best


print()
print(f"{'вар':<6}{'расстояние линии реза до поверхности меша':>44}")
for v in ('v1', 'v9', 'v13'):
    P = cutline(v)
    m, p9, mx = fit_mesh_to_curve(P)
    print(f"{v:<6}{m:>18.2f} сред {p9:>8.2f} p90 {mx:>8.2f} макс")

print()
print("Читать так: если остаток порядка 0.5-1 мм — CAD соответствует реальному шлему,")
print("и связь «меш <-> станок» получена без камер. Если несколько мм — CAD не годится")
print("как источник формы, и генерировать по нему контур нельзя.")
