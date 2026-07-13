import os
import sys
import json
import numpy as np
import cv2
from stl import mesh
import argparse
from logger import PipelineLogger

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
    logger = PipelineLogger(args.session, base_dir, "STEP 04: PROJECT 3D ETALON")
    
    config_path = os.path.join(base_dir, 'pipeline_config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    session_dir = os.path.join(base_dir, 'results', args.session)
    stl_path = os.path.join(session_dir, 'helmet_aligned.stl')
    helmet_mesh = mesh.Mesh.from_file(stl_path)
    logger.log(f"Loaded STL with {len(helmet_mesh.vectors)} triangles")
    
    # Load translation from step02
    align_file = os.path.join(session_dir, 'step02_alignment.json')
    if not os.path.exists(align_file):
        logger.log("Error: step02_alignment.json not found!")
        sys.exit(1)
        
    with open(align_file, 'r') as f:
        align_data = json.load(f)
        T_align = np.array(align_data['matrix_4x4'])
        tx, ty, tz = T_align[0, 3], T_align[1, 3], T_align[2, 3]
    
    # Render at origin (Identity matrix) since helmet is already aligned physically
    T_model = np.eye(4)
    
    out_dir = os.path.join(logger.results_dir, 'step_etalon_projected')
    os.makedirs(out_dir, exist_ok=True)
    
    cameras_data = {}
    
    for cam_name, cam_info in config['cameras'].items():
        if cam_name.startswith('_'): continue
        
        # Apply full T_align (rotation + translation) to keep cameras relative to the helmet
        cam_pos_4d = np.array([cam_info['position_mm'][0], cam_info['position_mm'][1], cam_info['position_mm'][2], 1.0])
        cam_look_4d = np.array([cam_info['look_at'][0], cam_info['look_at'][1], cam_info['look_at'][2], 1.0])
        cam_up_3d = np.array(cam_info['up_vector'], dtype=float)
        
        cam_pos_transformed = (T_align @ cam_pos_4d)[:3]
        cam_look_transformed = (T_align @ cam_look_4d)[:3]
        cam_up_transformed = T_align[:3, :3] @ cam_up_3d # direction vector only rotates
        
        # Update cam_info so render_silhouette uses the shifted positions
        cam_info['position_mm'] = cam_pos_transformed.tolist()
        cam_info['look_at'] = cam_look_transformed.tolist()
        cam_info['up_vector'] = cam_up_transformed.tolist()
        
        logger.log(f"Projecting {cam_name} (Pos: {cam_info['position_mm']})")
        
        img = render_silhouette(helmet_mesh, T_model, cam_info, config['camera_intrinsics'])
        
        out_path = os.path.join(out_dir, f"proj_{cam_name}.png")
        cv2.imwrite(out_path, img)
        
        # Save RGBA colored mask for visualization
        c_bgr = {'back': (51, 51, 255), 'left': (51, 255, 51), 'top': (255, 51, 51)}.get(cam_name, (255, 255, 255))
        rgba = np.zeros((img.shape[0], img.shape[1], 4), dtype=np.uint8)
        rgba[:, :, 0] = c_bgr[0] # Blue
        rgba[:, :, 1] = c_bgr[1] # Green
        rgba[:, :, 2] = c_bgr[2] # Red
        rgba[:, :, 3] = img # Alpha
        rgba_out_path = os.path.join(out_dir, f"rgba_{cam_name}.png")
        cv2.imwrite(rgba_out_path, rgba)
        
        logger.log(f"Saved projection to {out_path} & {rgba_out_path}")
        
        cameras_data[cam_name] = {
            'position': cam_pos_transformed.tolist(),
            'look_at': cam_look_transformed.tolist(),
            'up': cam_up_transformed.tolist()
        }
        
    out_dict = {'status': 'success', 'rendered_cameras': list(config['cameras'].keys())}
    out_json = os.path.join(logger.results_dir, 'step05_etalon_projection.json')
    with open(out_json, 'w') as f:
        json.dump(out_dict, f, indent=2)
        
    cam_json = os.path.join(logger.results_dir, 'step05_cameras.json')
    with open(cam_json, 'w') as f:
        json.dump(cameras_data, f, indent=2)
        
    logger.log(f"Saved camera positions to {cam_json}")

if __name__ == '__main__':
    main()
