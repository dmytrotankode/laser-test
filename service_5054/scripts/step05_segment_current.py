# -*- coding: utf-8 -*-
import os
import sys
import json
import argparse
import cv2
import numpy as np
from rembg import remove

def remove_stand(mask, cam):
    if cam != "back":
        return mask
        
    h, w = mask.shape
    y_indices, x_indices = np.where(mask > 0)
    if len(y_indices) == 0:
        return mask
        
    bottom_y = np.max(y_indices)
    top_y = np.min(y_indices)
    
    # scan from bottom up
    for y in range(bottom_y, top_y, -1):
        row_x = np.where(mask[y, :] > 0)[0]
        if len(row_x) > 0:
            width = row_x[-1] - row_x[0]
            if width > w * 0.4:
                # Helmet found. Remove everything below this y (with a small buffer).
                cutoff_y = min(bottom_y, y + int(h * 0.015))
                mask[cutoff_y:, :] = 0
                break
                
    return mask

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    args = parser.parse_args()
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    results_dir = os.path.join(base_dir, 'results', args.session)
    os.makedirs(results_dir, exist_ok=True)
    
    input_dir = os.path.join(base_dir, 'input', 'photos_current')
    
    cameras = {
        "back": "back.png",
        "left": "left.png",
        "top": "top.png"
    }
    
    colors = {
        "back": (51, 51, 255),  # Red (BGR)
        "left": (51, 255, 51),  # Green
        "top": (255, 51, 51)    # Blue
    }
    
    results = {}
    
    for cam, filename in cameras.items():
        in_path = os.path.join(input_dir, filename)
        if not os.path.exists(in_path):
            print(f"Error: Missing {in_path}")
            sys.exit(1)
            
        print(f"Processing {filename}...")
        img = cv2.imread(in_path)
        orig_h, orig_w = img.shape[:2]

        # Run rembg on a downscaled copy for speed, but bring the mask back to
        # full resolution before doing anything else with it - must stay
        # consistent with step03_segment.py / model_mask_*.png (rendered at
        # full 4096x3000), otherwise step04/06's base_scale and px_to_mm
        # conversion end up comparing masks at mismatched resolutions.
        max_dim = 1024
        if max(orig_h, orig_w) > max_dim:
            scale = max_dim / max(orig_h, orig_w)
            new_w, new_h = int(orig_w * scale), int(orig_h * scale)
            img_small = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        else:
            img_small = img

        # remove background
        _, encoded_img = cv2.imencode('.png', img_small)
        output_data = remove(encoded_img.tobytes(), only_mask=True)
        nparr = np.frombuffer(output_data, np.uint8)
        mask = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

        if mask.shape[:2] != (orig_h, orig_w):
            mask = cv2.resize(mask, (orig_w, orig_h), interpolation=cv2.INTER_LINEAR)

        # Morphological open to remove noise
        _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

        # Remove stand for back camera
        mask = remove_stand(mask, cam)
        
        # Create RGBA (Cropped)
        rgba = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        rgba[:, :, 3] = mask
        rgba_file = f"current_rgba_{cam}.png"
        rgba_path = os.path.join(results_dir, rgba_file)
        cv2.imwrite(rgba_path, rgba)
        
        # Create Solid Mask
        h, w = mask.shape
        solid = np.zeros((h, w, 4), dtype=np.uint8)
        c_bgr = colors[cam]
        solid[mask > 0] = (c_bgr[0], c_bgr[1], c_bgr[2], 255)
        
        solid_file = f"current_solid_{cam}.png"
        solid_path = os.path.join(results_dir, solid_file)
        cv2.imwrite(solid_path, solid)
        
        results[cam] = {
            "source_path": f"/input/photos_current/{filename}",
            "rgba_file": rgba_file,
            "rgba_path": f"/files/{args.session}/{rgba_file}",
            "solid_file": solid_file,
            "solid_path": f"/files/{args.session}/{solid_file}"
        }
        
    out_json = os.path.join(results_dir, 'step05_result.json')
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
        
if __name__ == "__main__":
    main()
