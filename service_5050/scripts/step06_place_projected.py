import os
import sys
import json
import numpy as np
import argparse
from logger import PipelineLogger

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    args = parser.parse_args()
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    logger = PipelineLogger(args.session, base_dir, "STEP 06: VISUALIZE PROJECTED MASKS")
    
    config_path = os.path.join(base_dir, 'pipeline_config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    session_dir = os.path.join(base_dir, 'results', args.session)
    cam_json = os.path.join(session_dir, 'step05_cameras.json')
    
    if not os.path.exists(cam_json):
        logger.log("Error: step05_cameras.json not found!")
        sys.exit(1)
        
    with open(cam_json, 'r') as f:
        cameras_data = json.load(f)
        
    w = config['camera_intrinsics']['image_width_px']
    h = config['camera_intrinsics']['image_height_px']
    focal_length = config['camera_intrinsics']['focal_length_px']
    
    placements = {}
    
    for cam_name, cam_info in cameras_data.items():
        C = np.array(cam_info['position'])
        L = np.array(cam_info['look_at'])
        
        Z = L - C
        dist_to_lookat = np.linalg.norm(Z)
        if dist_to_lookat < 1e-6:
            continue
        Z_norm = Z / dist_to_lookat
        
                # Find widest part of the helmet from this camera's perspective
        stl_path = os.path.join(session_dir, 'helmet_aligned.stl')
        from stl import mesh
        helmet_mesh = mesh.Mesh.from_file(stl_path)
        vertices = helmet_mesh.vectors.reshape(-1, 3)
        
        rel_pos = vertices - C
        depths = rel_pos @ Z_norm
        
        z_min, z_max = np.min(depths), np.max(depths)
        bins = np.linspace(z_min, z_max, 50)
        
        # We need X and Y axes of the camera
        cam_up = np.array(cam_info['up'])
        X_cam = np.cross(Z_norm, cam_up)
        X_cam = X_cam / np.linalg.norm(X_cam)
        
        max_width = 0
        best_z = dist_to_lookat
        for i in range(len(bins)-1):
            m = (depths >= bins[i]) & (depths < bins[i+1])
            if np.sum(m) > 10:
                pts = rel_pos[m]
                x_proj = pts @ X_cam
                width = np.max(x_proj) - np.min(x_proj)
                if width > max_width:
                    max_width = width
                    best_z = (bins[i] + bins[i+1]) / 2
                    
        D = best_z
        P = C + D * Z_norm
        
        # Calculate physical width and height of the plane so it matches the image projection
        W_3d = w * D / focal_length
        H_3d = h * D / focal_length
        
        placements[cam_name] = {
            'position': P.tolist(),
            'look_at': C.tolist(), # Plane looks AT the camera!
            'width': W_3d,
            'height': H_3d
        }
        logger.log(f"Calculated plane for {cam_name}: Pos={P.tolist()}, W={W_3d:.1f}, H={H_3d:.1f}")
        
    out_json = os.path.join(session_dir, 'step06_projected_placements.json')
    with open(out_json, 'w') as f:
        json.dump(placements, f, indent=2)
        
    logger.log(f"Saved 3D placements to {out_json}")
    
    # We also output a dummy result for app.py
    out_dict = {'status': 'success'}
    with open(os.path.join(session_dir, 'step06_status.json'), 'w') as f:
        json.dump(out_dict, f, indent=2)

if __name__ == '__main__':
    main()
