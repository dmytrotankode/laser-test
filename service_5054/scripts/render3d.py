"""
Headless (no browser) 3D -> 2D silhouette rendering.

Ported from service_5050/scripts/step05_project.py (proven, already-tested
pinhole camera projection code) and adapted to match EXACTLY what
web/static/js/main.js's Three.js scene does when it captures model_mask_*.png
(same camera positions/distances, same up vectors, same look_at offset
correction from step00_cameras.json, same 4096x3000 render size) - so this
can replace the browser round-trip inside an optimization loop.

The camera convention here was cross-checked against main.js directly
(not assumed from code comments elsewhere, which turned out to be stale/
wrong for the top camera's up vector).
"""
import numpy as np
import cv2

CAMERA_DISTANCES_MM = {"back": 2500.0, "left": 1650.0, "top": 2000.0}
CAMERA_UP = {"back": [0, 0, -1], "left": [0, 0, -1], "top": [0, 1, 0]}
NAME_MAP_RU = {"back": "Сзади", "left": "Слева", "top": "Сверху"}


def project_points_vectorized(points, cam_pos, cam_look, cam_up, focal_length, w, h):
    Z = cam_look - cam_pos
    norm_Z = np.linalg.norm(Z)
    if norm_Z < 1e-6:
        return None
    Z = Z / norm_Z

    X = np.cross(Z, cam_up)
    norm_X = np.linalg.norm(X)
    if norm_X < 1e-6:
        X = np.array([1.0, 0.0, 0.0])
    else:
        X = X / norm_X

    Y = np.cross(Z, X)

    R = np.vstack([X, Y, Z])
    t = -R @ cam_pos

    p_cam = (R @ points.T).T + t

    valid = p_cam[:, 2] > 0

    u = np.zeros(len(points))
    v = np.zeros(len(points))

    z_safe = np.where(valid, p_cam[:, 2], 1.0)

    u[valid] = (focal_length * p_cam[valid, 0] / z_safe[valid]) + (w / 2)
    v[valid] = (focal_length * p_cam[valid, 1] / z_safe[valid]) + (h / 2)

    return u, v, valid


def render_silhouette(vertices_world, cam_pos, cam_look, cam_up, f_px, w, h):
    """vertices_world: (N*3, 3) triangle vertices already in world/LS space
    (i.e. the STL transformed by whatever pose is being evaluated)."""
    res = project_points_vectorized(vertices_world, cam_pos, cam_look, cam_up, f_px, w, h)

    img = np.zeros((h, w), dtype=np.uint8)
    if res is None:
        return img

    u, v, valid = res

    u_tri = u.reshape(-1, 3)
    v_tri = v.reshape(-1, 3)
    valid_tri = valid.reshape(-1, 3)

    tri_is_valid = np.all(valid_tri, axis=1)

    valid_u = u_tri[tri_is_valid]
    valid_v = v_tri[tri_is_valid]

    if len(valid_u) == 0:
        return img

    pts = np.stack((valid_u, valid_v), axis=-1).astype(np.int32)

    # Draw each triangle separately (not all at once) - a single fillPoly call
    # over all triangles uses the even-odd rule, which XORs out the front and
    # back surfaces of a closed 3D shape, leaving only a wireframe.
    for p in pts:
        cv2.fillPoly(img, [p], 255)

    return img


def get_camera_pose(cam_name, center, step00_cams):
    """Reproduces main.js's `views` array + look_at offset correction exactly:
    camera position is `center` shifted by the real working distance along
    one axis; look_at is `center` shifted by step00's calibrated
    look_at_offset_x_mm/y_mm (camera aiming correction), mapped per-camera
    the same way main.js does it."""
    cx, cy, cz = center
    dist = CAMERA_DISTANCES_MM[cam_name]

    if cam_name == "back":
        pos = np.array([cx + dist, cy, cz])
    elif cam_name == "left":
        pos = np.array([cx, cy + dist, cz])
    elif cam_name == "top":
        pos = np.array([cx, cy, cz + dist])
    else:
        raise ValueError(cam_name)

    look_at = np.array([cx, cy, cz])
    ru_name = NAME_MAP_RU[cam_name]
    if step00_cams and ru_name in step00_cams:
        dx = step00_cams[ru_name]["look_at_offset_x_mm"]
        dy = step00_cams[ru_name]["look_at_offset_y_mm"]
        if cam_name == "back":
            look_at[1] -= dx
            look_at[2] += dy
        elif cam_name == "left":
            look_at[0] += dx
            look_at[2] += dy
        elif cam_name == "top":
            look_at[0] -= dx
            look_at[1] -= dy

    up = np.array(CAMERA_UP[cam_name], dtype=float)
    return pos, look_at, up
