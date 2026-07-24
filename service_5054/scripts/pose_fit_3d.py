"""
3D pose fit around the known physical pivot (ball/crown contact) - replaces
the per-camera 2D heuristic (find_2d_transform in step04/06) with a direct
3D search: for a candidate (rotation about pivot P, residual translation),
render the model into all 3 camera views (render3d.py, no browser) and
score against the real segmented masks. See KNOWN_ISSUES.md [7].

Not yet wired into app.py / the session flow - standalone for testing on
the branch until validated against archive/v1-v5.
"""
import os
import sys
import json
import numpy as np
import cv2
from stl import mesh
from scipy.spatial.transform import Rotation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render3d import render_silhouette, get_camera_pose, NAME_MAP_RU

IMG_W, IMG_H = 4096, 3000


def get_rotation_matrix(rx, ry, rz):
    rx, ry, rz = np.radians(rx), np.radians(ry), np.radians(rz)
    Rx = np.array([[1, 0, 0], [0, np.cos(rx), -np.sin(rx)], [0, np.sin(rx), np.cos(rx)]])
    Ry = np.array([[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]])
    Rz = np.array([[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def load_world_vertices(stl_path, s2):
    R = get_rotation_matrix(s2['rx'], s2['ry'], s2['rz'])
    m = mesh.Mesh.from_file(stl_path)
    verts = m.vectors.reshape(-1, 3)
    world = (R @ (verts * s2['scale']).T).T + np.array([s2['tx'], s2['ty'], s2['tz']])
    return world


def find_apex_pivot(world_vertices):
    """Crown apex = centroid of the narrowest tip of the dome (min world-Z
    for this STL/alignment - verified 2026-07-24 by checking the radius
    profile actually narrows there, not just picking an extreme blindly)."""
    z = world_vertices[:, 2]
    zmin = z.min()
    tip = world_vertices[z < zmin + 3]
    return tip.mean(axis=0)


def calibrate_f_px(world_vertices, center, step00_cams, results_dir):
    """step00_analyze_cameras.py derives f_px from an ASSUMED physical size
    and working distance per camera - if either assumption is off, f_px is
    off by the same factor, and nothing downstream can tell (self-consistent
    but wrong). Found empirically 2026-07-24: rendering the model at zero
    pose and comparing against the real ETALON segmentation (not a "current"
    photo, so this is independent of any actual pose-fit test) shows back/
    left within ~1%, but "top" off by ~7% (render bigger than the real
    photo) - consistent with the OLD 2D-heuristic pipeline's own etalon
    self-check, which separately found top's scale (0.924) noticeably worse
    than back/left (0.977/0.981). Re-derive f_px directly from this size
    ratio instead of trusting step00's number blindly."""
    from render3d import get_camera_pose as _get_cam_pose

    calibrated = {}
    for cam_name in ['back', 'left', 'top']:
        pos, look_at, up = _get_cam_pose(cam_name, center, step00_cams)
        f_px = step00_cams[NAME_MAP_RU[cam_name]]['f_px']
        rendered = render_silhouette(world_vertices, pos, look_at, up, f_px, IMG_W, IMG_H)
        etalon_mask = load_mask(os.path.join(results_dir, f'solid_{cam_name}.png'))

        r_nz = cv2.findNonZero(rendered)
        t_nz = cv2.findNonZero(etalon_mask)
        _, _, rw, rh = cv2.boundingRect(r_nz)
        _, _, tw, th = cv2.boundingRect(t_nz)
        ratio = ((rw / tw) + (rh / th)) / 2.0
        calibrated[cam_name] = f_px / ratio
        print(f"  f_px calibration [{cam_name}]: {f_px:.1f} -> {calibrated[cam_name]:.1f} (size ratio was {ratio:.4f})")
    return calibrated


def load_mask(path):
    data = np.fromfile(path, dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(path)
    if img.ndim == 3 and img.shape[2] == 4:
        mask = img[:, :, 3]
    else:
        gray = img if img.ndim == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
    return mask


# Bottom fraction of the frame to ignore per camera when scoring - the mount/
# stand is visible there in real photos (confirmed 2026-07-24: a bracket
# sticking out sideways in the "left" view, not cleanly removable by the old
# per-camera stand-removal heuristic, which only ever ran for "back" anyway),
# and it's also where the laser cut-zone/rim geometry is least trustworthy.
# Same convention (75%/90%) already used in the old 2D heuristic
# (find_2d_transform's cutoff), kept here for continuity, not re-derived.
CUTOFF_FRACTION = {"back": 0.75, "left": 0.75, "top": 0.90}


def iou_score(rendered, target, cutoff_frac=None):
    r = rendered > 0
    t = target > 0
    if cutoff_frac is not None:
        # Cutoff is a fraction of the way down the TARGET's own bounding box
        # (top of silhouette to bottom), not the whole image frame - the
        # helmet doesn't fill the frame, so a raw image-height fraction would
        # cut an arbitrary, inconsistent amount depending on framing. Uses
        # the target (real photo) as the reference for both images so the
        # same absolute region is excluded from each.
        rows = np.where(t.any(axis=1))[0]
        if len(rows) > 0:
            y0, y1 = rows[0], rows[-1]
            cutoff_y = int(y0 + (y1 - y0) * cutoff_frac)
            r = r.copy()
            t = t.copy()
            r[cutoff_y:, :] = False
            t[cutoff_y:, :] = False
    inter = np.count_nonzero(r & t)
    union = np.count_nonzero(r | t)
    if union == 0:
        return 0.0
    return inter / union


# Area-IoU barely responds to yaw for this helmet (empirically confirmed
# 2026-07-24: +-15deg changes IoU by <1%, see ROADMAP.md "Направление 1") -
# the dome is close to rotationally symmetric, so silhouette AREA looks
# almost the same at any yaw. The only place the shape is NOT symmetric is
# the rim/cut-edge near the bottom of the (post-cutoff) silhouette, and area
# overlap dilutes that small asymmetric region into a sea of symmetric dome
# pixels. A boundary/contour distance is far more sensitive to a rotated
# edge than an area ratio is, and weighting it toward the rim gives the
# optimizer an actual yaw signal instead of a nearly-flat one.
RIM_WEIGHT = 3.0
CHAMFER_WEIGHT = 0.5  # blend factor between area-IoU and rim-weighted chamfer


def _contour_points_and_boundary(mask_u8):
    contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return None, None
    boundary = np.zeros_like(mask_u8)
    cv2.drawContours(boundary, contours, -1, 255, 1)
    pts = np.concatenate([c.reshape(-1, 2) for c in contours], axis=0)
    return pts, boundary


def prep_target_chamfer(target, cutoff_frac):
    """Precompute the target's contour/distance-transform once per camera -
    it doesn't change across candidate poses within one optimization run, so
    this must NOT be recomputed on every score_pose() call (would dominate
    runtime for no reason)."""
    t = target > 0
    rows = np.where(t.any(axis=1))[0]
    if len(rows) == 0:
        return None
    y0, y1 = int(rows[0]), int(rows[-1])
    cutoff_y = int(y0 + (y1 - y0) * cutoff_frac) if cutoff_frac is not None else y1 + 1
    t = t.copy()
    t[cutoff_y:, :] = False
    t_u8 = (t * 255).astype(np.uint8)
    pts_t, boundary_t = _contour_points_and_boundary(t_u8)
    if pts_t is None:
        return None
    dt_t = cv2.distanceTransform(255 - boundary_t, cv2.DIST_L2, 5)
    return {'pts': pts_t, 'dt': dt_t, 'y0': y0, 'y1': y1, 'cutoff_y': cutoff_y}


def _rim_weights(pts, y0, span):
    y = pts[:, 1].astype(np.float64)
    frac = np.clip((y - y0) / span, 0.0, 1.0)
    return 1.0 + (RIM_WEIGHT - 1.0) * frac


def chamfer_score(rendered, target_prep):
    """Symmetric boundary chamfer distance between rendered and target
    silhouettes (cropped to the same cutoff as target_prep), weighted toward
    the rim (bottom of the post-cutoff region). Returns a score in [0, 1],
    higher = better match, comparable in scale to iou_score."""
    if target_prep is None:
        return 0.0
    r = rendered > 0
    r = r.copy()
    r[target_prep['cutoff_y']:, :] = False
    r_u8 = (r * 255).astype(np.uint8)
    pts_r, boundary_r = _contour_points_and_boundary(r_u8)
    pts_t, dt_t = target_prep['pts'], target_prep['dt']
    if pts_r is None:
        return 0.0
    dt_r = cv2.distanceTransform(255 - boundary_r, cv2.DIST_L2, 5)

    h, w = dt_t.shape
    px_r = np.clip(pts_r[:, 0], 0, w - 1)
    py_r = np.clip(pts_r[:, 1], 0, h - 1)
    px_t = np.clip(pts_t[:, 0], 0, w - 1)
    py_t = np.clip(pts_t[:, 1], 0, h - 1)

    d_r_to_t = dt_t[py_r, px_r]
    d_t_to_r = dt_r[py_t, px_t]

    span = max(target_prep['y1'] - target_prep['y0'], 1)
    w_r = _rim_weights(pts_r, target_prep['y0'], span)
    w_t = _rim_weights(pts_t, target_prep['y0'], span)

    mean_dist = (np.sum(d_r_to_t * w_r) + np.sum(d_t_to_r * w_t)) / (np.sum(w_r) + np.sum(w_t))
    normalized = mean_dist / span
    return max(0.0, 1.0 - normalized)


def score_pose(params, world_vertices, pivot, etalon_center, step00_cams, target_masks,
               cam_cache=None, chamfer_cache=None):
    """Cameras are physically fixed (bolted to the rig) and are always set up
    relative to the ETALON's own center - they must NOT move with the
    candidate pose, or every hypothesis looks identical (translating both the
    model and the camera together changes nothing relative to each other -
    caught this exact bug empirically: tx+5mm was scoring identically to
    zero). Only the MODEL moves per candidate pose."""
    rx, ry, rz, tx, ty, tz = params
    R = Rotation.from_euler('xyz', [rx, ry, rz], degrees=True).as_matrix()
    T = np.array([tx, ty, tz])
    posed = pivot + (R @ (world_vertices - pivot).T).T + T

    total_score = 0.0
    for cam_name in ['back', 'left', 'top']:
        if cam_cache is not None and cam_name in cam_cache:
            pos, look_at, up, f_px = cam_cache[cam_name]
        else:
            pos, look_at, up = get_camera_pose(cam_name, etalon_center, step00_cams)
            ru = NAME_MAP_RU[cam_name]
            f_px = step00_cams[ru]['f_px']
            if cam_cache is not None:
                cam_cache[cam_name] = (pos, look_at, up, f_px)
        rendered = render_silhouette(posed, pos, look_at, up, f_px, IMG_W, IMG_H)
        iou = iou_score(rendered, target_masks[cam_name], CUTOFF_FRACTION[cam_name])

        if chamfer_cache is not None:
            if cam_name not in chamfer_cache:
                chamfer_cache[cam_name] = prep_target_chamfer(target_masks[cam_name], CUTOFF_FRACTION[cam_name])
            chamfer = chamfer_score(rendered, chamfer_cache[cam_name])
            total_score += (1.0 - CHAMFER_WEIGHT) * iou + CHAMFER_WEIGHT * chamfer
        else:
            total_score += iou
    return total_score / 3.0


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    parser.add_argument('--probe', action='store_true',
                         help='Just print scores at a few hand-picked poses, no optimization')
    args = parser.parse_args()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    results_dir = os.path.join(base_dir, 'results', args.session)

    with open(os.path.join(results_dir, 'step02_result.json')) as f:
        s2 = json.load(f)
    with open(os.path.join(results_dir, 'step00_cameras.json'), encoding='utf-8') as f:
        step00_cams = json.load(f)

    stl_path = os.path.join(base_dir, 'input', 'model_3d', 'helmet_ref.stl')
    world = load_world_vertices(stl_path, s2)
    pivot = find_apex_pivot(world)
    center = (world.min(axis=0) + world.max(axis=0)) / 2.0
    print(f"pivot (crown apex) = {pivot}")
    print(f"center (bbox)      = {center}")

    target_masks = {}
    for cam_name in ['back', 'left', 'top']:
        target_masks[cam_name] = load_mask(os.path.join(results_dir, f'current_solid_{cam_name}.png'))

    multipose_calib_path = os.path.join(results_dir, 'camera_calibration_multipose.json')
    if os.path.exists(multipose_calib_path):
        print(f"Using multi-pose f_px calibration from {multipose_calib_path} "
              "(see scripts/calibrate_cameras_multipose.py)")
        with open(multipose_calib_path) as f:
            calibrated_f_px = json.load(f)['f_px_calibrated']
    else:
        print("Calibrating f_px per camera against the real etalon segmentation...")
        calibrated_f_px = calibrate_f_px(world, center, step00_cams, results_dir)
    cam_cache = {}
    for cam_name in ['back', 'left', 'top']:
        pos, look_at, up = get_camera_pose(cam_name, center, step00_cams)
        cam_cache[cam_name] = (pos, look_at, up, calibrated_f_px[cam_name])
    chamfer_cache = {}

    if args.probe:
        for label, params in [
            ('zero (no change from etalon)', [0, 0, 0, 0, 0, 0]),
            ('roll +2deg', [2, 0, 0, 0, 0, 0]),
            ('roll -2deg', [-2, 0, 0, 0, 0, 0]),
            ('roll +5deg', [5, 0, 0, 0, 0, 0]),
            ('pitch +2deg', [0, 2, 0, 0, 0, 0]),
            ('pitch -2deg', [0, -2, 0, 0, 0, 0]),
            ('yaw +2deg', [0, 0, 2, 0, 0, 0]),
            ('yaw -2deg', [0, 0, -2, 0, 0, 0]),
            ('tx +5mm', [0, 0, 0, 5, 0, 0]),
            ('tx -5mm', [0, 0, 0, -5, 0, 0]),
            ('ty +5mm', [0, 0, 0, 0, 5, 0]),
            ('tz +5mm', [0, 0, 0, 0, 0, 5]),
            ('roll -3, pitch -2, yaw -1', [-3, -2, -1, 0, 0, 0]),
            ('roll -3, pitch -2, yaw -1, tx-10,ty+15,tz+1', [-3, -2, -1, -10, 15, 1]),
        ]:
            s = score_pose(params, world, pivot, center, step00_cams, target_masks, cam_cache, chamfer_cache)
            print(f"{label}: score = {s:.4f}")
        return

    from scipy.optimize import minimize

    def neg_score(params):
        return -score_pose(params, world, pivot, center, step00_cams, target_masks, cam_cache, chamfer_cache)

    # Multi-start: a single Powell run can settle into a local optimum: start
    # from a handful of small, plausible initial guesses (rather than just
    # zero) and keep the best - same reasoning as step02_align_3d_to_trim.py's
    # multi-start Powell for the etalon fit.
    initial_guesses = [
        [0, 0, 0, 0, 0, 0],
        [2, -2, 0, 0, 0, 0],
        [-2, 2, 0, 0, 0, 0],
        [0, 0, 2, 0, 0, 0],
        [3, -3, -1, 0, 0, 0],
    ]

    best = None
    for guess in initial_guesses:
        res = minimize(neg_score, guess, method='Powell',
                        options={'maxiter': 200, 'xtol': 0.1, 'ftol': 1e-4})
        print(f"start={guess} -> score={-res.fun:.4f} params={np.round(res.x, 2)}")
        if best is None or res.fun < best.fun:
            best = res

    rx, ry, rz, tx, ty, tz = best.x
    print(f"\nBest: mean IoU = {-best.fun:.4f}")
    print(f"delta_rotvec (deg, xyz euler about pivot): roll={rx:.2f} pitch={ry:.2f} yaw={rz:.2f}")
    print(f"delta_translation (mm): x={tx:.2f} y={ty:.2f} z={tz:.2f}")

    out = {
        'pivot': pivot.tolist(),
        'iou_score': float(-best.fun),
        'delta_rotation_deg_xyz': [float(rx), float(ry), float(rz)],
        'delta_translation_mm': [float(tx), float(ty), float(tz)],
    }
    out_path = os.path.join(results_dir, 'pose_fit_3d_result.json')
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"Saved to {out_path}")


if __name__ == '__main__':
    main()
