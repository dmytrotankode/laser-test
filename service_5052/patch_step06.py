import json
import numpy as np
from scipy.spatial.transform import Rotation

def apply_camera_patch():
    # Read step 5
    with open('results/run_20260717_211332/step05_result.json', 'r') as f:
        step5 = json.load(f)
        
    cameras = {
        "back": { "pos": [0, 2500, 0], "look_at": [0, 0, 0], "up_vector": [0, 0, 1] },
        "left": { "pos": [1650, 0, 0], "look_at": [0, 0, 0], "up_vector": [0, 0, 1] },
        "top": { "pos": [0, 0, 2000], "look_at": [0, 0, 0], "up_vector": [-1, 0, 0] }
    }
    focal = 1024.0
    
    for cam, info in cameras.items():
        if cam not in step5: continue
        align = step5[cam]
        scale = align['scale']
        rot = align['rotation']
        du = align['shift_x']
        dv = align['shift_y']
        
        pos = np.array(info['pos'])
        look = np.array(info['look_at'])
        up = np.array(info['up_vector'], dtype=float)
        
        Z = look - pos
        Z_dist = np.linalg.norm(Z)
        Z_cam = Z / Z_dist
        
        X_cam = np.cross(Z_cam, up)
        X_cam = X_cam / np.linalg.norm(X_cam)
        Y_cam = np.cross(Z_cam, X_cam)
        
        dp = (du * Z_dist / focal) * X_cam + (dv * Z_dist / focal) * Y_cam + Z_dist * (scale - 1) * Z_cam
        
        new_pos = pos - dp
        new_look = look - dp
        
        rot_rad = np.radians(-rot)
        R = Rotation.from_rotvec(rot_rad * Z_cam).as_matrix()
        new_up = R @ up
        
        print(f"{cam}:")
        print(f"  old pos: {pos}, new pos: {new_pos}")
        print(f"  old look: {look}, new look: {new_look}")
        print(f"  old up: {up}, new up: {new_up}")

apply_camera_patch()
