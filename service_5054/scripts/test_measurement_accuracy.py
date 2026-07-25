"""
Systematic accuracy characterization of the heuristic's own 2D measurement
layer (find_2d_transform + M_base/M_total combination + the x_3d/y_3d/z_3d/
roll/pitch/yaw formulas in step06_fit_3d.py), using clean synthetic renders
with EXACTLY known ground truth - no real-photo noise, no segmentation
noise, isolates whether the MEASUREMENT ITSELF is trustworthy before
building any correction on top of it (see MEASUREMENT_ACCURACY.md for the
full write-up of what this found).

Each case is deterministic (find_2d_transform is a grid search, no
randomness) - reproducible by construction.

Usage: python scripts/test_measurement_accuracy.py [--session SESSION]
"""
import argparse
import os
import sys
import json
import numpy as np
import cv2
from scipy.spatial.transform import Rotation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render3d import render_silhouette, get_camera_pose, NAME_MAP_RU
from pivot_utils import load_world_vertices, find_apex_pivot
from step06_fit_3d import find_2d_transform, get_px_to_mm_per_camera

IMG_W, IMG_H = 4096, 3000
NAME_MAP_RU_LOCAL = {'back': 'Сзади', 'left': 'Слева', 'top': 'Сверху'}


def get_m_base(target_mask, proj_mask):
    coords_t = cv2.findNonZero(target_mask)
    coords_p = cv2.findNonZero(proj_mask)
    M_base = np.zeros((2, 3), dtype=np.float64)
    M_base[0, 0] = 1.0
    M_base[1, 1] = 1.0
    if coords_t is not None and coords_p is not None:
        xt, yt, wt, ht = cv2.boundingRect(coords_t)
        xp, yp, wp, hp = cv2.boundingRect(coords_p)
        base_scale = min(wt / float(wp) if wp > 0 else 1.0, ht / float(hp) if hp > 0 else 1.0)
        M_base[0, 0] = base_scale
        M_base[1, 1] = base_scale
        M_base[0, 2] = (xt + wt / 2.0) - (xp + wp / 2.0) * base_scale
        M_base[1, 2] = yt - yp * base_scale
    return M_base


