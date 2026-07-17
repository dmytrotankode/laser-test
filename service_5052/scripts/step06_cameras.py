import os
import sys
import json
import argparse
import numpy as np
from scipy.spatial.transform import Rotation

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    args = parser.parse_args()
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    results_dir = os.path.join(base_dir, 'results', args.session)
    os.makedirs(results_dir, exist_ok=True)
    
    # Load step 2 (for world transform)
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
    
    # Load step 5
    step5_file = os.path.join(results_dir, 'step05_result.json')
    step5_data = {}
    if os.path.exists(step5_file):
        with open(step5_file, 'r') as f:
            step5_data = json.load(f)
            
    # Default cameras
    cameras = {
        "back": { "pos": [0, 2500, 0], "look_at": [0, 0, 0], "up_vector": [0, 0, 1] },
        "left": { "pos": [1650, 0, 0], "look_at": [0, 0, 0], "up_vector": [0, 0, 1] },
        "top": { "pos": [0, 0, 2000], "look_at": [0, 0, 0], "up_vector": [-1, 0, 0] }
    }
    
    focal = 1024.0
    
    results = {"cameras": {}}
    for cam, info in cameras.items():
        pos = np.array(info["pos"], dtype=float)
        look = np.array(info["look_at"], dtype=float)
        up = np.array(info["up_vector"], dtype=float)
        
        if cam in step5_data:
            align = step5_data[cam]
            scale = float(align['scale'])
            rot = float(align['rotation'])
            du = float(align['shift_x'])
            dv = float(align['shift_y'])
            
            Z = look - pos
            Z_dist = np.linalg.norm(Z)
            if Z_dist > 1e-6:
                Z_cam = Z / Z_dist
                
                X_cam = np.cross(Z_cam, up)
                norm_X = np.linalg.norm(X_cam)
                if norm_X > 1e-6: X_cam = X_cam / norm_X
                else: X_cam = np.array([1.0, 0.0, 0.0])
                
                Y_cam = np.cross(Z_cam, X_cam)
                
                dp_lateral = (du * Z_dist / focal) * X_cam + (dv * Z_dist / focal) * Y_cam
                dp_z = Z_dist * (scale - 1) * Z_cam
                
                pos = pos - dp_lateral - dp_z
                look = look - dp_lateral
                
                rot_rad = np.radians(-rot)
                R = Rotation.from_rotvec(rot_rad * Z_cam).as_matrix()
                up = R @ up
                
        # Transform to world coordinates (robot cell)
        world_pos = R_align @ pos + t_align
        world_look = R_align @ look + t_align
        world_up = R_align @ up
        
        dist = np.linalg.norm(world_pos - world_look)
        results["cameras"][cam] = {
            "pos": world_pos.tolist(),
            "look_at": world_look.tolist(),
            "up_vector": world_up.tolist(),
            "distance": float(dist)
        }
        
    result_file = os.path.join(results_dir, 'step06_result.json')
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=4)
        
    print(f"Saved step 6 results to {result_file}")

if __name__ == '__main__':
    main()
