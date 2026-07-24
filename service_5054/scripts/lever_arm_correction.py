"""
Corrects step04_fit_masks.py's/step06_fit_3d.py's per-camera 2D-shift
measurement (find_2d_transform's du/dv) for lever-arm contamination.

Diagnosis (full detail in KNOWN_ISSUES.md [6]/[7], found while building the
`3d-pose-fit` branch): when the helmet rotates about its real physical pivot
(crown apex / ball contact, ~130-170mm from the visible silhouette's own
center), part of the apparent 2D silhouette shift measured by
find_2d_transform is caused by the rotation itself, not by any real
translation of the object - z_mm ended up almost exactly proportional to
rotation angle across all 5 archive sets (ratio ~-2.4mm/degree, implying an
"effective lever" of ~137mm - suspiciously close to the real ~140mm helmet
radius from the crown).

Given the ALREADY-measured rotation (rx_3d, ry_3d, rz_3d - measured directly
per camera from 2D image rotation, trusted as-is here), this predicts what
du/dv a PURE rotation (that same rotation, zero translation) about the crown
apex would produce on its own, by rendering the model at zero pose and at
the rotation-only pose (headless, via render3d.py - the same proven pinhole
projection already validated on the 3d-pose-fit branch) and comparing
silhouette centroids. step04/06 subtract this predicted contamination from
the raw measured du/dv BEFORE converting to x_3d/y_3d/z_3d, so the corrected
translation represents "translation of the crown apex" specifically -
step08_visualize.py's final pivot MUST match (crown apex, not step02's own
tx/ty/tz) or the same class of error re-appears one stage later. See the
git commit that introduced this file for the full reasoning; this is not
an optional cleanup, the two changes are mathematically coupled.
"""
import os
import sys
import json
import numpy as np
from scipy.spatial.transform import Rotation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render3d import render_silhouette, get_camera_pose, NAME_MAP_RU
from pivot_utils import load_world_vertices, find_apex_pivot

IMG_W, IMG_H = 4096, 3000

# Same convention already used by find_2d_transform's own cutoff (stand/mount
# visible at the bottom of "back"/"left", rim geometry least trustworthy at
# the very bottom of "top") - kept identical here so the synthetic-render
# centroid comparison crops the same region the real measurement does.
CUTOFF_FRACTION = {"back": 0.75, "left": 0.75, "top": 0.90}


def _silhouette_centroid(mask, cutoff_frac):
    m = mask > 0
    rows = np.where(m.any(axis=1))[0]
    if len(rows) == 0:
        return None
    y0, y1 = int(rows[0]), int(rows[-1])
    cutoff_y = int(y0 + (y1 - y0) * cutoff_frac)
    m = m.copy()
    m[cutoff_y:, :] = False
    ys, xs = np.where(m)
    if len(xs) == 0:
        return None
    return np.array([xs.mean(), ys.mean()])


def get_pivot_and_world(base_dir, results_dir):
    stl_path = os.path.join(base_dir, 'input', 'model_3d', 'helmet_ref.stl')
    with open(os.path.join(results_dir, 'step02_result.json')) as f:
        s2 = json.load(f)
    world = load_world_vertices(stl_path, s2)
    pivot = find_apex_pivot(world)
    return world, pivot


def predict_lever_arm_shift_px(world, pivot, rx_deg, ry_deg, rz_deg, step00_cams):
    """Returns {cam_name: (ddu, ddv)} - predicted full-resolution-pixel shift
    (same units as find_2d_transform's du/dv) caused by PURE rotation
    (rx_deg, ry_deg, rz_deg about the crown apex, zero translation) alone.
    Rotation convention matches step08_visualize.py exactly
    (R.from_euler('ZYX', [yaw, pitch, roll])) so the prediction stays
    consistent with what will actually be applied to the .ls file."""
    center = (world.min(axis=0) + world.max(axis=0)) / 2.0
    R = Rotation.from_euler('ZYX', [rz_deg, ry_deg, rx_deg], degrees=True).as_matrix()
    rotated = pivot + (R @ (world - pivot).T).T

    shifts = {}
    for cam_name in ['back', 'left', 'top']:
        pos, look_at, up = get_camera_pose(cam_name, center, step00_cams)
        f_px = step00_cams[NAME_MAP_RU[cam_name]]['f_px']
        rendered_zero = render_silhouette(world, pos, look_at, up, f_px, IMG_W, IMG_H)
        rendered_rot = render_silhouette(rotated, pos, look_at, up, f_px, IMG_W, IMG_H)
        c0 = _silhouette_centroid(rendered_zero, CUTOFF_FRACTION[cam_name])
        c1 = _silhouette_centroid(rendered_rot, CUTOFF_FRACTION[cam_name])
        if c0 is None or c1 is None:
            shifts[cam_name] = (0.0, 0.0)
        else:
            d = c1 - c0
            shifts[cam_name] = (float(d[0]), float(d[1]))
    return shifts
