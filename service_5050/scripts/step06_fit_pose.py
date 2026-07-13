import os
import sys
import json
import numpy as np
import cv2
from scipy.optimize import minimize
from step04_project import render_silhouette, get_transform_matrix
from stl import mesh
import argparse
from logger import PipelineLogger

def compute_chamfer_distance(img1, img2):
    if np.sum(img1) == 0 or np.sum(img2) == 0:
        return 999999.0
    
    edges1 = cv2.Canny(img1, 100, 200)
    edges2 = cv2.Canny(img2, 100, 200)
    
    if np.sum(edges1) == 0 or np.sum(edges2) == 0:
        return 999999.0
        
    dist1 = cv2.distanceTransform(~edges1, cv2.DIST_L2, 5)
    dist2 = cv2.distanceTransform(~edges2, cv2.DIST_L2, 5)
    
    d1 = np.mean(dist1[edges2 > 0])
    d2 = np.mean(dist2[edges1 > 0])
    return d1 + d2

def cost_function(delta_params, base_T, stl_mesh, config, target_masks):
    dx, dy, dz, drx, dry, drz = delta_params
    
    delta_T = get_transform_matrix(dx, dy, dz, drx, dry, drz, 1.0)
    T_new = delta_T @ base_T
    
    total_cost = 0.0
    
    for cam_name, target_mask in target_masks.items():
        cam_info = config['cameras'][cam_name]
        rendered = render_silhouette(stl_mesh, T_new, cam_info, config['camera_intrinsics'])
        cost = compute_chamfer_distance(target_mask, rendered)
        total_cost += cost
        
    return total_cost

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    args = parser.parse_args()
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    logger = PipelineLogger(args.session, base_dir, "STEP 06: FIT POSE")
    
    config_path = os.path.join(base_dir, 'pipeline_config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    align_path = os.path.join(logger.results_dir, 'step02_alignment.json')
    with open(align_path, 'r') as f:
        align_data = json.load(f)
    base_T = np.array(align_data['matrix_4x4'])
    
    stl_path = os.path.join(base_dir, config['paths']['model_stl'])
    helmet_mesh = mesh.Mesh.from_file(stl_path)
    
    mask_dir = os.path.join(logger.results_dir, 'step_current_masks')
    target_masks = {}
    for cam_name in config['cameras'].keys():
        if cam_name.startswith('_'): continue
        mask_path = os.path.join(mask_dir, f"mask_{cam_name}.png")
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        target_masks[cam_name] = mask
        
    initial_guess = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    
    logger.log("Optimizing pose delta (this might take a few minutes)...")
    res = minimize(
        cost_function,
        initial_guess,
        args=(base_T, helmet_mesh, config, target_masks),
        method='Powell',
        options={'maxiter': 100, 'disp': False}
    )
    
    dx, dy, dz, drx, dry, drz = res.x
    delta_T = get_transform_matrix(dx, dy, dz, drx, dry, drz, 1.0)
    T_final = delta_T @ base_T
    
    logger.log("Pose Fitting Results:")
    logger.log(f"  Delta translation (mm): dx={dx:.2f}, dy={dy:.2f}, dz={dz:.2f}")
    logger.log(f"  Delta rotation (deg):   drx={drx:.2f}, dry={dry:.2f}, drz={drz:.2f}")
    logger.log(f"  Final Cost:             {res.fun:.4f}")
    
    out_dict = {
        'delta_tx': float(dx),
        'delta_ty': float(dy),
        'delta_tz': float(dz),
        'delta_rx': float(drx),
        'delta_ry': float(dry),
        'delta_rz': float(drz),
        'matrix_4x4': T_final.tolist(),
        'base_matrix_4x4': base_T.tolist(),
        'cost': float(res.fun)
    }
    
    out_path = os.path.join(logger.results_dir, 'step06_pose_delta.json')
    with open(out_path, 'w') as f:
        json.dump(out_dict, f, indent=2)
        
    logger.log("Saved pose delta.")

if __name__ == '__main__':
    main()
