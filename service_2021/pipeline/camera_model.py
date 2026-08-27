"""Pinhole camera projection - vendored from service_3030/exp_camera_fit.py.

Pure math, no I/O. Same convention as ../ls_points.py's camera contract: rotation is a
Rodrigues vector, `C` is the camera center, principal point at the image center, no
distortion.
"""
import numpy as np
import cv2

IMG_W, IMG_H = 4096, 3000


def project(X, rvec, C, f):
    """World points X (n,3) -> pixel (u,v) and camera-space depth z."""
    R = cv2.Rodrigues(np.asarray(rvec, float))[0]
    Xc = (np.asarray(X, float) - np.asarray(C, float)) @ R.T
    z = np.maximum(Xc[:, 2], 1e-6)
    return np.c_[f * Xc[:, 0] / z + IMG_W / 2, f * Xc[:, 1] / z + IMG_H / 2], Xc[:, 2]


def dist_to_polyline(P, R):
    """Signed distance from each 2D point in P to the polyline R (nearest segment).

    Plus = below the reference line in the frame. Vendored from service_3030/bench.py -
    used for image-space line-mark residuals (not geometry.curve_distance, which is the
    unsigned 3D closed-contour distance used for shape comparison).
    """
    A, B = R[:-1], R[1:]
    AB = B - A
    L2 = (AB ** 2).sum(1)
    L2[L2 == 0] = 1e-9
    AP = P[:, None, :] - A[None, :, :]
    t = np.clip((AP * AB[None]).sum(2) / L2[None], 0, 1)
    proj = A[None] + t[:, :, None] * AB[None]
    dv = P[:, None, :] - proj
    d = np.hypot(dv[:, :, 0], dv[:, :, 1])
    j = np.argmin(d, axis=1)
    i = np.arange(len(P))
    n = np.c_[-AB[j][:, 1], AB[j][:, 0]]
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    n[n[:, 1] < 0] *= -1
    sign = np.sign((dv[i, j] * n).sum(1))
    return d[i, j] * np.where(sign == 0, 1, sign)


def near_arc(uv, z):
    """The near half of a closed ring: the far side isn't facing the camera.

    Takes the longest contiguous run of near-side (z below median) points around the
    ring, so the far side's projection can't pull a fit toward it.
    """
    m = z < np.median(z)
    n = len(m)
    best = cur = start = bs = 0
    for i in range(2 * n):
        if m[i % n]:
            if cur == 0:
                start = i
            cur += 1
            if cur > best:
                best, bs = cur, start
        else:
            cur = 0
    return uv[[(bs + i) % n for i in range(min(best, n))]]
