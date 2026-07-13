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
    
    img1 = cv2.resize(target_mask, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
    img2 = cv2.resize(proj_mask, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
    
    # img1 and img2 are grayscale textures. We don't use Canny.
    edges1_base = img1.astype(np.float32)
    edges2_base = img2.astype(np.float32)
    
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
    
    img1 = cv2.resize(target_mask, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
    img2 = cv2.resize(proj_mask, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
    
    # img1 and img2 are grayscale textures. We don't use Canny.
    edges1_base = img1.astype(np.float32)
    edges2_base = img2.astype(np.float32)
    
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


def generate_overlap_images(target_masks, proj_masks, transforms, out_dir, current_masks_dir, proj_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    for cam_name in target_masks:
        # Load the original RGB images for blending
        target_color = cv2.imread(os.path.join(current_masks_dir, f"rgba_{cam_name}.png"), cv2.IMREAD_UNCHANGED)
        proj_color = cv2.imread(os.path.join(proj_dir, f"rgba_{cam_name}.png"), cv2.IMREAD_UNCHANGED)
        
        target_rgb = target_color[:, :, :3]
        proj_rgb = proj_color[:, :, :3]
        target_alpha = target_color[:, :, 3] > 128
        proj_alpha = proj_color[:, :, 3] > 128
        
        h, w = target_rgb.shape[:2]
        if proj_rgb.shape[:2] != (h, w):
            proj_rgb = cv2.resize(proj_rgb, (w, h), interpolation=cv2.INTER_LINEAR)
            proj_alpha = cv2.resize(proj_color[:, :, 3], (w, h), interpolation=cv2.INTER_NEAREST) > 128
            
        # Convert to grayscale and apply tints
        target_gray = cv2.cvtColor(target_rgb, cv2.COLOR_BGR2GRAY)
        proj_gray = cv2.cvtColor(proj_rgb, cv2.COLOR_BGR2GRAY)
        
        # Green tint for Current (target): B=0, G=gray, R=0
        target_tinted = np.zeros_like(target_rgb)
        target_tinted[:, :, 1] = target_gray
        
        # Yellow tint for Etalon (proj): B=0, G=gray, R=gray
        proj_tinted = np.zeros_like(proj_rgb)
        proj_tinted[:, :, 1] = proj_gray
        proj_tinted[:, :, 2] = proj_gray

        overlap = np.full((h, w, 3), 30, dtype=np.uint8)
        
        # Where both are visible, blend them 50/50
        both = target_alpha & proj_alpha
        only_target = target_alpha & ~proj_alpha
        only_proj = proj_alpha & ~target_alpha
        
        overlap[only_target] = target_tinted[only_target]
        overlap[only_proj] = proj_tinted[only_proj]
        overlap[both] = cv2.addWeighted(target_tinted[both], 0.5, proj_tinted[both], 0.5, 0)
        
        cv2.putText(overlap, f"BLENDED TEXTURES", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 4)
        cv2.putText(overlap, "Current Photo & Etalon Photo", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 2, (200, 200, 200), 4)
        
        out_path = os.path.join(out_dir, f"overlap_{cam_name}.png")
        cv2.imwrite(out_path, overlap)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', type=str, required=True)
    args = parser.parse_args()
    
    session_id = args.session
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    session_dir = os.path.join(base_dir, 'results', session_id)
    
    logger = PipelineLogger(session_id, base_dir, "STEP 09B: 2D CURRENT POSE FIT (TEXTURE)")
    
    config_path = os.path.join(base_dir, 'pipeline_config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
        
    etalon_file = os.path.join(session_dir, 'step07_etalon_fit.json')
    if not os.path.exists(etalon_file):
        logger.log("Error: step07_etalon_fit.json not found!")
        sys.exit(1)
        
    with open(etalon_file, 'r') as f:
        etalon_data = json.load(f)
        T_etalon = np.array(etalon_data['final_matrix'])
        
    current_masks_dir = os.path.join(session_dir, 'step_current_masks')
    proj_dir = os.path.join(session_dir, 'step_etalon_masks') # Compare against Etalon Masks
    
    target_masks = {}
    proj_masks = {}
    
    for cam_name in [k for k in config['cameras'] if not k.startswith('_')]:
        img_name = f"rgba_{cam_name}.png"
        mask_path = os.path.join(current_masks_dir, img_name)
        if not os.path.exists(mask_path):
            logger.log(f"Error: Mask {mask_path} not found!")
            sys.exit(1)
        # Load RGBA, convert to grayscale, mask out background
        rgba1 = cv2.imread(mask_path, cv2.IMREAD_UNCHANGED)
        gray1 = cv2.cvtColor(rgba1, cv2.COLOR_BGRA2GRAY)
        gray1[rgba1[:,:,3] < 128] = 0
        target_masks[cam_name] = gray1
        
        proj_name = f"rgba_{cam_name}.png"
        proj_path = os.path.join(proj_dir, proj_name)
        if not os.path.exists(proj_path):
            logger.log(f"Error: Etalon mask {proj_path} not found!")
            sys.exit(1)
        rgba2 = cv2.imread(proj_path, cv2.IMREAD_UNCHANGED)
        gray2 = cv2.cvtColor(rgba2, cv2.COLOR_BGRA2GRAY)
        gray2[rgba2[:,:,3] < 128] = 0
        proj_masks[cam_name] = gray2
        
    focal_length = config['camera_intrinsics']['focal_length_px']
    tx, ty, tz = T_etalon[0, 3], T_etalon[1, 3], T_etalon[2, 3]
    
    global_dp = np.zeros(3)
    axis_counts = np.zeros(3)
    global_rotvec = np.zeros(3)
    transforms = {}
    
    logger.log("Executing Grid Search + Phase Correlation for current photos relative to etalon projections...")
    
    for cam_name in [k for k in config['cameras'] if not k.startswith('_')]:
        cam_info = config['cameras'][cam_name]
        cam_pos = np.array(cam_info['position_mm'], dtype=float) + np.array([tx, ty, tz])
        cam_look = np.array(cam_info['look_at'], dtype=float) + np.array([tx, ty, tz])
        cam_up = np.array(cam_info['up_vector'], dtype=float)
        
        X_cam, Y_cam, Z_cam, Z_dist = get_cam_axes(cam_pos, cam_look, cam_up)
        
        scale, rot, du, dv = find_2d_transform(target_masks[cam_name], proj_masks[cam_name], cam_name)
        transforms[cam_name] = (scale, rot, du, dv)
        
        # Calculate dynamic mm/px ratio using Step 6 projections
        step06_mask_path = os.path.join(session_dir, 'step_etalon_projected', f"proj_{cam_name}.png")
        if os.path.exists(step06_mask_path):
            step06_mask = cv2.imread(step06_mask_path, cv2.IMREAD_GRAYSCALE)
            y06, x06 = np.where(step06_mask > 0)
            y_ph, x_ph = np.where(proj_masks[cam_name] > 0)
            if len(x06) > 0 and len(x_ph) > 0:
                w06 = np.max(x06) - np.min(x06)
                h06 = np.max(y06) - np.min(y06)
                w_ph = np.max(x_ph) - np.min(x_ph)
                h_ph = np.max(y_ph) - np.min(y_ph)
                
                # Average width and height ratio
                ratio_w = w06 / w_ph if w_ph > 0 else 1.0
                ratio_h = h06 / h_ph if h_ph > 0 else 1.0
                ratio = (ratio_w + ratio_h) / 2.0
            else:
                ratio = 1.0
        else:
            ratio = 1.0
            
        mm_per_px = (Z_dist / focal_length) * ratio
        logger.log(f"  {cam_name}: Scale={scale:.3f}, Rot={rot:.2f}deg, Shift u={du:.2f}px, v={dv:.2f}px (Ratio: {ratio:.3f}, mm/px: {mm_per_px:.3f})")
        
        # Use only direct translation (u, v) to estimate world shift.
        # Ignore noisy scale-derived depth changes. Orthogonal cameras ensure all 3 axes are covered by u, v!
        dp_trans = (du * mm_per_px) * X_cam + (dv * mm_per_px) * Y_cam
        
        for i in range(3):
            # Only accumulate if this camera has direct translation observation of this axis
            weight = abs(X_cam[i]) + abs(Y_cam[i])
            if weight > 0.1:
                global_dp[i] += dp_trans[i]
                axis_counts[i] += 1
                
        rot_rad = np.radians(-rot)
        global_rotvec += rot_rad * (-Z_cam)
                
    for i in range(3):
        if axis_counts[i] > 0:
            global_dp[i] /= axis_counts[i]
            
    logger.log(f"Calculated optimal 3D shift: dx={global_dp[0]:.2f}, dy={global_dp[1]:.2f}, dz={global_dp[2]:.2f}")
    logger.log(f"Calculated optimal 3D rotvec: {global_rotvec}")
    
    from scipy.spatial.transform import Rotation
    rot_obj = Rotation.from_rotvec(global_rotvec)
    euler_angles = rot_obj.as_euler('xyz', degrees=True)
    rx, ry, rz = euler_angles
    
    res_path = os.path.join(session_dir, 'step09b_current_pose_fit.json')
    res_data = {
        'delta_translation': global_dp.tolist(),
        'delta_rotvec': global_rotvec.tolist(),
        'metrics': {
            'shift_horizontal_mm': round(float(global_dp[0]), 2),
            'shift_vertical_mm': round(float(global_dp[2]), 2),
            'shift_depth_mm': round(float(global_dp[1]), 2),
            'tilt_pitch_deg': round(float(rx), 2),
            'tilt_roll_deg': round(float(ry), 2),
            'tilt_yaw_deg': round(float(rz), 2)
        }
    }
    with open(res_path, 'w') as f:
        json.dump(res_data, f, indent=4)
        
    logger.log(f"Saved delta translation and rotation to {res_path}")


    out_dir = os.path.join(session_dir, 'step09b_current_overlap')
    generate_overlap_images(target_masks, proj_masks, transforms, out_dir, current_masks_dir, proj_dir)
    logger.log("Generated 2D overlap images successfully.")

if __name__ == '__main__':
    main()
