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


def iou_score(rendered, target):
    r = rendered > 0
    t = target > 0
    inter = np.count_nonzero(r & t)
    union = np.count_nonzero(r | t)
    if union == 0:
        return 0.0
    return inter / union


def score_pose(params, world_vertices, pivot, etalon_center, step00_cams, target_masks, cam_cache=None):
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

    total_iou = 0.0
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
        total_iou += iou_score(rendered, target_masks[cam_name])
    return total_iou / 3.0


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

    if args.probe:
        cam_cache = {}
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
            s = score_pose(params, world, pivot, center, step00_cams, target_masks, cam_cache)
            print(f"{label}: mean IoU = {s:.4f}")
        return


if __name__ == '__main__':
    main()
