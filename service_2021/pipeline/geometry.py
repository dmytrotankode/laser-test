"""Shared Fanuc .LS geometry helpers - vendored from service_5056/scripts/lsgeom.py.

This is pipeline-internal optimizer/training math (ICP shape alignment, traversal-order
contour extraction, standoff fitting) - NOT the same job as ../ls_points.py, which is the
viewer's own naive/robust .LS parser. Keep them separate: merging would make the viewer's
simple parser depend on scipy.optimize and ICP, and would lose ls_points.py's ability to
survive an operator-corrected .LS that never went through this pipeline. tool_axes() below
duplicates ls_points.py's tool_axis() (same W/R-swap Fanuc convention) - that duplication is
deliberate, see ls_points.py's own docstring.

Everything here is deliberately ORDER-INDEPENDENT where it can be. The point numbering in
.LS files is not consistent between the two archive batches:

    old batch (v1-v6):   P[1]=approach, contour = P[2], P[99], P[3]..P[97], P[98]=retreat
    new batch (v7-v16):  P[1]=approach, contour = P[2]..P[98],               P[99]=retreat

Both are fully described by the motion instructions in /MN, so we read the traversal order
from there instead of guessing from the P-index.
"""
import os
import re
import numpy as np
from scipy.spatial.transform import Rotation as _R

_POS_RE = re.compile(
    r'P\[(\d+)\]\{.*?X\s*=\s*([-\d.]+).*?Y\s*=\s*([-\d.]+).*?Z\s*=\s*([-\d.]+)'
    r'.*?W\s*=\s*([-\d.]+).*?P\s*=\s*([-\d.]+).*?R\s*=\s*([-\d.]+)',
    re.DOTALL | re.IGNORECASE)

# a motion instruction line, e.g.  "  12:L P[99] R[23:moving]mm/sec CNT100    ;"
_MOVE_RE = re.compile(r'^\s*\d+:\s*[LJC]\s*P\[(\d+)\]', re.MULTILINE)

# jump/segment ratio above which a move counts as approach/retreat rather than cutting
WHISKER_JUMP_FACTOR = 3.0


class Program:
    """A parsed .LS program."""

    def __init__(self, text, path=None):
        self.text = text
        self.path = path
        self.points = {}
        for m in _POS_RE.finditer(text):
            self.points[int(m.group(1))] = tuple(float(m.group(k)) for k in range(2, 8))
        self.order = [int(m.group(1)) for m in _MOVE_RE.finditer(text)]

    def xyz(self, idx):
        return np.array(self.points[idx][:3])

    def path_xyz(self):
        """XYZ in true traversal order."""
        ids = self.order if len(self.order) >= 5 else sorted(self.points)
        return np.array([self.points[i][:3] for i in ids])

    def path_wpr(self):
        ids = self.order if len(self.order) >= 5 else sorted(self.points)
        return np.array([self.points[i][3:] for i in ids])

    def split_path(self):
        """(approach_ids, contour_ids, retreat_ids) in traversal order.

        Approach/retreat are the leading/trailing moves whose length is far above the
        median cutting step. They are fixed machine-space safety positions, not part of
        the helmet's rigid body, and must never be rotated with the trajectory.
        """
        ids = self.order
        if len(ids) < 5:
            ids = sorted(self.points)
        P = np.array([self.points[i][:3] for i in ids])
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
        if len(seg) < 4:
            return [], list(ids), []
        med = float(np.median(seg))
        thr = med * WHISKER_JUMP_FACTOR
        lo = 0
        while lo < len(seg) and seg[lo] > thr:
            lo += 1
        hi = len(ids) - 1
        while hi > 0 and seg[hi - 1] > thr:
            hi -= 1
        return ids[:lo], ids[lo:hi + 1], ids[hi + 1:]

    def contour_xyz(self):
        _, c, _ = self.split_path()
        return np.array([self.points[i][:3] for i in c]), c


def cut_ring(prog):
    """Contour points with the lead-in dropped, for SHAPE matching only.

    The first cutting move after the approach is a pierce/lead-in placed for the
    burn-through, not from the part geometry - it drags any fit if left in."""
    P, ids = prog.contour_xyz()
    if len(P) < 10:
        return P, ids
    return P[1:], ids[1:]


