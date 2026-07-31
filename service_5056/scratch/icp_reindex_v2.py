import numpy as np
from scipy.optimize import linear_sum_assignment
import sys
sys.path.insert(0, '.')
from icp_reindex_new_variants import load_pts_full, trim_whiskers, rigid_fit, euler_zyx


def icp_hungarian(ref, tgt, init_rot=None, iters=50, tol=1e-6):
    """Point-to-point ICP with OPTIMAL (Hungarian) one-to-one assignment per iteration,
    instead of greedy nearest-point (which can map multiple ref points to the same tgt point).
    ref: (n,3), tgt: (m,3) with m >= n. Returns rot, trans, corr (len n, values in [0,m)), err."""
    ref = np.asarray(ref, dtype=float)
    tgt = np.asarray(tgt, dtype=float)

    rot = np.eye(3) if init_rot is None else init_rot
    cref, ctgt = ref.mean(axis=0), tgt.mean(axis=0)
    trans = cref - rot @ ctgt

    prev_err = None
    corr = None
    for _ in range(iters):
        moved = (rot @ tgt.T).T + trans
        cost = np.linalg.norm(ref[:, None, :] - moved[None, :, :], axis=2)  # (n, m)
        row_ind, col_ind = linear_sum_assignment(cost)  # row_ind is sorted 0..n-1
        corr = col_ind
        matched_tgt = tgt[corr]
        rot, trans = rigid_fit(matched_tgt, ref)
        moved = (rot @ tgt.T).T + trans
        err = np.mean(np.linalg.norm(ref - moved[corr], axis=1))
        if prev_err is not None and abs(prev_err - err) < tol:
            break
        prev_err = err
    return rot, trans, corr, prev_err


if __name__ == "__main__":
    cad_full = load_pts_full("input/ls_file/TORXL_NEW_PROG.LS")
    cad_loop = trim_whiskers(cad_full)
    cad_xyz = np.array([[p[1], p[2], p[3]] for p in cad_loop])
    print(f"CAD loop: {len(cad_loop)} points")

    for v in ['v7', 'v8', 'v9', 'v10', 'v11', 'v12', 'v13']:
        full = load_pts_full(f"input/archive/{v}/ground_truth.ls")
        loop = trim_whiskers(full)
        xyz = np.array([[p[1], p[2], p[3]] for p in loop])

        best = None
        for yaw_guess in range(0, 360, 3):
            th = np.radians(yaw_guess)
            init_rot = np.array([[np.cos(th), -np.sin(th), 0], [np.sin(th), np.cos(th), 0], [0, 0, 1]])
            rot, trans, corr, err = icp_hungarian(cad_xyz, xyz, init_rot=init_rot)
            if best is None or err < best[3]:
                best = (rot, trans, corr, err)
        rot, trans, corr, err = best
        yaw, pitch, roll = euler_zyx(rot)
        dropped = sorted(set(range(len(loop))) - set(corr.tolist()))
        print(f"{v}: loop={len(loop)} err={err:.3f}mm yaw={yaw:.2f} pitch={pitch:.2f} roll={roll:.2f} dropped={dropped}")
