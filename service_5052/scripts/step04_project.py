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

def render_silhouette(stl_mesh, cam_pos, cam_look, cam_up, camera_intrinsics):
    w = camera_intrinsics['image_width_px']
    h = camera_intrinsics['image_height_px']
    f = camera_intrinsics['focal_length_px']
    
    vertices = stl_mesh.vectors.reshape(-1, 3)
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
    print(f"Loaded STL with {len(helmet_mesh.vectors)} triangles")
    
    cameras = {
        "back": { "position_mm": [0, 2500, 0], "look_at": [0, 0, 0], "up_vector": [0, 0, 1] },
        "left": { "position_mm": [1650, 0, 0], "look_at": [0, 0, 0], "up_vector": [0, 0, 1] },
        "top": { "position_mm": [0, 0, 2000], "look_at": [0, 0, 0], "up_vector": [0, -1, 0] }
    }
    
    out_dict = {}
    
    for cam_name, cam_info in cameras.items():
        print(f"Projecting {cam_name}...")
        
        target_path = os.path.join(results_dir, f"solid_{cam_name}.png")
        if os.path.exists(target_path):
            target_mask = cv2.imread(target_path, cv2.IMREAD_GRAYSCALE)
            target_h, target_w = target_mask.shape
        else:
            target_h, target_w = 512, 512
            
        camera_intrinsics = {
            "image_width_px": target_w,
            "image_height_px": target_h,
            "focal_length_px": max(target_w, target_h) * 2.0
        }
        
        cam_pos = np.array(cam_info['position_mm'], dtype=float)
        cam_look = np.array(cam_info['look_at'], dtype=float)
        cam_up = np.array(cam_info['up_vector'], dtype=float)
        
        # Render untransformed
        img = render_silhouette(helmet_mesh, cam_pos, cam_look, cam_up, camera_intrinsics)
        
        # Fit bounding box to target mask
        if os.path.exists(target_path):
            y_tgt, x_tgt = np.where(target_mask > 0)
            y_proj, x_proj = np.where(img > 0)
            
            if len(y_tgt) > 0 and len(y_proj) > 0:
                tgt_w = np.max(x_tgt) - np.min(x_tgt)
                tgt_h = np.max(y_tgt) - np.min(y_tgt)
                tgt_cx = float((np.max(x_tgt) + np.min(x_tgt)) / 2.0)
                tgt_cy = float((np.max(y_tgt) + np.min(y_tgt)) / 2.0)
                
                proj_w = np.max(x_proj) - np.min(x_proj)
                proj_h = np.max(y_proj) - np.min(y_proj)
                proj_cx = float((np.max(x_proj) + np.min(x_proj)) / 2.0)
                proj_cy = float((np.max(y_proj) + np.min(y_proj)) / 2.0)
                
                scale = float(min(tgt_w / max(1, proj_w), tgt_h / max(1, proj_h)) * 0.95)
                
                M = cv2.getRotationMatrix2D((proj_cx, proj_cy), 0, scale)
                M[0, 2] += (tgt_cx - proj_cx)
                M[1, 2] += (tgt_cy - proj_cy)
                
                img = cv2.warpAffine(img, M, (target_w, target_h), flags=cv2.INTER_NEAREST)
        
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
