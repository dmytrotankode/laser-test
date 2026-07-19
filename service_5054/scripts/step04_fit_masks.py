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
    coords1 = cv2.findNonZero(edges1_base)
    if coords1 is not None:
        _, y1, _, h1 = cv2.boundingRect(coords1)
        if cam_name in ['Сзади', 'Слева']:
            cutoff = int(y1 + h1 * 0.75)
        elif cam_name == 'Сверху':
            cutoff = int(y1 + h1 * 0.90)
        
    if cam_name == 'Сзади':
        passes = [
            {'scales': [0.75, 0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3, 1.35], 'rots': [-9, -6, -3, 0, 3, 6, 9]},
            {'scales': [0.96, 0.98, 1.0, 1.02, 1.04], 'rots': [-2, -1, 0, 1, 2], 'relative': True},
            {'scales': [0.99, 1.0, 1.01], 'rots': [-0.5, 0, 0.5], 'relative': True}
        ]
    elif cam_name == 'Слева':
        passes = [
            {'scales': [0.75, 0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3, 1.35], 'rots': [-9, -6, -3, 0, 3, 6, 9]},
            {'scales': [0.96, 0.98, 1.0, 1.02, 1.04], 'rots': [-2, -1, 0, 1, 2], 'relative': True},
            {'scales': [0.99, 1.0, 1.01], 'rots': [-0.5, 0, 0.5], 'relative': True}
        ]
    elif cam_name == 'Сверху':
        passes = [
            {'scales': [0.85, 0.9, 0.95, 1.0, 1.05, 1.15], 'rots': range(0, 360, 5)},
            {'scales': [0.96, 0.98, 1.0, 1.02, 1.04], 'rots': [-5, 0, 5], 'relative': True},
            {'scales': [0.98, 1.0, 1.02], 'rots': [-2, 0, 2], 'relative': True}
        ]
    else:
        passes = [{'scales': [1.0], 'rots': [0]}]
        
    best_scale = 1.0
    best_rot = 0.0
    best_tx = 0.0
    best_ty = 0.0
    best_score = -1
    
    img1_f = np.float32(edges1_base)
    if cutoff:
        img1_f[cutoff:, :] = 0
        
    img1_uint8 = img1_f.astype(np.uint8)
    kernel = np.ones((7, 7), np.uint8)
    img1_dilated = cv2.dilate(img1_uint8, kernel, iterations=1)
        
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
                warped_edges2 = cv2.warpAffine(edges2_base, M, (target_w, target_h), flags=cv2.INTER_NEAREST)
                
                if cutoff:
                    warped_edges2[cutoff:, :] = 0
                    
                img2_f = np.float32(warped_edges2)
                
                if cam_name in ['Сзади', 'Слева']:
                    coords1_f = cv2.findNonZero(img1_uint8)
                    coords2_f = cv2.findNonZero(warped_edges2.astype(np.uint8))
                    
                    if coords1_f is not None and coords2_f is not None:
                        _, y1_f, _, _ = cv2.boundingRect(coords1_f)
                        _, y2_f, _, _ = cv2.boundingRect(coords2_f)
                        base_dy = y1_f - y2_f
                        
                        pts = np.argwhere(img2_f > 0)
                        num_pts = len(pts)
                        
                        best_score_shift = -1
                        best_dx = 0
                        best_dy = base_dy
                        
                        if num_pts > 0:
                            for dy in range(base_dy - 20, base_dy + 21, 2):
                                for dx in range(-40, 41, 2):
                                    ty = pts[:, 0] + dy
                                    tx = pts[:, 1] + dx
                                    
                                    mask = (ty >= 0) & (ty < target_h) & (tx >= 0) & (tx < target_w)
                                    ty = ty[mask]
                                    tx = tx[mask]
                                    
                                    overlap = np.sum(img1_dilated[ty, tx] > 0)
                                    score = overlap / float(num_pts)
                                    
                                    if score > best_score_shift:
                                        best_score_shift = score
                                        best_dx = dx
                                        best_dy = dy
                                        
                        shift_x = best_dx
                        shift_y = best_dy
                        overlap_score = best_score_shift
                    else:
                        shift_x = 0
                        shift_y = 0
                        overlap_score = 0
                else:
                    (shift_x, shift_y), response = cv2.phaseCorrelate(img1_f, img2_f)
                    overlap_score = response
                
                if overlap_score > pass_best_score:
                    pass_best_score = overlap_score
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
        ph, pw = proj_mask.shape[:2]
        
        # 1) Compute bounding boxes to find base_scale and base_translation
        coords_t = cv2.findNonZero(target_mask)
        coords_p = cv2.findNonZero(proj_mask)
        
        M_base = np.zeros((2, 3), dtype=np.float64)
        M_base[0, 0] = 1.0
        M_base[1, 1] = 1.0
        
        if coords_t is not None and coords_p is not None:
            xt, yt, wt, ht = cv2.boundingRect(coords_t)
            xp, yp, wp, hp = cv2.boundingRect(coords_p)
            
            # Use min to find the true scale without interference from noisy extra parts (like stand/neck)
            base_scale = min(wt / float(wp) if wp > 0 else 1.0, ht / float(hp) if hp > 0 else 1.0)
            
            # For Center alignment, we align TOP-CENTER instead of center-center!
            # Since the bottom of the photo mask is noisy, aligning the top edges perfectly is a much better starting point!
            top_t_y = yt
            top_p_y = yp
            
            center_t_x = xt + wt / 2.0
            center_p_x = xp + wp / 2.0
            
            M_base[0, 0] = base_scale
            M_base[1, 1] = base_scale
            M_base[0, 2] = center_t_x - center_p_x * base_scale
            M_base[1, 2] = top_t_y - top_p_y * base_scale
            
        proj_pre_aligned = cv2.warpAffine(proj_mask, M_base, (w, h), flags=cv2.INTER_NEAREST)
        
        # 2) Find fine transform mapping proj_pre_aligned to target_mask
        fine_scale, rot, fine_du, fine_dv = find_2d_transform(target_mask, proj_pre_aligned, cam)
        
        # 3) Construct M_fine
        center = (w / 2.0, h / 2.0)
        M_fine_2x3 = cv2.getRotationMatrix2D(center, rot, fine_scale)
        M_fine_2x3[0, 2] += fine_du
        M_fine_2x3[1, 2] += fine_dv
        
        # 4) Combine M_total = M_fine * M_base
        M_base_3x3 = np.eye(3)
        M_base_3x3[0:2, :] = M_base
        
        M_fine_3x3 = np.eye(3)
        M_fine_3x3[0:2, :] = M_fine_2x3
        
        M_total_3x3 = np.dot(M_fine_3x3, M_base_3x3)
        M_total = M_total_3x3[0:2, :]
        
        # Extract total scale and rot for metrics
        total_scale = np.sqrt(M_total[0,0]**2 + M_total[1,0]**2)
        total_rot = np.degrees(np.arctan2(M_total[1,0], M_total[0,0]))
        total_du = M_total[0, 2]
        total_dv = M_total[1, 2]
        
        proj_aligned = cv2.warpAffine(proj_mask, M_total, (w, h), flags=cv2.INTER_NEAREST)
        
        overlap = np.full((h, w, 3), 30, dtype=np.uint8)
        
        mask1 = target_mask > 0
        mask2 = proj_aligned > 0
        
        only_etalon = mask1 & ~mask2
        only_model = mask2 & ~mask1
        both = mask1 & mask2
        
        c_etalon = (255, 150, 0)
        c_model = (0, 100, 255)
        c_both = (100, 255, 100)
        
        overlap[only_etalon] = c_etalon
        overlap[only_model] = c_model
        overlap[both] = c_both
        
        cv2.putText(overlap, f"BLUE: Etalon (s={total_scale:.2f}, r={total_rot:.1f})", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, c_etalon, 2)
        cv2.putText(overlap, "ORANGE: 3D Model", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, c_model, 2)
        cv2.putText(overlap, "GREEN: Match", (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, c_both, 2)
        
        out_path = os.path.join(results_dir, f'overlap_{cam}.png')
        is_success, im_buf_arr = cv2.imencode(".png", overlap)
        if is_success:
            im_buf_arr.tofile(out_path)
        
        results[cam] = {
            "scale": float(total_scale),
            "rot": float(total_rot),
            "du": float(total_du),
            "dv": float(total_dv),
            "overlap_file": f'overlap_{cam}.png',
            "overlap_path": f'/files/{args.session}/overlap_{cam}.png'
        }
        
    with open(os.path.join(results_dir, 'step04_result.json'), 'w') as f:
        json.dump(results, f, indent=4)
        
if __name__ == '__main__':
    main()
