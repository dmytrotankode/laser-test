"""
Self-calibrate per-camera f_px using the 5 archive/v1-v5 real photo sets as
calibration data, instead of a physical ChArUco/checkerboard shoot.

Why: step00_analyze_cameras.py derives f_px from ONE etalon photo's bounding
box plus an ASSUMED phys_size_mm (the working distance dist_mm is confirmed
correct by production - see ROADMAP.md "Направление 0" - so it is NOT a free
parameter here). A single-photo measurement fully inherits that one photo's
segmentation noise. A real ChArUco calibration was tried before and made
things WORSE (cause not diagnosed) and the saved calibration photos have no
cross-camera board overlap, so classical cv2.calibrateCamera isn't possible
with that data anyway (see ROADMAP.md for the full reasoning).

Instead: for each of v1-v5 we have an EXACT point correspondence between the
original etalon .ls and what production recorded (98 points, matched by id)
- so the true (rotation, translation) pose for each set can be computed
directly via Kabsch/Procrustes, with NO dependency on photos or segmentation.
Holding that ground-truth pose FIXED, render the model through each camera
with a candidate f_px and compare against the real segmented photo - fit
f_px (3 numbers total, dist_mm untouched) to minimize mismatch summed over
all 5 sets x 3 cameras (15 independent views instead of the 1 used by
calibrate_f_px in pose_fit_3d.py).

Caveat (see ROADMAP.md): calibrating and then validating on the same 5 sets
is optimistic - this is not a held-out test. Worth re-checking against new
archive sets once available.
"""
import os
import sys
import re
import json
import subprocess
import numpy as np
from scipy.optimize import minimize_scalar

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pose_fit_3d import (load_world_vertices, find_apex_pivot, load_mask,
                          iou_score, CUTOFF_FRACTION, IMG_W, IMG_H)
from render3d import render_silhouette, get_camera_pose, NAME_MAP_RU

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ARCHIVE_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'archive'))

REF_FILES = {
    'v1': 'TORXL_NEW_PROG2.LS',
    'v2': 'TORXL_NEW_PROG2_2.LS',
    'v3': 'TORXL_NEW_PROG2_3.LS',
    'v4': 'TORXL_NEW_PROG2_4.LS',
    'v5': 'TORXL_NEW_PROG2_5.LS',
}


def load_ls_points(path):
    pts = []
    pat = re.compile(
        r'P\[(\d+)\]\{[^}]*X\s*=\s*([-\d.]+)[^}]*Y\s*=\s*([-\d.]+)[^}]*Z\s*=\s*([-\d.]+)',
        re.IGNORECASE | re.DOTALL)
    txt = open(path, errors='replace').read()
    for m in pat.finditer(txt):
        pts.append((int(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))))
    return pts


def kabsch(src, dst):
    """Best-fit rotation+translation (no scale) mapping src -> dst. Returns R, t
    such that R@src_i + t ~= dst_i (least squares)."""
    csrc = src.mean(axis=0)
    cdst = dst.mean(axis=0)
    H = (src - csrc).T @ (dst - cdst)
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, d]) @ U.T
    t = cdst - R @ csrc
    return R, t


def ground_truth_pose(pivot):
    """For each archive set, exact (R, T-about-pivot) from direct point
    correspondence with the original etalon .ls (not a photo-based estimate)."""
    orig_path = os.path.join(BASE_DIR, 'input', 'ls_file', 'TORXL_NEW_PROG.LS')
    orig = load_ls_points(orig_path)
    o = np.array([[p[1], p[2], p[3]] for p in orig])
    mask = np.ones(len(o), dtype=bool)
    mask[[0, 97]] = False

    poses = {}
    for v, ref_file in REF_FILES.items():
        ref = load_ls_points(os.path.join(ARCHIVE_DIR, v, ref_file))
        r = np.array([[p[1], p[2], p[3]] for p in ref])[:98]
        R, t = kabsch(o[mask], r[mask])
        T = t + R @ pivot - pivot
        poses[v] = (R, T)
    return poses


def _copy_with_retry(src, dst, attempts=5, delay=1.0):
    """Windows occasionally raises a transient OSError (Errno 22) on a fresh
    copy right after a prior subprocess exits, likely AV/indexer touching the
    file - retrying after a short pause clears it (confirmed manually)."""
    import shutil
    import time
    last_err = None
    for i in range(attempts):
        try:
            shutil.copy(src, dst)
            return
        except OSError as e:
            last_err = e
            time.sleep(delay)
    raise last_err


