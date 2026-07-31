import re
import numpy as np

BASE = "input"


def load_pts_full(path):
    content = open(path, 'r', encoding='utf-8', errors='ignore').read()
    pattern = re.compile(r'P\[(\d+)\]\{.*?X\s*=\s*([-\d.]+).*?Y\s*=\s*([-\d.]+).*?Z\s*=\s*([-\d.]+)', re.DOTALL | re.IGNORECASE)
    return [(int(i), float(a), float(b), float(c)) for i, a, b, c in pattern.findall(content)]


def trim_whiskers(pts, jump_factor=3.0):
    """Return (loop_pts, loop_indices) excluding big-jump approach/retreat points at both ends."""
    coords = np.array([[p[1], p[2], p[3]] for p in pts])
    seg = np.linalg.norm(np.diff(coords, axis=0), axis=1)
    normal_med = np.median(seg[len(seg)//4: 3*len(seg)//4])  # robust median from the "safe middle" of the path
    threshold = normal_med * jump_factor

    lo = 0
    while lo < len(seg) and seg[lo] > threshold:
        lo += 1
    hi = len(pts) - 1
    while hi > 0 and seg[hi - 1] > threshold:
        hi -= 1
    return pts[lo:hi + 1]


def rigid_fit(a, b):
    """Best-fit rotation+translation mapping a -> b (SVD, Kabsch)."""
    ca, cb = a.mean(axis=0), b.mean(axis=0)
    H = (a - ca).T @ (b - cb)
    U, S, Vt = np.linalg.svd(H)
    rot = Vt.T @ U.T
    if np.linalg.det(rot) < 0:
        Vt[2, :] *= -1
        rot = Vt.T @ U.T
    trans = cb - rot @ ca
    return rot, trans


def icp(ref, tgt, init_rot=None, iters=50, tol=1e-6):
    """Point-to-point ICP aligning tgt onto ref (different point counts allowed).
    Returns final rot, trans, and per-ref-point nearest tgt index (correspondence)."""
    ref = np.asarray(ref, dtype=float)
    tgt = np.asarray(tgt, dtype=float)

    if init_rot is None:
        rot = np.eye(3)
    else:
        rot = init_rot
    cref, ctgt = ref.mean(axis=0), tgt.mean(axis=0)
    trans = cref - rot @ ctgt

    prev_err = None
    corr_idx = None
    for _ in range(iters):
        moved = (rot @ tgt.T).T + trans
        # for each ref point, nearest moved-tgt point
        d = np.linalg.norm(ref[:, None, :] - moved[None, :, :], axis=2)
        corr_idx = np.argmin(d, axis=1)
        matched_tgt = tgt[corr_idx]
        rot, trans = rigid_fit(matched_tgt, ref)
        moved = (rot @ tgt.T).T + trans
        err = np.mean(np.min(np.linalg.norm(ref[:, None, :] - moved[None, :, :], axis=2), axis=1))
        if prev_err is not None and abs(prev_err - err) < tol:
            break
        prev_err = err
    return rot, trans, corr_idx, prev_err


def euler_zyx(rot):
    from scipy.spatial.transform import Rotation as R
    return R.from_matrix(rot).as_euler('zyx', degrees=True)  # yaw, pitch, roll


if __name__ == "__main__":
    cad_full = load_pts_full(f"{BASE}/ls_file/TORXL_NEW_PROG.LS")
    cad_loop = trim_whiskers(cad_full)
    cad_xyz = np.array([[p[1], p[2], p[3]] for p in cad_loop])
    print(f"CAD: full={len(cad_full)} loop={len(cad_loop)} (indices {cad_loop[0][0]}..{cad_loop[-1][0]})")

    for v in ['v1', 'v7', 'v8', 'v9', 'v10', 'v11', 'v12', 'v13', 'v14', 'v15', 'v16']:
        full = load_pts_full(f"{BASE}/archive/{v}/ground_truth.ls")
        loop = trim_whiskers(full)
        xyz = np.array([[p[1], p[2], p[3]] for p in loop])

        # Try several yaw initializations to avoid local minima (near-symmetric dome contour)
        best = None
        for yaw_guess in range(0, 360, 15):
            th = np.radians(yaw_guess)
            init_rot = np.array([
                [np.cos(th), -np.sin(th), 0],
                [np.sin(th), np.cos(th), 0],
                [0, 0, 1]
            ])
            rot, trans, corr, err = icp(cad_xyz, xyz, init_rot=init_rot)
            if best is None or err < best[3]:
                best = (rot, trans, corr, err)

        rot, trans, corr, err = best
        yaw, pitch, roll = euler_zyx(rot)
        print(f"{v}: full={len(full)} loop={len(loop)} (idx {loop[0][0]}..{loop[-1][0]})  "
              f"ICP mean_err={err:.3f}mm  yaw={yaw:.2f} pitch={pitch:.2f} roll={roll:.2f}  "
              f"trans={np.round(trans,2)}")
