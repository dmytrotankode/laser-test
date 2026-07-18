import cv2
import numpy as np
from stl import mesh

def project_points_vectorized(points, cam_pos, cam_look, cam_up, focal_length, w, h):
    Z = cam_look - cam_pos
    norm_Z = np.linalg.norm(Z)
    Z = Z / norm_Z
    X = np.cross(Z, cam_up)
    X = X / np.linalg.norm(X)
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
    u, v, valid = project_points_vectorized(vertices, cam_pos, cam_look, cam_up, focal, w, h)
    img = np.zeros((h, w), dtype=np.uint8)
    u_tri, v_tri, valid_tri = u.reshape(-1, 3), v.reshape(-1, 3), valid.reshape(-1, 3)
    tri_is_valid = np.all(valid_tri, axis=1)
    pts = np.stack((u_tri[tri_is_valid], v_tri[tri_is_valid]), axis=-1).astype(np.int32)
    for p in pts: cv2.fillPoly(img, [p], 255)
    return img

helmet = mesh.Mesh.from_file('input/model_3d/helmet_ref.stl')

# Test up=[1,0,0]
img1 = render_silhouette(helmet, np.array([0,0,2000]), np.array([0,0,0]), np.array([1,0,0]), 1024, 512, 512)
y, x = np.where(img1 > 0)
print(f"up=[1,0,0]: center of mass X = {np.mean(x):.1f} (if < 256, it's left heavy)")

# Test up=[-1,0,0]
img2 = render_silhouette(helmet, np.array([0,0,2000]), np.array([0,0,0]), np.array([-1,0,0]), 1024, 512, 512)
y, x = np.where(img2 > 0)
print(f"up=[-1,0,0]: center of mass X = {np.mean(x):.1f} (if < 256, it's left heavy)")

# Front of the helmet is generally larger/more bulky than the back? No, the back of the helmet is usually bulkier, front has the brim.
# Let's just output the min X and max X to see the shape.
print(f"up=[1,0,0] X bounds: {np.min(x)} to {np.max(x)}")
print(f"up=[-1,0,0] X bounds: {np.min(x)} to {np.max(x)}")
