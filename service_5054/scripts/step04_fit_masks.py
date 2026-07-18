import os
import sys
import json
import numpy as np
import cv2
import argparse

def find_2d_transform(target_mask, proj_mask, cam_name):
    target_w = 512
    scale_factor = target_w / target_mask.shape[1]
    target_h = int(target_mask.shape[0] * scale_factor)
    
    img1 = cv2.resize(target_mask, (target_w, target_h), interpolation=cv2.INTER_NEAREST)
    img2 = cv2.resize(proj_mask, (target_w, target_h), interpolation=cv2.INTER_NEAREST)
    
    edges1_base = cv2.Canny(img1, 100, 200)
    edges2_base = cv2.Canny(img2, 100, 200)
    
    cutoff = None
    if cam_name in ['Сзади', 'Слева']:
        cutoff = int(target_h * 0.75)
    elif cam_name == 'Сверху':
        cutoff = int(target_h * 0.90)
        
    if cam_name == 'Сзади':
        passes = [
            {'scales': [0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15], 'rots': [-9, -4, 0, 4, 9]},
            {'scales': [0.96, 0.98, 1.0, 1.02, 1.04], 'rots': [-3, -1, 0, 1, 3], 'relative': True},
            {'scales': [0.99, 1.0, 1.01], 'rots': [-1, 0, 1], 'relative': True}
        ]
    elif cam_name == 'Слева':
        passes = [
            {'scales': [0.85, 0.95, 1.05, 1.15], 'rots': [-9, -4, 0, 4, 9]},
            {'scales': [0.96, 0.98, 1.0, 1.02, 1.04], 'rots': [-3, -1, 0, 1, 3], 'relative': True},
            {'scales': [0.99, 1.0, 1.01], 'rots': [-1, 0, 1], 'relative': True}
        ]
    elif cam_name == 'Сверху':
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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    args = parser.parse_args()
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    results_dir = os.path.join(base_dir, 'results', args.session)
    
    cameras = ["Сзади", "Слева", "Сверху"]
    results = {}
    
    for cam in cameras:
        cam_map = {"Сзади": "back", "Слева": "left", "Сверху": "top"}
        eng_cam = cam_map[cam]
        
        rgba_path = os.path.join(results_dir, f'rgba_{eng_cam}.png')
        model_mask_path = os.path.join(results_dir, f'model_mask_{cam}.png')
        
        if not os.path.exists(rgba_path) or not os.path.exists(model_mask_path):
            print(f"Error: Missing files for {cam}")
            continue
            
        rgba_img = cv2.imdecode(np.fromfile(rgba_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        if rgba_img is None:
            print(f"Error reading {rgba_path}")
            continue
            
        if rgba_img.shape[2] == 4:
            target_mask = rgba_img[:, :, 3]
        else:
            target_mask = cv2.cvtColor(rgba_img, cv2.COLOR_BGR2GRAY)
            _, target_mask = cv2.threshold(target_mask, 10, 255, cv2.THRESH_BINARY)
            
        model_img = cv2.imdecode(np.fromfile(model_mask_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        if model_img is None:
            print(f"Error reading {model_mask_path}")
            continue
            
        if model_img.shape[2] == 4:
            proj_mask = model_img[:, :, 3]
        else:
            proj_mask = cv2.cvtColor(model_img, cv2.COLOR_BGR2GRAY)
            _, proj_mask = cv2.threshold(proj_mask, 10, 255, cv2.THRESH_BINARY)
            
        h, w = target_mask.shape
        if proj_mask.shape[:2] != (h, w):
            proj_mask = cv2.resize(proj_mask, (w, h), interpolation=cv2.INTER_NEAREST)
            
        scale, rot, du, dv = find_2d_transform(target_mask, proj_mask, cam)
        
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
        cv2.putText(overlap, "GREEN: Match", (50, 260), cv2.FONT_HERSHEY_SIMPLEX, 2, c_both, 4)
        
        out_path = os.path.join(results_dir, f'overlap_{cam}.png')
        is_success, im_buf_arr = cv2.imencode(".png", overlap)
        if is_success:
            im_buf_arr.tofile(out_path)
        
        results[cam] = {
            "scale": float(scale),
            "rot": float(rot),
            "du": float(du),
            "dv": float(dv),
            "overlap_file": f"overlap_{cam}.png",
            "overlap_path": f"/files/{args.session}/overlap_{cam}.png"
        }
        
    with open(os.path.join(results_dir, 'step04_result.json'), 'w') as f:
        json.dump(results, f, indent=4)
        
if __name__ == '__main__':
    main()
