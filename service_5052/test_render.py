import os
import cv2
import numpy as np
from stl import mesh

def project_points_vectorized(points, cam_pos, cam_look, cam_up, focal_length, w, h):
    Z = cam_look - cam_pos
    norm_Z = np.linalg.norm(Z)
    if norm_Z < 1e-6: return None
    Z = Z / norm_Z
    
    X = np.cross(Z, cam_up)
    norm_X = np.linalg.norm(X)
    if norm_X < 1e-6: X = np.array([1.0, 0.0, 0.0])
    else: X = X / norm_X
        
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

def render_silhouette(stl_mesh, cam_pos, cam_look, cam_up, focal, w, h):
    vertices = stl_mesh.vectors.reshape(-1, 3)
    res = project_points_vectorized(vertices, cam_pos, cam_look, cam_up, focal, w, h)
    img = np.zeros((h, w), dtype=np.uint8)
    if res is None: return img
    u, v, valid = res
    u_tri, v_tri, valid_tri = u.reshape(-1, 3), v.reshape(-1, 3), valid.reshape(-1, 3)
    tri_is_valid = np.all(valid_tri, axis=1)
    valid_u, valid_v = u_tri[tri_is_valid], v_tri[tri_is_valid]
    if len(valid_u) == 0: return img
    pts = np.stack((valid_u, valid_v), axis=-1).astype(np.int32)
    for p in pts: cv2.fillPoly(img, [p], 255)
    return img

helmet = mesh.Mesh.from_file('input/model_3d/helmet_ref.stl')
cams = {
    "back": { "pos": np.array([0, 2500, 0]), "look": np.array([0,0,0]), "up": np.array([0,0,1]) },
    "left": { "pos": np.array([1650, 0, 0]), "look": np.array([0,0,0]), "up": np.array([0,0,1]) },
    "top": { "pos": np.array([0, 0, 2000]), "look": np.array([0,0,0]), "up": np.array([0,-1,0]) }
}

for name, cam in cams.items():
    img = render_silhouette(helmet, cam['pos'], cam['look'], cam['up'], 1200, 512, 512)
    cv2.imwrite(f'test_{name}.png', img)
    print(f"{name}: mask area = {np.sum(img>0)}")
