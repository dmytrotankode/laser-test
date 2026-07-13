import os
import sys
import json
import numpy as np
import cv2
import argparse
from scipy.spatial.transform import Rotation
from logger import PipelineLogger

def get_cam_axes(cam_pos, cam_look, cam_up):
    Z = cam_look - cam_pos
    norm_Z = np.linalg.norm(Z)
    if norm_Z < 1e-6:
        return None, None, None, 1.0
    Z = Z / norm_Z
    
    X = np.cross(Z, cam_up)
    norm_X = np.linalg.norm(X)
    if norm_X < 1e-6:
        X = np.array([1.0, 0.0, 0.0])
    else:
        X = X / norm_X
        
    Y = np.cross(Z, X)
    
    return X, Y, Z, norm_Z

def find_2d_transform(target_mask, proj_mask, cam_name):
    target_w = 512
    scale_factor = target_w / target_mask.shape[1]
    target_h = int(target_mask.shape[0] * scale_factor)
    
    img1 = cv2.resize(target_mask, (target_w, target_h), interpolation=cv2.INTER_NEAREST)
    img2 = cv2.resize(proj_mask, (target_w, target_h), interpolation=cv2.INTER_NEAREST)
    
    edges1_base = cv2.Canny(img1, 100, 200)
    edges2_base = cv2.Canny(img2, 100, 200)
    
    cutoff = None
    if cam_name in ['back', 'left']:
        cutoff = int(target_h * 0.75)
    elif cam_name == 'top':
        cutoff = int(target_h * 0.90)
        
    if cam_name == 'back':
        passes = [
            {'scales': [0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15], 'rots': [-9, -4, 0, 4, 9]},
            {'scales': [0.96, 0.98, 1.0, 1.02, 1.04], 'rots': [-3, -1, 0, 1, 3], 'relative': True},
            {'scales': [0.99, 1.0, 1.01], 'rots': [-1, 0, 1], 'relative': True}
        ]
    elif cam_name == 'left':
        passes = [
            {'scales': [0.85, 0.95, 1.05, 1.15], 'rots': [-9, -4, 0, 4, 9]},
            {'scales': [0.96, 0.98, 1.0, 1.02, 1.04], 'rots': [-3, -1, 0, 1, 3], 'relative': True},
            {'scales': [0.99, 1.0, 1.01], 'rots': [-1, 0, 1], 'relative': True}
        ]
    elif cam_name == 'top':
        passes = [
            {'scales': [1.0], 'rots': range(0, 360, 10)},
            {'scales': [0.85, 0.95, 1.05, 1.15], 'rots': [-10, -5, 0, 5, 10], 'relative': True},
            {'scales': [0.98, 1.0, 1.02], 'rots': [-2, 0, 2], 'relative': True}
        ]
    else:
        passes = [{'scales': [1.0], 'rots': [0]}]
        
    best_scale = 1.0
    best_rot = 0.0
    best_tx = 0.0
    best_ty = 0.0
    best_score = -1
    
    img2_f = np.float32(edges2_base)
    if cutoff:
        img2_f[cutoff:, :] = 0
        
    center = (target_w / 2, target_h / 2)
    
    for p in passes:
        is_rel = p.get('relative', False)
        pass_best_score = -1
        pass_best_s = best_scale
        pass_best_r = best_rot
        pass_best_tx = best_tx
        pass_best_ty = best_ty
        
        for s_val in p['scales']:
            s = (best_scale * s_val) if is_rel else s_val
            for r_val in p['rots']:
                r = (best_rot + r_val) if is_rel else r_val
                
                M = cv2.getRotationMatrix2D(center, r, s)
                warped_edges1 = cv2.warpAffine(edges1_base, M, (target_w, target_h), flags=cv2.INTER_NEAREST)
                
                if cutoff:
                    warped_edges1[cutoff:, :] = 0
                    
                img1_f = np.float32(warped_edges1)
                
                (shift_x, shift_y), response = cv2.phaseCorrelate(img2_f, img1_f)
                
                if response > pass_best_score:
                    pass_best_score = response
                    pass_best_s = s
                    pass_best_r = r
                    pass_best_tx = shift_x
                    pass_best_ty = shift_y
                    
        best_scale = pass_best_s
        best_rot = pass_best_r
        best_tx = pass_best_tx
        best_ty = pass_best_ty
        best_score = pass_best_score
        
    du = best_tx / scale_factor
    dv = best_ty / scale_factor
    
    return best_scale, best_rot, du, dv

