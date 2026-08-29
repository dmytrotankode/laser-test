"""The pose optimizer - vendored from service_3030/exp_top_contour.py (resid_of,
top_contour, mode='contour' only - box2/box3 modes are diagnostic-only and not on the
production hot path) and service_3030/exp_three_cams.py (marker_cams).

Fits a 7-parameter pose (6-DOF rigid motion + one radial "skirt" allowance) so the CAD
rim, offset from cut-line to fold-line by the fixed FOLD_RADIAL/FOLD_UP constants,
lands on: the manual back/left fold-line marks, and the top-view mask contour.

FOLD_RADIAL/FOLD_UP are passed in (from the recipe's `constants`), not hardcoded here -
that is what lets a recipe pin a different physical-offset measurement for comparison
without editing this file.
"""
import os

import cv2
import numpy as np

from . import camera_model as E
from . import segmentation

_TOP_CONTOUR_CACHE = {}
_MASK_BOX_CACHE = {}


def resample(a, n=120):
    """Resample a 2D polyline (manual line mark) to n points along its length."""
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(a, axis=0).T))]
    t = np.linspace(0, d[-1], n)
    return np.c_[np.interp(t, d, a[:, 0]), np.interp(t, d, a[:, 1])]


def radial(P):
    """Outward from the dome axis - the direction the fold sits offset from the cut."""
    c = P.mean(0)
    v = P - c
    v[:, 2] = 0
    return v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-9)


def marker_cams(calib_dir):
    """{view: (pose6, focal_px)} from a calib/cameras/<name>/ directory."""
    out = {}
    for v in ('back', 'left', 'top'):
        z = np.load(os.path.join(calib_dir, f'cam_{v}.npy'))
        out[v] = (z[:6], z[6])
    return out


def mask_box3(archive_dir, variant, view):
    """Reference silhouette landmarks (top row, left/right edges) for a view."""
    key = (variant, view)
    if key not in _MASK_BOX_CACHE:
        path = os.path.join(archive_dir, variant, f'{view}.png')
        m, _, _, _, _ = segmentation.segment_image(path, view == 'top')
        ys, xs = np.where(m > 0)
        _MASK_BOX_CACHE[key] = (float(ys.min()), float(xs.min()), float(xs.max()))
    return _MASK_BOX_CACHE[key]


def top_contour(archive_dir, variant, n=160):
    """Top-view mask contour, evenly resampled to n points."""
    if variant not in _TOP_CONTOUR_CACHE:
        path = os.path.join(archive_dir, variant, 'top.png')
        m, _, _, _, _ = segmentation.segment_image(path, True)
        c = max(cv2.findContours((m > 0).astype(np.uint8), cv2.RETR_EXTERNAL,
                                 cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)
        p = c[:, 0, :].astype(float)
        k = np.linspace(0, len(p) - 1, n).astype(int)
        _TOP_CONTOUR_CACHE[variant] = p[k]
    return _TOP_CONTOUR_CACHE[variant]


def resid_of(archive_dir, variant, rim, verts, marks, cams, R0, t0, fold_radial, fold_up):
    """Residual function for scipy.optimize.least_squares - the actual pose fit.

    Combines: back/left fold-line-mark distance, a back/left silhouette bounding-box
    check against the full STL vertex set (`verts` - catches the model drifting outside
    the photographed silhouette even where the rim/mark residuals are locally flat), and
    the top-view contour-vs-mask distance with a free radial "skirt" allowance (uncut
    kevlar sticking out beyond the CAD rim in the photo).

    Fold-line marks are OPTIONAL (2026-08-29): manual marking takes real operator time
    that production can't always spare, and the mark distance is only one of three
    terms here - the silhouette box-check and top-contour terms still constrain the fit
    without it, just less tightly. `marks` may be missing the variant entirely, or have
    only one of back/left (load_marks() already drops any view with under 3 points) -
    either way, that view's mark term is skipped rather than raising, and the operator
    can always tighten the result afterward via the per-point correction UI.
    """
    off = fold_radial * radial(rim)
    off[:, 2] += fold_up
    rad = radial(rim)
    var_marks = marks.get(variant, {})

    def resid(p):
        R = cv2.Rodrigues(p[:3])[0] @ R0
        fold = (rim + off) @ R.T + t0 + p[3:6]
        out = []
        for w in ('back', 'left'):
            if w not in var_marks:
                continue
            pc, f = cams[w]
            uv, z = E.project(fold, pc[:3], pc[3:6], f)
            d = np.abs(E.dist_to_polyline(resample(var_marks[w]), E.near_arc(uv, z)))
            out.append(d * float(np.median(z)) / f / np.sqrt(len(d)))
        V = verts @ R.T + t0 + p[3:6]
        for w in ('back', 'left'):
            pc, f = cams[w]
            uv, z = E.project(V, pc[:3], pc[3:6], f)
            got = np.array([uv[:, 1].min(), uv[:, 0].min(), uv[:, 0].max()])
            want = np.array(mask_box3(archive_dir, variant, w))
            out.append((got - want) * float(np.median(z)) / f / np.sqrt(3))
        skirt = p[6]
        edge = (rim + skirt * rad) @ R.T + t0 + p[3:6]
        pc, f = cams['top']
        uv, z = E.project(edge, pc[:3], pc[3:6], f)
        q = top_contour(archive_dir, variant)
        d = np.abs(E.dist_to_polyline(q, uv))
        out.append(d * float(np.median(z)) / f / np.sqrt(len(d)))
        return np.concatenate(out)
    return resid