def load(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return Program(f.read(), path)


PROGRAM_PREFIX = "DISTI"


def program_name(session):
    """Program name for a session's export. Unique per run, Fanuc-safe."""
    m = re.search(r'(\d{8})_(\d{6})', session)
    if m:
        return f"{PROGRAM_PREFIX}_{m.group(1)[4:]}_{m.group(2)}"
    s = re.sub(r'[^A-Za-z0-9]+', '_', session).upper().strip('_')
    return f"{PROGRAM_PREFIX}_{s}"[:17]


def resample_closed(P, n):
    """Resample a closed contour to n points, uniformly by arc length."""
    Q = np.vstack([P, P[0]])
    d = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
    t = np.linspace(0.0, d[-1], n, endpoint=False)
    return np.column_stack([np.interp(t, d, Q[:, k]) for k in range(3)])


def curve_distance(pts, curve):
    """Exact point-to-SEGMENT distance from each of pts to the closed polyline `curve` (mm)."""
    P = np.asarray(pts, dtype=float)
    C = np.asarray(curve, dtype=float)
    A = C
    B = np.roll(C, -1, axis=0)
    AB = B - A
    denom = (AB * AB).sum(1)
    denom[denom == 0] = 1e-12
    AP = P[:, None, :] - A[None, :, :]
    t = np.clip((AP * AB[None, :, :]).sum(2) / denom[None, :], 0.0, 1.0)
    closest = A[None, :, :] + t[:, :, None] * AB[None, :, :]
    return np.linalg.norm(P[:, None, :] - closest, axis=2).min(axis=1)


# -- pose conventions --------------------------------------------------------
#
# ONE convention, used for both directions. Fanuc's W/P/R are fixed-angle rotations about
# the world X, Y, Z axes applied in that order, i.e. R = Rz(R)*Ry(P)*Rx(W) - exactly
# scipy's INTRINSIC 'ZYX' with [yaw, pitch, roll]. Always go through these two functions,
# not as_euler('zyx', ...) (lowercase = extrinsic, a different composition, worth ~0.4mm).

def rot_from_ypr(yaw, pitch, roll):
    return _R.from_euler('ZYX', [yaw, pitch, roll], degrees=True)


def ypr_from_rot(rot):
    if not isinstance(rot, _R):
        rot = _R.from_matrix(np.asarray(rot, dtype=float))
    yaw, pitch, roll = rot.as_euler('ZYX', degrees=True)
    return float(yaw), float(pitch), float(roll)


# -- standoff and the cut line -----------------------------------------------
#
# A recorded pose is the CUT POINT plus a standoff along the tool axis: the cut point is
# where the beam lands (the product), the standoff is slack (the beam travels ALONG the
# tool axis, so sliding the nozzle along it does not move the cut point at all).

NOMINAL_STANDOFF = 10.0


def tool_axes(prog, ids):
    """Unit tool +Z at each of the given points. Points AWAY from the part."""
    return np.array([rot_from_ypr(r, p, w).apply([0.0, 0.0, 1.0])
                     for w, p, r in (prog.points[i][3:] for i in ids)])


def kabsch(A, B):
    """Rigid transform (R, t) taking A onto B, paired by index."""
    A = np.asarray(A, dtype=float)
    B = np.asarray(B, dtype=float)
    ca, cb = A.mean(0), B.mean(0)
    H = (A - ca).T @ (B - cb)
    U, _, Vt = np.linalg.svd(H)
    D = np.diag([1.0, 1.0, np.sign(np.linalg.det(Vt.T @ U.T))])
    Rm = Vt.T @ D @ U.T
    return Rm, cb - Rm @ ca


def icp(A, B, iters=40, n=900):
    """Rigid transform taking contour A onto contour B, without point correspondences."""
    Bd = resample_closed(np.asarray(B, dtype=float), n)
    A = np.asarray(A, dtype=float)
    Rm, t, X = np.eye(3), np.zeros(3), A.copy()
    for _ in range(iters):
        j = np.linalg.norm(X[:, None, :] - Bd[None, :, :], axis=2).argmin(1)
        Rm, t = kabsch(A, Bd[j])
        X = A @ Rm.T + t
    return Rm, t


def cut_surface(prog, standoff, full=False):
    """(cut line, ids): the nozzle path pushed back along the tool axis by `standoff`.

    full=False drops the lead-in (matching cut_ring) for matching/scoring; full=True
    keeps every contour point, which is what export needs (the lead-in is a real move)."""
    P, ids = (prog.contour_xyz() if full else cut_ring(prog))
    return P - float(standoff) * tool_axes(prog, ids), ids


def fit_standoff(prog, ref_surface, grid=None):
    """Standoff at which this program's cut line best matches a reference cut line.

    All archive variants are the same physical helmet, so their cut lines must coincide up
    to a rigid pose - the standoff is the one parameter that breaks that (a shape change,
    not a rigid motion), hence identifiable this way. Returns (standoff, residual_mm)."""
    if grid is None:
        grid = np.arange(-6.0, 26.01, 0.5)

    def resid(d):
        S, _ = cut_surface(prog, d)
        Rm, t = icp(S, ref_surface)
        return float(curve_distance(S @ Rm.T + t, ref_surface).mean())

    e = np.array([resid(d) for d in grid])
    k = int(e.argmin())
    off = 0.0
    if 0 < k < len(grid) - 1:
        y0, y1, y2 = e[k - 1], e[k], e[k + 1]
        den = y0 - 2 * y1 + y2
        if abs(den) > 1e-12:
            off = 0.5 * (y0 - y2) / den * (grid[1] - grid[0])
    return float(grid[k] + off), float(e[k])