def get_target_masks(session, v):
    """Swap in v's real photos, (re)run segmentation, load the resulting
    current_solid_{cam}.png masks. Restores photos_current via git checkout
    when the caller is done with ALL sets (see main)."""
    conv_dir = os.path.join(ARCHIVE_DIR, v, 'converted')
    files = sorted(f for f in os.listdir(conv_dir) if not f.lower().endswith('thumb.png'))
    frame1 = next(f for f in files if f.startswith('frame1_'))
    frame2 = next(f for f in files if f.startswith('frame2_'))
    frame3 = next(f for f in files if f.startswith('frame3_'))

    photos_dir = os.path.join(BASE_DIR, 'input', 'photos_current')
    _copy_with_retry(os.path.join(conv_dir, frame1), os.path.join(photos_dir, 'back.png'))
    _copy_with_retry(os.path.join(conv_dir, frame2), os.path.join(photos_dir, 'left.png'))
    _copy_with_retry(os.path.join(conv_dir, frame3), os.path.join(photos_dir, 'top.png'))

    subprocess.run([sys.executable, os.path.join(BASE_DIR, 'scripts', 'step05_segment_current.py'),
                     '--session', session], check=True, cwd=BASE_DIR)

    results_dir = os.path.join(BASE_DIR, 'results', session)
    masks = {}
    for cam in ['back', 'left', 'top']:
        masks[cam] = load_mask(os.path.join(results_dir, f'current_solid_{cam}.png'))
    return masks


def per_camera_mismatch(f_px, cam, world, pivot, poses, all_target_masks, cam_positions):
    """Given the ground-truth pose is FIXED per archive set, camera `cam`'s
    rendered silhouette depends ONLY on that camera's own f_px - the 3-camera
    joint problem decomposes into 3 independent 1D problems, no coupling.
    Much cheaper than a joint search and easier to sanity-check."""
    pos, look_at, up = cam_positions[cam]
    total = 0.0
    for v, (R, T) in poses.items():
        posed = pivot + (R @ (world - pivot).T).T + T
        rendered = render_silhouette(posed, pos, look_at, up, f_px, IMG_W, IMG_H)
        score = iou_score(rendered, all_target_masks[v][cam], CUTOFF_FRACTION[cam])
        total += (1.0 - score)
    return total / len(poses)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    args = parser.parse_args()

    results_dir = os.path.join(BASE_DIR, 'results', args.session)
    with open(os.path.join(results_dir, 'step02_result.json')) as f:
        s2 = json.load(f)
    with open(os.path.join(results_dir, 'step00_cameras.json'), encoding='utf-8') as f:
        step00_cams = json.load(f)

    stl_path = os.path.join(BASE_DIR, 'input', 'model_3d', 'helmet_ref.stl')
    world = load_world_vertices(stl_path, s2)
    pivot = find_apex_pivot(world)
    center = (world.min(axis=0) + world.max(axis=0)) / 2.0

    print("Computing exact ground-truth poses (point correspondence, not photo-based)...")
    poses = ground_truth_pose(pivot)
    for v, (R, T) in poses.items():
        angle = np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))
        print(f"  {v}: |T|={np.linalg.norm(T):.2f}mm angle={angle:.2f}deg")

    cam_positions = {}
    for cam in ['back', 'left', 'top']:
        cam_positions[cam] = get_camera_pose(cam, center, step00_cams)

    print("\nSegmenting real photos for all 5 archive sets (this takes a few minutes)...")
    all_target_masks = {}
    for v in REF_FILES:
        print(f"  {v}...")
        all_target_masks[v] = get_target_masks(args.session, v)

    # restore photos_current to whatever was committed before this script ran
    subprocess.run(['git', 'checkout', '--',
                     'input/photos_current/back.png',
                     'input/photos_current/left.png',
                     'input/photos_current/top.png'], cwd=BASE_DIR)

    f_px_initial = {c: step00_cams[NAME_MAP_RU[c]]['f_px'] for c in ['back', 'left', 'top']}
    print(f"\nInitial f_px (from step00, single-etalon-photo estimate): {f_px_initial}")

    f_px_calibrated = {}
    mismatch_initial = {}
    mismatch_calibrated = {}
    print("\nCalibrating f_px per camera (5 known ground-truth poses each, independent 1D search)...")
    for cam in ['back', 'left', 'top']:
        mismatch_initial[cam] = per_camera_mismatch(f_px_initial[cam], cam, world, pivot,
                                                      poses, all_target_masks, cam_positions)
        # search window: +-15% of the initial estimate is generous given the
        # single worst bug found so far (top camera) was ~7% off
        lo, hi = f_px_initial[cam] * 0.85, f_px_initial[cam] * 1.15
        res = minimize_scalar(per_camera_mismatch, bounds=(lo, hi), method='bounded',
                               args=(cam, world, pivot, poses, all_target_masks, cam_positions),
                               options={'xatol': 1.0})
        f_px_calibrated[cam] = float(res.x)
        mismatch_calibrated[cam] = float(res.fun)
        print(f"  {cam}: f_px {f_px_initial[cam]:.1f} -> {res.x:.1f} "
              f"(mismatch {mismatch_initial[cam]:.4f} -> {res.fun:.4f})")

    out = {
        'f_px_initial': f_px_initial,
        'f_px_calibrated': f_px_calibrated,
        'mismatch_initial': mismatch_initial,
        'mismatch_calibrated': mismatch_calibrated,
    }
    out_path = os.path.join(results_dir, 'camera_calibration_multipose.json')
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"Saved to {out_path}")


if __name__ == '__main__':
    main()
