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
    
    # Load step 2 (for world transform, to know where the camera is looking)
    step02_file = os.path.join(results_dir, 'step02_result.json')
    tx, ty, tz, rx, ry, rz = 0, 0, 0, 0, 0, 0
    if os.path.exists(step02_file):
        with open(step02_file, 'r') as f:
            step02 = json.load(f)
            tx, ty, tz = step02.get('tx', 0), step02.get('ty', 0), step02.get('tz', 0)
            rx, ry, rz = step02.get('rx', 0), step02.get('ry', 0), step02.get('rz', 0)
            
    t_align = np.array([tx, ty, tz])
    
    # Load step 5
    step5_file = os.path.join(results_dir, 'step05_result.json')
    if not os.path.exists(step5_file):
        print(f"Error: {step5_file} not found. Run Step 5 first.")
        sys.exit(1)
        
    with open(step5_file, 'r') as f:
        step5_data = json.load(f)
        
    cameras = {
        "back": { "position_mm": [0, 2500, 0], "up_vector": [0, 0, 1], "w": 512, "h": 512, "focal": 1024.0 },
        "left": { "position_mm": [1650, 0, 0], "up_vector": [0, 0, 1], "w": 512, "h": 512, "focal": 1024.0 },
        "top": { "position_mm": [0, 0, 2000], "up_vector": [-1, 0, 0], "w": 512, "h": 512, "focal": 1024.0 }
    }
    
    results = {
        "cameras": {},
        "calibration_file": "camera_calibration.json"
    }
    
    calibration_data = {}
    
    for cam, info in step5_data.items():
        if cam in cameras:
            cam_def = cameras[cam]
            
            # Theoretical WORLD positions
            pos = np.array(cam_def['position_mm'], dtype=float)
            look = t_align # The camera looks at the helmet
            up = np.array(cam_def['up_vector'], dtype=float)
            focal = cam_def['focal']
            
            # Measured shifts
            scale = info.get('scale', 1.0)
            rot = info.get('rotation', 0.0)
            du = info.get('shift_x', 0.0)
            dv = info.get('shift_y', 0.0)
            
            # Calculate local displacements
            Z = look - pos
            Z_dist = np.linalg.norm(Z)
            
            if Z_dist > 1e-6:
                Z_cam = Z / Z_dist
                
                X_cam = np.cross(Z_cam, up)
                if np.linalg.norm(X_cam) > 1e-6:
                    X_cam = X_cam / np.linalg.norm(X_cam)
                else:
                    X_cam = np.array([1.0, 0.0, 0.0])
                
                Y_cam = np.cross(Z_cam, X_cam)
                
                dp_lateral = (du * Z_dist / focal) * X_cam + (dv * Z_dist / focal) * Y_cam
                dp_z = Z_dist * (scale - 1) * Z_cam
                
                # Calibrated WORLD positions
                pos = pos - dp_lateral - dp_z
                look = look - dp_lateral
                
                rot_rad = np.radians(-rot)
                R = Rotation.from_rotvec(rot_rad * Z_cam).as_matrix()
                up = R @ up
        
        dist = np.linalg.norm(pos - look)
        
        results["cameras"][cam] = {
            "pos": pos.tolist(),
            "look_at": look.tolist(),
            "up_vector": up.tolist(),
            "distance": float(dist)
        }
        
        calibration_data[cam] = results["cameras"][cam]
        
    result_file = os.path.join(results_dir, 'step06_result.json')
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=4)
        
    global_calib_file = os.path.join(base_dir, 'results', 'camera_calibration.json')
    with open(global_calib_file, 'w') as f:
        json.dump(calibration_data, f, indent=4)
        
    print(f"Saved step 6 results to {result_file}")
    print(f"Saved global camera calibration to {global_calib_file}")

if __name__ == '__main__':
    main()
