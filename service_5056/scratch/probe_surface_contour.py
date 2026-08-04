"""Проверка идеи: перейти от поз сопла к контуру НА поверхности шлема.

Q1. Несут ли W/P/R в .ls информацию сверх одной жёсткой ротации на вариант?
Q2. Сближаются ли 16 контуров, если снять отступ d вдоль оси инструмента?
    И восстанавливается ли при этом ступенька зазора (-3.6 / -6.4) из PLAN §4?
"""
import sys, os
import numpy as np

ROOT = r"C:\Art\Ai projects\Laser2\service_5056"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import lsgeom
from scipy.spatial.transform import Rotation as R

VARIANTS = [f"v{i}" for i in range(1, 17)]
N = 720


def load(v):
    p = os.path.join(ROOT, "input", "archive", v, "ground_truth.ls")
    prog = lsgeom.load(p)
    ids = prog.order if len(prog.order) >= 5 else sorted(prog.points)
    _, contour, _ = prog.split_path()
    contour = contour[1:]                      # как cut_ring: без врезки
    P = np.array([prog.points[i][:3] for i in contour])
    W = np.array([prog.points[i][3:] for i in contour])
    ax = np.array([R.from_euler('ZYX', [w[2], w[1], w[0]], degrees=True).apply([0, 0, 1])
                   for w in W])
    return P, W, ax


def kabsch(A, B):
    """Жёсткое преобразование, переводящее A в B (соответствие по индексу)."""
    ca, cb = A.mean(0), B.mean(0)
    H = (A - ca).T @ (B - cb)
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    Rm = Vt.T @ np.diag([1, 1, d]) @ U.T
    return Rm, cb - Rm @ ca


def resample_aligned(ref, cur, n=N):
    """cur, пересэмплированный на n точек и выровненный по фазе с ref."""
    du = lsgeom.phase_offset(ref, cur)
    u = np.linspace(0, 1, n, endpoint=False)
    return lsgeom.eval_at_arc(ref, u), lsgeom.eval_at_arc(cur, u + du)


def fit_residual(ref, cur):
    """Остаток после наилучшего жёсткого совмещения, мм (среднее точка->кривая)."""
    a, b = resample_aligned(ref, cur)
    Rm, t = kabsch(b, a)
    b2 = (Rm @ b.T).T + t
    return float(lsgeom.curve_distance(b2, ref).mean())


data = {v: load(v) for v in VARIANTS}

print("=" * 74)
print("Q1. Информативны ли углы? Ось инструмента: разброс внутри варианта")
print("    и остаток после снятия одной жёсткой ротации относительно v1.")
print("=" * 74)

P1, W1, ax1 = data["v1"]
print(f"{'вар':<5} {'разброс осей внутри контура':>28} {'остаток к v1 после ротации':>28}")
for v in VARIANTS:
    P, W, ax = data[v]
    spread = np.degrees(np.arccos(np.clip(ax @ ax.mean(0) /
                                          np.linalg.norm(ax.mean(0)), -1, 1)))
    n = min(len(ax), len(ax1))
    Rm, _ = kabsch(ax[:n], ax1[:n])
    resid = np.degrees(np.arccos(np.clip(((Rm @ ax[:n].T).T * ax1[:n]).sum(1), -1, 1)))
    print(f"{v:<5} {spread.max():>21.1f}° макс {resid.mean():>21.2f}° сред")

print()
print("=" * 74)
print("Q2. Отступ d вдоль оси: сближаются ли контуры на поверхности?")
print("    Опора — v1 при d=10 мм. Для каждого варианта ищем свой d.")
print("=" * 74)

ref_surf = P1 - 10.0 * ax1
grid = np.arange(-6.0, 26.01, 0.5)

print(f"{'вар':<5} {'d при d=10':>12} {'лучший d':>10} {'остаток':>10} {'сдвиг к v1':>12}")
rows = []
for v in VARIANTS:
    P, W, ax = data[v]
    errs = [fit_residual(ref_surf, P - d * ax) for d in grid]
    errs = np.array(errs)
    k = int(errs.argmin())
    # уточнение параболой по трём точкам
    if 0 < k < len(grid) - 1:
        y0, y1, y2 = errs[k - 1], errs[k], errs[k + 1]
        dd = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) * (grid[1] - grid[0])
    else:
        dd = 0.0
    dbest = grid[k] + dd
    e10 = fit_residual(ref_surf, P - 10.0 * ax)
    rows.append((v, e10, dbest, errs[k], dbest - 10.0))
    print(f"{v:<5} {e10:>12.2f} {dbest:>10.2f} {errs[k]:>10.2f} {dbest - 10.0:>+12.2f}")

print()
print("Для сравнения — те же контуры БЕЗ снятия отступа (позы сопла как есть):")
for v in VARIANTS:
    P, W, ax = data[v]
    print(f"  {v:<5} остаток к v1 (сопло): {fit_residual(P1, P):.2f} мм")
