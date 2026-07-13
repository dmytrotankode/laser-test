import os
import sys
import json
import numpy as np
import cv2
from stl import mesh
import argparse


def get_transform_matrix(tx, ty, tz, rx_deg, ry_deg, rz_deg, scale=1.0):
    from scipy.spatial.transform import Rotation
    R = Rotation.from_euler('xyz', [rx_deg, ry_deg, rz_deg], degrees=True).as_matrix()
    T = np.eye(4)
    T[:3, :3] = R * scale
    T[0, 3] = tx
    T[1, 3] = ty
    T[2, 3] = tz
    return T

def get_transform_matrix(tx, ty, tz, rx_deg, ry_deg, rz_deg, scale=1.0):
    from scipy.spatial.transform import Rotation
    R = Rotation.from_euler('xyz', [rx_deg, ry_deg, rz_deg], degrees=True).as_matrix()
    T = np.eye(4)
    T[:3, :3] = R * scale
    T[0, 3] = tx
    T[1, 3] = ty
    T[2, 3] = tz
    return T

def project_points_vectorized(points, cam_pos, cam_look, cam_up, focal_length, w, h):
    Z = cam_look - cam_pos
    norm_Z = np.linalg.norm(Z)
    if norm_Z < 1e-6: return None
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
    
    # points: (N, 3)
    p_cam = (R @ points.T).T + t # (N, 3)
    
    # Keep only points in front of camera
    valid = p_cam[:, 2] > 0
    
    u = np.zeros(len(points))
    v = np.zeros(len(points))
    
    # Avoid division by zero
    z_safe = np.where(valid, p_cam[:, 2], 1.0)
    
    u[valid] = (focal_length * p_cam[valid, 0] / z_safe[valid]) + (w / 2)
    v[valid] = (focal_length * p_cam[valid, 1] / z_safe[valid]) + (h / 2)
    
    return u, v, valid

def render_silhouette(stl_mesh, T_model, cam_info, camera_intrinsics):
    w = camera_intrinsics['image_width_px']
    h = camera_intrinsics['image_height_px']
    f = camera_intrinsics['focal_length_px']
    
    vertices = stl_mesh.vectors.reshape(-1, 3) # (N*3, 3)
    ones = np.ones((vertices.shape[0], 1))
    vertices_4d = np.hstack([vertices, ones])
    transformed = (T_model @ vertices_4d.T).T[:, :3]
    
    tx, ty, tz = T_model[0, 3], T_model[1, 3], T_model[2, 3]
    
    cam_pos = np.array(cam_info['position_mm'], dtype=float) + np.array([tx, ty, tz])
    cam_look = np.array(cam_info['look_at'], dtype=float) + np.array([tx, ty, tz])
    cam_up = np.array(cam_info['up_vector'], dtype=float)
    
    res = project_points_vectorized(transformed, cam_pos, cam_look, cam_up, f, w, h)
    
    img = np.zeros((h, w), dtype=np.uint8)
    if res is None: return img
    
    u, v, valid = res
    
    # Reshape back to triangles (N, 3)
    u_tri = u.reshape(-1, 3)
    v_tri = v.reshape(-1, 3)
    valid_tri = valid.reshape(-1, 3)
    
    # A triangle is valid only if ALL 3 vertices are in front of camera
    tri_is_valid = np.all(valid_tri, axis=1)
    
    valid_u = u_tri[tri_is_valid]
    valid_v = v_tri[tri_is_valid]
    
    if len(valid_u) == 0: return img
    
    # Format for cv2.fillPoly: list of arrays of shape (3, 2)
    pts = np.stack((valid_u, valid_v), axis=-1).astype(np.int32)
    
    # We must draw each triangle sequentially! 
    # If we pass all triangles to a single cv2.fillPoly call, OpenCV uses the Even-Odd fill rule.
    # Because a 3D helmet has overlapping front and back surfaces, the Even-Odd rule XORs them out,
    # leaving only the edges visible (which looks like a wireframe X-Ray).
    for p in pts:
        cv2.fillPoly(img, [p], 255)
    
    return img

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    args = parser.parse_args()
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    results_dir = os.path.join(base_dir, 'results', args.session)
    os.makedirs(results_dir, exist_ok=True)
    
    # In 5052, we project the original helmet_ref.stl with the alignment matrix
    stl_path = os.path.join(base_dir, 'input', 'model_3d', 'helmet_ref.stl')
    helmet_mesh = mesh.Mesh.from_file(stl_path)
    print(f"Loaded STL with {len(helmet_mesh.vectors)} triangles")
    
    align_file = os.path.join(results_dir, 'step02_result.json')
    if not os.path.exists(align_file):
        print("Error: step02_result.json not found!")
        sys.exit(1)
        
    with open(align_file, 'r') as f:
        align_data = json.load(f)
        
    T_align = get_transform_matrix(
        align_data['tx'], align_data['ty'], align_data['tz'],
        align_data['rx'], align_data['ry'], align_data['rz'],
        align_data['scale']
    )
    
    # Original 5050 constants
    camera_intrinsics = {
        "image_width_px": 512,
        "image_height_px": 512,
        "focal_length_px": 1200.0
    }
    
    cameras = {
        "back": { "position_mm": [0, 2500, 0], "look_at": [0, 0, 0], "up_vector": [0, 0, 1] },
        "left": { "position_mm": [1650, 0, 0], "look_at": [0, 0, 0], "up_vector": [0, 0, 1] },
        "top": { "position_mm": [0, 0, 2000], "look_at": [0, 0, 0], "up_vector": [0, -1, 0] }
    }
    
    # We apply T_align to the model directly, not to cameras. 
    # Or apply it to cameras to simulate moving them relative to the rotated helmet.
    # We will apply T_align to the mesh in `render_silhouette`.
    # Wait, in render_silhouette, `T_model` is used to transform the mesh.
    # So we just pass T_align as T_model.
    T_model = T_align
    
    out_dict = {}
    
    for cam_name, cam_info in cameras.items():
        print(f"Projecting {cam_name}...")
        img = render_silhouette(helmet_mesh, T_model, cam_info, camera_intrinsics)
        
        # Save silhouette (proj_cam)
        proj_file = f"proj_{cam_name}.png"
        out_path = os.path.join(results_dir, proj_file)
        cv2.imwrite(out_path, img)
        
        out_dict[cam_name] = proj_file
        
    result_file = os.path.join(results_dir, 'step04_result.json')
    with open(result_file, 'w') as f:
        json.dump(out_dict, f, indent=4)
        
    print(f"Saved step 4 results to {result_file}")

if __name__ == '__main__':
    main()

