import os
import sys
import json
import cv2
import numpy as np
from rembg import remove
import argparse
from logger import PipelineLogger

def remove_stand(mask, logger):
    height, width = mask.shape
    row_widths = np.count_nonzero(mask, axis=1)
    if len(row_widths) == 0 or np.max(row_widths) == 0:
        return mask
        
    max_w = np.max(row_widths)
    threshold = max_w * 0.3
    
    cut_y = height
    for y in range(height - 1, height // 2, -1):
        if row_widths[y] > threshold:
            cut_y = y
            break
            
    if cut_y < height - 50:
        logger.log(f"  Stand detected! Cutting image at Y={cut_y} (Max width: {max_w}, Threshold: {threshold:.1f})")
        mask[cut_y:, :] = 0
        
    return mask

def process_image(img_path, out_path, logger, cam_name):
    logger.log(f"Processing {img_path} (View: {cam_name})...")
    
    img = cv2.imread(img_path)
    if img is None:
        logger.log(f"[ERROR] Could not read {img_path}")
        return 0
        
    orig_h, orig_w = img.shape[:2]
    
    max_dim = 1024
    if max(orig_h, orig_w) > max_dim:
        scale = max_dim / max(orig_h, orig_w)
        new_w, new_h = int(orig_w * scale), int(orig_h * scale)
        img_resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        logger.log(f"  Resized from {orig_w}x{orig_h} to {new_w}x{new_h} to prevent OOM")
    else:
        img_resized = img
        
    _, encoded_img = cv2.imencode('.png', img_resized)
    input_data = encoded_img.tobytes()
    
    output_data = remove(input_data, only_mask=True)
    
    nparr = np.frombuffer(output_data, np.uint8)
    mask = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    
    if mask.shape[:2] != (orig_h, orig_w):
        mask = cv2.resize(mask, (orig_w, orig_h), interpolation=cv2.INTER_LINEAR)
    
    # Check for and remove the stand before final morphology, EXCEPT for top view!
    if cam_name != 'top':
        mask = remove_stand(mask, logger)
    else:
        logger.log("  Top view detected, skipping stand removal to avoid clipping.")
    
    _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    
    cv2.imwrite(out_path, mask)
    
    # Save RGBA colored mask for visualization (original image with transparent background)
    rgba = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    rgba[:, :, 3] = mask
    rgba_out_path = out_path.replace('mask_', 'rgba_')
    cv2.imwrite(rgba_out_path, rgba)
    
    # Save solid colored mask for 3D visualization and UI
    c_bgr = {'back': (51, 51, 255), 'left': (51, 255, 51), 'top': (255, 51, 51)}.get(cam_name, (255, 255, 255))
    solid = np.zeros((orig_h, orig_w, 4), dtype=np.uint8)
    solid[:, :, 0] = c_bgr[0]
    solid[:, :, 1] = c_bgr[1]
    solid[:, :, 2] = c_bgr[2]
    solid[:, :, 3] = mask
    solid_out_path = out_path.replace('mask_', 'solid_')
    cv2.imwrite(solid_out_path, solid)
    
    logger.log(f"Saved segmented mask, RGBA, and Solid to {out_path} & {rgba_out_path} & {solid_out_path}")
    
    non_zero = cv2.countNonZero(mask)
    return non_zero

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['etalon', 'current'], required=True)
    parser.add_argument('--session', required=True)
    args = parser.parse_args()
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    logger = PipelineLogger(args.session, base_dir, f"STEP 03/05: SEGMENTATION ({args.mode.upper()})")
    
    config_path = os.path.join(base_dir, 'pipeline_config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    input_key = f"photos_{args.mode}"
    input_dir = os.path.join(base_dir, config['paths'][input_key])
    out_dir = os.path.join(logger.results_dir, f"step_{args.mode}_masks")
    os.makedirs(out_dir, exist_ok=True)
    
    results = {}
    for cam_name, info in config['cameras'].items():
        if cam_name.startswith('_'): continue
        
        in_path = os.path.join(input_dir, info['file'])
        if not os.path.exists(in_path):
            logger.log(f"[FAIL] Missing {in_path}")
            sys.exit(1)
            
        out_file = f"mask_{cam_name}.png"
        out_path = os.path.join(out_dir, out_file)
        
        pixels = process_image(in_path, out_path, logger, cam_name)
        results[cam_name] = {
            'mask_path': out_path,
            'mask_pixels': int(pixels)
        }
        
    metrics_path = os.path.join(logger.results_dir, f'step_{args.mode}_segmentation.json')
    with open(metrics_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.log(f"Finished segmenting 3 images for {args.mode}")

if __name__ == '__main__':
    main()
