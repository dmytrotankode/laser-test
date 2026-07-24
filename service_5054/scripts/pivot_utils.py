"""
Loads the STL into world/LS space (using step02's alignment fit) and finds
the crown-apex pivot - the physical point the helmet actually rotates about
(ball/crown contact), as opposed to any arbitrary reference point.

Ported from the `3d-pose-fit` branch's pose_fit_3d.py (see
3D_POSE_FIT_STATUS.md there) to support lever_arm_correction.py on `main`.
"""
import numpy as np
from stl import mesh


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
    for this STL/alignment - verified by checking the radius profile
    actually narrows there, not just picking an extreme blindly). This is
    the physical point the helmet rotates about (ball/crown contact) -
    NOT the same as step02's own tx/ty/tz (that's just the STL's local
    origin after alignment, which for this model sits ~169mm away, near
    the opposite/rim end - see lever_arm_correction.py)."""
    z = world_vertices[:, 2]
    zmin = z.min()
    tip = world_vertices[z < zmin + 3]
    return tip.mean(axis=0)
