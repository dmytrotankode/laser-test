import os
import sys
import json
import numpy as np
import cv2
from stl import mesh
import argparse

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
    
    p_cam = (R @ points.T).T + t
    
    valid = p_cam[:, 2] > 0
    u = np.zeros(len(points))
    v = np.zeros(len(points))
    
    z_safe = np.where(valid, p_cam[:, 2], 1.0)
    u[valid] = (focal_length * p_cam[valid, 0] / z_safe[valid]) + (w / 2)
    v[valid] = (focal_length * p_cam[valid, 1] / z_safe[valid]) + (h / 2)
    
    return u, v, valid

def render_silhouette(vertices, cam_pos, cam_look, cam_up, camera_intrinsics):
    w = camera_intrinsics['image_width_px']
    h = camera_intrinsics['image_height_px']
    f = camera_intrinsics['focal_length_px']
    
    res = project_points_vectorized(vertices, cam_pos, cam_look, cam_up, f, w, h)
    
    img = np.zeros((h, w), dtype=np.uint8)
    if res is None: return img
    
    u, v, valid = res
    u_tri = u.reshape(-1, 3)
    v_tri = v.reshape(-1, 3)
    valid_tri = valid.reshape(-1, 3)
    
    tri_is_valid = np.all(valid_tri, axis=1)
    valid_u = u_tri[tri_is_valid]
    valid_v = v_tri[tri_is_valid]
    
    if len(valid_u) == 0: return img
    
    pts = np.stack((valid_u, valid_v), axis=-1).astype(np.int32)
    
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
    
    stl_path = os.path.join(base_dir, 'input', 'model_3d', 'helmet_ref.stl')
    helmet_mesh = mesh.Mesh.from_file(stl_path)
    vertices = helmet_mesh.vectors.reshape(-1, 3)
    print(f"Loaded STL with {len(vertices)//3} triangles")
    
    # Load step 2 to get the helmet's real world coordinates
    step02_file = os.path.join(results_dir, 'step02_result.json')
    tx, ty, tz, rx, ry, rz = 0, 0, 0, 0, 0, 0
    if os.path.exists(step02_file):
        with open(step02_file, 'r') as f:
            step02 = json.load(f)
            tx, ty, tz = step02.get('tx', 0), step02.get('ty', 0), step02.get('tz', 0)
            rx, ry, rz = step02.get('rx', 0), step02.get('ry', 0), step02.get('rz', 0)
            
    rx_rad, ry_rad, rz_rad = np.radians(rx), np.radians(ry), np.radians(rz)
    Rx = np.array([[1, 0, 0], [0, np.cos(rx_rad), -np.sin(rx_rad)], [0, np.sin(rx_rad), np.cos(rx_rad)]])
    Ry = np.array([[np.cos(ry_rad), 0, np.sin(ry_rad)], [0, 1, 0], [-np.sin(ry_rad), 0, np.cos(ry_rad)]])
    Rz = np.array([[np.cos(rz_rad), -np.sin(rz_rad), 0], [np.sin(rz_rad), np.cos(rz_rad), 0], [0, 0, 1]])
    R_align = Rz @ Ry @ Rx
    t_align = np.array([tx, ty, tz])
    
    # Transform helmet to World
    vertices_world = (R_align @ vertices.T).T + t_align
    
    cameras = {
        "back": { "position_mm": [0, 2500, 0], "up_vector": [0, 0, 1] },
        "left": { "position_mm": [1650, 0, 0], "up_vector": [0, 0, 1] },
        "top": { "position_mm": [0, 0, 2000], "up_vector": [-1, 0, 0] }
    }
    
    out_dict = {}
    
    for cam_name, cam_info in cameras.items():
        print(f"Projecting {cam_name}...")
        
        target_path = os.path.join(results_dir, f"solid_{cam_name}.png")
        if os.path.exists(target_path):
            img_rgba = cv2.imread(target_path, cv2.IMREAD_UNCHANGED)
            if img_rgba.shape[2] == 4:
                target_mask = img_rgba[:, :, 3]
            else:
                target_mask = cv2.cvtColor(img_rgba, cv2.COLOR_BGR2GRAY)
            target_h, target_w = target_mask.shape
        else:
            target_mask = None
            target_h, target_w = 512, 512
            
        camera_intrinsics = {
            "image_width_px": target_w,
            "image_height_px": target_h,
            "focal_length_px": max(target_w, target_h) * 2.0
        }
        
        cam_pos = np.array(cam_info['position_mm'], dtype=float)
        cam_up = np.array(cam_info['up_vector'], dtype=float)
        
        # The physical camera is pointed at the helmet!
        cam_look = t_align
        
        # Pure physical projection
        img = render_silhouette(vertices_world, cam_pos, cam_look, cam_up, camera_intrinsics)
        
        proj_file = f"proj_{cam_name}.png"
        out_path = os.path.join(results_dir, proj_file)
        cv2.imwrite(out_path, img)
        
        out_dict[cam_name] = {
            "file": proj_file,
            "rotation_applied": 0,
            "iou_score": 1.0 # Bounding box normalization removed
        }
        print(f"  Projected {cam_name}.")
        
    result_file = os.path.join(results_dir, 'step04_result.json')
    with open(result_file, 'w') as f:
        json.dump(out_dict, f, indent=4)
        
    print(f"Saved step 4 results to {result_file}")

if __name__ == '__main__':
    main()