def generate_overlap_images(target_masks, proj_masks, transforms, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    for cam_name in target_masks:
        target_mask = target_masks[cam_name]
        proj_mask = proj_masks[cam_name]
        
        h, w = target_mask.shape
        if proj_mask.shape[:2] != (h, w):
            proj_mask = cv2.resize(proj_mask, (w, h), interpolation=cv2.INTER_NEAREST)
            
        scale, rot, du, dv = transforms[cam_name]
        
        center = (w / 2, h / 2)
        M_rot_scale = cv2.getRotationMatrix2D(center, rot, scale)
        M_rot_scale[0, 2] += -du
        M_rot_scale[1, 2] += -dv
        
        target_aligned = cv2.warpAffine(target_mask, M_rot_scale, (w, h), flags=cv2.INTER_NEAREST)
            
        overlap = np.full((h, w, 3), 30, dtype=np.uint8)
        
        mask1 = target_aligned > 0
        mask2 = proj_mask > 0
        
        only_etalon = mask1 & ~mask2
        only_model = mask2 & ~mask1
        both = mask1 & mask2
        
        c_etalon = (255, 150, 0)
        c_model = (0, 100, 255)
        c_both = (100, 255, 100)
        
        overlap[only_etalon] = c_etalon
        overlap[only_model] = c_model
        overlap[both] = c_both
        
        cv2.putText(overlap, f"BLUE: Etalon (s={scale:.2f}, r={rot:.1f})", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, c_etalon, 4)
        cv2.putText(overlap, "ORANGE: 3D Model", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 2, c_model, 4)
        cv2.putText(overlap, "GREEN: Perfect Match", (50, 260), cv2.FONT_HERSHEY_SIMPLEX, 2, c_both, 4)
        
        out_path = os.path.join(out_dir, f"overlap_{cam_name}.png")
        cv2.imwrite(out_path, overlap)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', type=str, required=True)
    args = parser.parse_args()
    
    session_id = args.session
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    session_dir = os.path.join(base_dir, 'results', session_id)
    
    logger = PipelineLogger(args.session, base_dir, "STEP 07: ETALON FIT")
    
    config_path = os.path.join(base_dir, 'pipeline_config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
        
    align_file = os.path.join(session_dir, 'step02_alignment.json')
    if not os.path.exists(align_file):
        logger.log("Error: step02_alignment.json not found!")
        sys.exit(1)
        
    with open(align_file, 'r') as f:
        align_data = json.load(f)
        base_T = np.array(align_data['matrix_4x4'])
        
    masks_dir = os.path.join(session_dir, 'step_etalon_masks')
    proj_dir = os.path.join(session_dir, 'step_etalon_projected')
    
    target_masks = {}
    proj_masks = {}
    
    for cam_name in [k for k in config['cameras'] if not k.startswith('_')]:
        img_name = f"mask_{cam_name}.png"
        mask_path = os.path.join(masks_dir, img_name)
        if not os.path.exists(mask_path):
            logger.log(f"Error: Mask {mask_path} not found!")
            sys.exit(1)
        target_masks[cam_name] = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        
        proj_name = f"proj_{cam_name}.png"
        proj_path = os.path.join(proj_dir, proj_name)
        if not os.path.exists(proj_path):
            logger.log(f"Error: Projection {proj_path} not found! Run Step 4 first.")
            sys.exit(1)
        proj_masks[cam_name] = cv2.imread(proj_path, cv2.IMREAD_GRAYSCALE)
        
    focal_length = config['camera_intrinsics']['focal_length_px']
    tx, ty, tz = base_T[0, 3], base_T[1, 3], base_T[2, 3]
    
    global_dp = np.zeros(3)
    axis_counts = np.zeros(3)
    global_rotvec = np.zeros(3)
    
    logger.log("Executing Grid Search + Phase Correlation for each camera...")
    
    transforms = {}
    
    for cam_name in [k for k in config['cameras'] if not k.startswith('_')]:
        cam_info = config['cameras'][cam_name]
        cam_pos = np.array(cam_info['position_mm'], dtype=float) + np.array([tx, ty, tz])
        cam_look = np.array(cam_info['look_at'], dtype=float) + np.array([tx, ty, tz])
        cam_up = np.array(cam_info['up_vector'], dtype=float)
        
        X_cam, Y_cam, Z_cam, Z_dist = get_cam_axes(cam_pos, cam_look, cam_up)
        
        scale, rot, du, dv = find_2d_transform(target_masks[cam_name], proj_masks[cam_name], cam_name)
        transforms[cam_name] = (scale, rot, du, dv)
        logger.log(f"  {cam_name}: Scale={scale:.3f}, Rot={rot:.2f}deg, Shift u={du:.2f}px, v={dv:.2f}px")
        
        dp_world = (du * Z_dist / focal_length) * X_cam + (dv * Z_dist / focal_length) * Y_cam
        dp_world += Z_dist * (scale - 1) * Z_cam
        
        for i in range(3):
            weight = abs(X_cam[i]) + abs(Y_cam[i]) + abs(Z_cam[i])
            if weight > 0.1:
                global_dp[i] += dp_world[i]
                axis_counts[i] += 1
                
        rot_rad = np.radians(-rot)
        global_rotvec += rot_rad * (-Z_cam)
                
    for i in range(3):
        if axis_counts[i] > 0:
            global_dp[i] /= axis_counts[i]
            
    logger.log(f"Calculated optimal 3D shift: dx={global_dp[0]:.2f}, dy={global_dp[1]:.2f}, dz={global_dp[2]:.2f}")
    
    delta_R = Rotation.from_rotvec(global_rotvec).as_matrix()
    T_final = base_T.copy()
    T_final[:3, :3] = delta_R @ base_T[:3, :3]
    T_final[0:3, 3] += global_dp
    
    out_file = os.path.join(session_dir, 'step07_etalon_fit.json')
    res_data = {
        'base_matrix': base_T.tolist(),
        'delta_translation': global_dp.tolist(),
        'delta_rotvec': global_rotvec.tolist(),
        'final_matrix': T_final.tolist()
    }
    with open(out_file, 'w') as f:
        json.dump(res_data, f, indent=4)
        
    logger.log(f"Saved T_etalon to {out_file}")
    
    overlap_dir = os.path.join(session_dir, 'step07_etalon_overlap')
    generate_overlap_images(target_masks, proj_masks, transforms, overlap_dir)
    logger.log("Generated 2D overlap images successfully.")

if __name__ == '__main__':
    main()
