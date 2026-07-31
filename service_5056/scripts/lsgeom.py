"""Shared Fanuc .LS geometry helpers.

Everything here is deliberately ORDER-INDEPENDENT where it can be. The point numbering
in .LS files is not consistent between the two archive batches:

    old batch (v1-v6):   P[1]=approach, contour = P[2], P[99], P[3]..P[97], P[98]=retreat
    new batch (v7-v16):  P[1]=approach, contour = P[2]..P[98],               P[99]=retreat

Both are fully described by the motion instructions in /MN, so we read the traversal
order from there instead of guessing from the P-index. An earlier attempt to normalise
this by physically re-indexing the files (ICP + Hungarian matching) destroyed the /MN
section of v7..v13 and dropped one point per file; it is not used any more.
"""
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

    # -- validity ---------------------------------------------------------
    def problems(self):
        """List of structural problems; empty list means the file is loadable by a robot."""
        bad = []
        if not self.points:
            bad.append("no P[i] position records")
        if len(self.order) < 5:
            bad.append(f"only {len(self.order)} motion instructions in /MN "
                       f"(program body missing or corrupted)")
        missing = [i for i in self.order if i not in self.points]
        if missing:
            bad.append(f"motion references undefined points: {sorted(set(missing))}")
        if '/END' not in self.text:
            bad.append("no /END marker")
        return bad

    # -- geometry ---------------------------------------------------------
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
            # /MN unusable (corrupted file). Fall back to P-index order so callers still
            # get a usable contour instead of silently including the approach/retreat
            # points, which sit hundreds of mm away and wreck any distance measurement.
            # problems() still reports the file as broken.
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


def load(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return Program(f.read(), path)


# -- resampling / blending -------------------------------------------------

def resample_closed(P, n):
    """Resample a closed contour to n points, uniformly by arc length.

    Parameter origin stays at P[0], so the result is comparable between calls only
    after phase alignment (see align_phase)."""
    Q = np.vstack([P, P[0]])
    d = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
    t = np.linspace(0.0, d[-1], n, endpoint=False)
    return np.column_stack([np.interp(t, d, Q[:, k]) for k in range(3)])


def eval_at_arc(P, u):
    """Evaluate a closed polyline at normalised arc positions u, exactly on the polyline.

    Unlike resampling to a fixed grid and indexing into it, this never cuts a corner:
    asking for a vertex's own arc position returns that vertex bit-for-bit. That matters
    because the contour has a genuine ~50 deg corner near the ear, where a 1 mm chord
    already costs ~0.4 mm."""
    P = np.asarray(P, dtype=float)
    Q = np.vstack([P, P[0]])
    d = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
    total = d[-1]
    t = (np.asarray(u, dtype=float) % 1.0) * total
    return np.column_stack([np.interp(t, d, Q[:, k]) for k in range(3)])


def arc_params(P):
    """Normalised arc-length position in [0,1) of each vertex of a closed contour."""
    P = np.asarray(P, dtype=float)
    Q = np.vstack([P, P[0]])
    d = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
    return d[:-1] / d[-1]


def phase_offset(A, B, n=1440):
    """Arc-parameter shift du such that B(u + du) corresponds to A(u).

    The two archive batches start their contour at different physical places, so without
    this the correspondence is off by a full ~10 mm step and any blend of them lands
    beside both curves instead of between them."""
    u = np.linspace(0.0, 1.0, n, endpoint=False)
    a = eval_at_arc(A, u)
    best, best_du = None, 0.0
    for k in range(n):
        b = eval_at_arc(B, u + k / n)
        e = float(((a - b) ** 2).sum())
        if best is None or e < best:
            best, best_du = e, k / n
    return best_du


def blend_contours(contours, weights, at=None):
    """Weighted blend of closed contours, evaluated at the FIRST contour's own vertices.

    Implemented as a displacement field on top of contours[0]: each other contour is
    phase-aligned and sampled at the matching arc positions, and the weighted mean of the
    offsets is added. With a single contour (weight 1.0) the result is exactly its own
    vertices - no resampling error at all, which keeps the zero-delta identity exact."""
    ref = np.asarray(contours[0], dtype=float)
    u = arc_params(ref) if at is None else np.asarray(at, dtype=float)
    base = eval_at_arc(ref, u)
    w = np.asarray(weights, dtype=float)
    w = w / w.sum()
    acc = np.zeros_like(base)
    for wi, C in zip(w, contours):
        C = np.asarray(C, dtype=float)
        if C.shape == ref.shape and np.allclose(C, ref):
            acc += wi * base
        else:
            acc += wi * eval_at_arc(C, u + phase_offset(ref, C))
    return acc


# -- metric ----------------------------------------------------------------

def curve_distance(pts, curve):
    """Exact distance from each of pts to the closed polyline `curve` (mm).

    Point-to-SEGMENT, not point-to-sampled-point: a sampled version has a resolution
    floor of half the sample spacing (0.12 mm at 4000 samples over this contour), which
    is enough to mask the very invariances the test suite is trying to prove.

    This is the metric that matters: the cut is a continuous path, so a point that has
    slid ALONG the path is harmless, while point-to-point index-wise comparison would
    penalise it as if it had left the path."""
    P = np.asarray(pts, dtype=float)
    C = np.asarray(curve, dtype=float)
    A = C
    B = np.roll(C, -1, axis=0)                     # closed: last segment wraps to first
    AB = B - A                                     # (m,3)
    denom = (AB * AB).sum(1)
    denom[denom == 0] = 1e-12
    AP = P[:, None, :] - A[None, :, :]             # (n,m,3)
    t = np.clip((AP * AB[None, :, :]).sum(2) / denom[None, :], 0.0, 1.0)
    closest = A[None, :, :] + t[:, :, None] * AB[None, :, :]
    return np.linalg.norm(P[:, None, :] - closest, axis=2).min(axis=1)


# -- pose conventions ------------------------------------------------------
#
# ONE convention, used for both directions. Fanuc's W/P/R are fixed-angle rotations
# about the world X, Y, Z axes applied in that order, i.e. R = Rz(R)*Ry(P)*Rx(W),
# which is exactly scipy's INTRINSIC 'ZYX' with [yaw, pitch, roll].
#
# The codebase used to apply from_euler('ZYX', ...) but extract with
# as_euler('zyx', ...) - lowercase is EXTRINSIC, a different composition
# (Rx*Ry*Rz). At the angles present in this data that mismatch is worth ~0.4 mm
# mean on the contour, comparable to the whole measurement noise floor, so it is
# not cosmetic. Always go through these two functions.

def rot_from_ypr(yaw, pitch, roll):
    """Rotation from yaw/pitch/roll in degrees (Fanuc-consistent: Rz*Ry*Rx)."""
    return _R.from_euler('ZYX', [yaw, pitch, roll], degrees=True)


def ypr_from_rot(rot):
    """Inverse of rot_from_ypr. Accepts a Rotation or a 3x3 matrix; returns
    (yaw, pitch, roll) in degrees."""
    if not isinstance(rot, _R):
        rot = _R.from_matrix(np.asarray(rot, dtype=float))
    yaw, pitch, roll = rot.as_euler('ZYX', degrees=True)
    return float(yaw), float(pitch), float(roll)
