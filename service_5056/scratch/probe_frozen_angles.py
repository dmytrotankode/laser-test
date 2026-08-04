"""Заморожены ли W/P/R? Сравниваем поворот, зашитый в углы, с поворотом,
который даёт совмещение самих контуров (реальная поза шлема)."""
import sys, os
import numpy as np

ROOT = r"C:\Art\Ai projects\Laser2\service_5056"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import lsgeom
from scipy.spatial.transform import Rotation as R

VARIANTS = [f"v{i}" for i in range(1, 17)]


def load(v):
    prog = lsgeom.load(os.path.join(ROOT, "input", "archive", v, "ground_truth.ls"))
    _, contour, _ = prog.split_path()
    contour = contour[1:]
    P = np.array([prog.points[i][:3] for i in contour])
    W = np.array([prog.points[i][3:] for i in contour])
    ax = np.array([R.from_euler('ZYX', [w[2], w[1], w[0]], degrees=True).apply([0, 0, 1])
                   for w in W])
    return P, W, ax


def kabsch(A, B):
    ca, cb = A.mean(0), B.mean(0)
    H = (A - ca).T @ (B - cb)
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    return Vt.T @ np.diag([1, 1, d]) @ U.T


data = {v: load(v) for v in VARIANTS}
P1, W1, ax1 = data["v1"]

print("Сырые W/P/R первых трёх точек контура, по вариантам:")
for v in ["v1", "v2", "v4", "v6", "v7", "v13"]:
    P, W, ax = data[v]
    s = "  ".join(f"({w[0]:.2f},{w[1]:.2f},{w[2]:.2f})" for w in W[:3])
    print(f"  {v:<4} {s}")

print()
print("Побитово одинаковы ли углы с v1 (в пределах партии)?")
for v in VARIANTS:
    P, W, ax = data[v]
    n = min(len(W), len(W1))
    same = np.abs(W[:n] - W1[:n]).max()
    print(f"  {v:<4} макс |ΔWPR| к v1 = {same:8.3f}°")

print()
print("Поворот из углов vs поворот из совмещения контуров (реальная поза):")
print(f"{'вар':<5} {'из углов':>12} {'из контура':>12}")
for v in VARIANTS:
    P, W, ax = data[v]
    n = min(len(ax), len(ax1))
    Ra = kabsch(ax[:n], ax1[:n])
    ang_a = np.degrees(np.linalg.norm(R.from_matrix(Ra).as_rotvec()))
    u = np.linspace(0, 1, 720, endpoint=False)
    a = lsgeom.eval_at_arc(P1, u)
    b = lsgeom.eval_at_arc(P, u + lsgeom.phase_offset(P1, P))
    Rc = kabsch(b, a)
    ang_c = np.degrees(np.linalg.norm(R.from_matrix(Rc).as_rotvec()))
    print(f"{v:<5} {ang_a:>11.3f}° {ang_c:>11.3f}°")
