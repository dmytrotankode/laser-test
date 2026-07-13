import os
import sys
import json
import numpy as np
import re
import argparse
from logger import PipelineLogger

def get_rotation_matrix(rx, ry, rz):
    rx, ry, rz = np.radians(rx), np.radians(ry), np.radians(rz)
    Rx = np.array([[1, 0, 0], [0, np.cos(rx), -np.sin(rx)], [0, np.sin(rx), np.cos(rx)]])
    Ry = np.array([[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]])
    Rz = np.array([[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx

def get_transform_matrix(tx, ty, tz, rx, ry, rz):
    T = np.eye(4)
    T[:3, :3] = get_rotation_matrix(rx, ry, rz)
    T[0, 3] = tx
    T[1, 3] = ty
    T[2, 3] = tz
    return T

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    args = parser.parse_args()
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    logger = PipelineLogger(args.session, base_dir, "STEP 07/08: GENERATE LS FILE")
    
    config_path = os.path.join(base_dir, 'pipeline_config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    delta_path = os.path.join(logger.results_dir, 'step06_pose_delta.json')
    with open(delta_path, 'r') as f:
        delta_data = json.load(f)
        
    dx = delta_data['delta_tx']
    dy = delta_data['delta_ty']
    dz = delta_data['delta_tz']
    drx = delta_data['delta_rx']
    dry = delta_data['delta_ry']
    drz = delta_data['delta_rz']
    
    delta_T = get_transform_matrix(dx, dy, dz, drx, dry, drz)
    
    ls_in_path = os.path.join(base_dir, config['paths']['ls_file'])
    with open(ls_in_path, 'r') as f:
        lines = f.readlines()
        
    point_pattern = re.compile(
        r'(P\[\d+\]\{\s*GP1:\s*UF\s*:\s*\d+,\s*UT\s*:\s*\d+.*?X\s*=\s*)([-\d.]+)(.*?Y\s*=\s*)([-\d.]+)(.*?Z\s*=\s*)([-\d.]+)(.*?W\s*=\s*)([-\d.]+)(.*?P\s*=\s*)([-\d.]+)(.*?R\s*=\s*)([-\d.]+)(.*)',
        re.IGNORECASE
    )
    
    out_lines = []
    points_modified = 0
    
    for line in lines:
        match = point_pattern.search(line)
        if match:
            prefix, x, m1, y, m2, z, m3, w, m4, p, m5, r, suffix = match.groups()
            
            x, y, z = float(x), float(y), float(z)
            pt_4d = np.array([x, y, z, 1.0])
            pt_new = delta_T @ pt_4d
            
            x_new, y_new, z_new = pt_new[:3]
            w_new, p_new, r_new = float(w)+drx, float(p)+dry, float(r)+drz
            
            new_line = f"{prefix}{x_new:.3f}{m1}{y_new:.3f}{m2}{z_new:.3f}{m3}{w_new:.3f}{m4}{p_new:.3f}{m5}{r_new:.3f}{suffix}\n"
            out_lines.append(new_line)
            points_modified += 1
        else:
            out_lines.append(line)
            
    out_ls_path = os.path.join(logger.results_dir, 'TORXL_corrected.ls')
    with open(out_ls_path, 'w') as f:
        f.writelines(out_lines)
        
    logger.log(f"Generated new LS file with {points_modified} corrected points.")
    logger.log(f"Saved to: {out_ls_path}")

if __name__ == '__main__':
    main()
