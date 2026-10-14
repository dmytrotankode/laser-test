"""Межа підгонки еталона, якщо дозволити ПЛАВНИЙ вигин: поверх жорсткої пози кожна точка
зсувається радіально і по висоті на a(θ), b(θ) - ряд Фур'є до K гармонік за кутом навколо кільця.
K=0 - чисто жорстко. Чим менше K, тим плавніше (жодних хвиль між сусідніми точками)."""
import sys, numpy as np, cv2
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
sys.path.insert(0, r"C:\Art\Ai projects\Laser2\service_2021")
import ls_points
L = r"C:\Art\Ai projects\Laser2"
P = {k: np.array([p[2] for p in ls_points.read_ring(v)]) for k, v in {
  '1010_1': L + r"\laserdot_3\TOR_XL_1010_1.LS",
  '0510_1': L + r"\laserdot_3\sets_0510\TOR_XL_0510_1\TOR_XL_0510_1.LS",
  '0510_2': L + r"\laserdot_3\sets_0510\TOR_XL_0510_2\TOR_XL_0510_2.LS"}.items()}
def dense(R, n=3000):
    Q = np.r_[R, R[:1]]; d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
    t = np.linspace(0, d[-1], n, endpoint=False)
    return np.c_[[np.interp(t, d, Q[:, i]) for i in range(3)]].T
A = P['1010_1']; c = A.mean(0)
th = np.arctan2(A[:, 1] - c[1], A[:, 0] - c[0])
rad = np.c_[np.cos(th), np.sin(th), np.zeros_like(th)]
for tgt in ('0510_1', '0510_2'):
    tree = cKDTree(dense(P[tgt]))
    prev = None
    for K in (0, 1, 2, 3, 4, 6):
        F = np.c_[[np.ones_like(th)] + [f(k * th) for k in range(1, K + 1) for f in (np.cos, np.sin)]].T
        nb = F.shape[1]
        def warp(p):
            Rm = cv2.Rodrigues(p[:3])[0]; s = np.exp(p[6])
            a, b = F @ p[7:7 + nb], F @ p[7 + nb:]
            X = A + rad * a[:, None] + np.c_[0 * a, 0 * a, b]
            return (X - c) @ Rm.T * s + c + p[3:6]
        best = None
        starts = [prev] if prev is not None else [np.r_[0, 0, y, P[tgt].mean(0) - c, 0, np.zeros(2 * nb)] for y in np.radians(np.arange(-20, 21, 5))]
        for x0 in starts:
            x0 = np.r_[x0[:7], np.zeros(2 * nb)] if len(x0) != 7 + 2 * nb else x0
            r = least_squares(lambda p: tree.query(warp(p))[0], x0)
            if best is None or r.cost < best.cost: best = r
        d = tree.query(warp(best.x))[0]
        prev = best.x
        print(f'{tgt} K={K}: середня {d.mean():.2f} мм, 90% {np.percentile(d,90):.2f}, макс {d.max():.2f}, <1мм {np.mean(d<1)*100:.0f}%')