def measure_total(target_mask, proj_mask, ru_cam_name):
    """Full replication of step06_fit_3d.py main()'s per-camera measurement -
    M_base pre-align, find_2d_transform fine search, M_total = M_fine @
    M_base - not just find_2d_transform's own raw output, since that's not
    what actually feeds global_3d in production."""
    h, w = target_mask.shape
    M_base = get_m_base(target_mask, proj_mask)
    proj_pre_aligned = cv2.warpAffine(proj_mask, M_base, (w, h), flags=cv2.INTER_NEAREST)
    fine_scale, rot, fine_du, fine_dv, fine_center = find_2d_transform(target_mask, proj_pre_aligned, ru_cam_name)
    M_fine_2x3 = cv2.getRotationMatrix2D(fine_center, rot, fine_scale)
    M_fine_2x3[0, 2] += fine_du
    M_fine_2x3[1, 2] += fine_dv
    M_base_3x3 = np.eye(3); M_base_3x3[0:2, :] = M_base
    M_fine_3x3 = np.eye(3); M_fine_3x3[0:2, :] = M_fine_2x3
    M_total = (M_fine_3x3 @ M_base_3x3)[0:2, :]
    total_rot = np.degrees(np.arctan2(M_total[1, 0], M_total[0, 0]))
    return total_rot, M_total[0, 2], M_total[1, 2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', default='run_20260723_122941')
    args = parser.parse_args()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    results_dir = os.path.join(base_dir, 'results', args.session)

    stl_path = os.path.join(base_dir, 'input', 'model_3d', 'helmet_ref.stl')
    with open(os.path.join(results_dir, 'step02_result.json')) as f:
        s2 = json.load(f)
    world = load_world_vertices(stl_path, s2)
    pivot = find_apex_pivot(world)
    with open(os.path.join(results_dir, 'step00_cameras.json'), encoding='utf-8') as f:
        step00_cams = json.load(f)
    center = (world.min(axis=0) + world.max(axis=0)) / 2.0
    px_to_mm = get_px_to_mm_per_camera(results_dir)

    cam_render = {}
    for cam in ['back', 'left', 'top']:
        pos, look_at, up = get_camera_pose(cam, center, step00_cams)
        f_px = step00_cams[NAME_MAP_RU[cam]]['f_px']
        cam_render[cam] = (pos, look_at, up, f_px)
    zero_masks = {cam: render_silhouette(world, *cam_render[cam][:3], cam_render[cam][3], IMG_W, IMG_H)
                  for cam in cam_render}

    def measure_case(rx=0.0, ry=0.0, rz=0.0, tx=0.0, ty=0.0, tz=0.0):
        R = Rotation.from_euler('ZYX', [rz, ry, rx], degrees=True).as_matrix()
        T = np.array([tx, ty, tz])
        posed = pivot + (R @ (world - pivot).T).T + T
        measured = {}
        for cam in ['back', 'left', 'top']:
            m = render_silhouette(posed, *cam_render[cam][:3], cam_render[cam][3], IMG_W, IMG_H)
            rot, du, dv = measure_total(m, zero_masks[cam], NAME_MAP_RU_LOCAL[cam])
            measured[cam] = {'rot': rot, 'du': du, 'dv': dv}
        rx_m = -measured['back']['rot']
        ry_m = -measured['left']['rot']
        rz_m = measured['top']['rot']
        x_m = (measured['left']['du'] * px_to_mm['left'] + measured['top']['du'] * px_to_mm['top']) / 2.0
        y_m = (-measured['back']['du'] * px_to_mm['back'] + measured['top']['dv'] * px_to_mm['top']) / 2.0
        z_m = (measured['back']['dv'] * px_to_mm['back'] + measured['left']['dv'] * px_to_mm['left']) / 2.0
        return rx_m, ry_m, rz_m, x_m, y_m, z_m

    print("=" * 70)
    print("TEST A: pure translation only (zero rotation)")
    print("=" * 70)
    for tx, ty, tz in [(5, 0, 0), (-5, 0, 0), (0, 5, 0), (0, -5, 0), (0, 0, 5), (0, 0, -5), (15, 0, 0), (0, 0, 15)]:
        _, _, _, x_m, y_m, z_m = measure_case(tx=tx, ty=ty, tz=tz)
        err = np.linalg.norm([x_m - tx, y_m - ty, z_m - tz])
        print(f"true T=({tx:+.0f},{ty:+.0f},{tz:+.0f})  measured=({x_m:+.2f},{y_m:+.2f},{z_m:+.2f})  error={err:.2f}mm")

    print()
    print("=" * 70)
    print("TEST B: pure rotation per axis, multiple magnitudes, both signs")
    print("=" * 70)
    for axis_name, axis_idx in [('roll (rx)', 0), ('pitch (ry)', 1), ('yaw (rz)', 2)]:
        print(f"\n--- {axis_name} ---")
        for mag in [1, 2, 3, 5, 8]:
            for true_val in [mag, -mag]:
                params = [0, 0, 0]
                params[axis_idx] = true_val
                rx_m, ry_m, rz_m, x_m, y_m, z_m = measure_case(rx=params[0], ry=params[1], rz=params[2])
                measured_val = [rx_m, ry_m, rz_m][axis_idx]
                trans_mag = np.linalg.norm([x_m, y_m, z_m])
                ratio = measured_val / true_val if true_val != 0 else float('nan')
                print(f"  true={true_val:+.1f}deg  measured={measured_val:+.2f}deg  ratio={ratio:+.2f}  "
                      f"spurious_translation={trans_mag:.2f}mm (x={x_m:+.1f} y={y_m:+.1f} z={z_m:+.1f})")

    print()
    print("=" * 70)
    print("TEST C: combined rotation+translation, realistic archive-set-like magnitudes")
    print("=" * 70)
    cases = [
        ('v1-like', -1.5, 0.5, 1.0, 0, 0, 0),
        ('v3-like', -3.0, 1.5, 1.0, 0, 0, 0),
        ('v5-like', -4.5, -4.0, -2.0, 0, 0, 0),
        ('v3-like + real T', -3.0, 1.5, 1.0, -3.2, 12.2, 21.6),
    ]
    for label, rx, ry, rz, tx, ty, tz in cases:
        rx_m, ry_m, rz_m, x_m, y_m, z_m = measure_case(rx=rx, ry=ry, rz=rz, tx=tx, ty=ty, tz=tz)
        print(f"{label}: true rot=({rx},{ry},{rz}) true T=({tx},{ty},{tz})")
        print(f"  measured rot=({rx_m:.2f},{ry_m:.2f},{rz_m:.2f}) measured T=({x_m:.2f},{y_m:.2f},{z_m:.2f})")


if __name__ == '__main__':
    main()
