import sys
import os
import cv2
import numpy as np
import json
import argparse

def main():
    parser = argparse.ArgumentParser(description='Step 7: Compare 3D Mask positions')
    parser.add_argument('--session', required=True)
    args = parser.parse_args()
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    results_dir = os.path.join(base_dir, 'results', args.session)
    
    cams = ["back", "left", "top"]
    results = {}
    
    for cam in cams:
        etalon_mask_path = os.path.join(results_dir, f'etalon_3d_mask_{cam}.png')
        current_mask_path = os.path.join(results_dir, f'current_3d_mask_{cam}.png')
        
        if not os.path.exists(etalon_mask_path) or not os.path.exists(current_mask_path):
            print(f"Skipping {cam}, missing files")
            continue
            
        etalon_mask = cv2.imread(etalon_mask_path, cv2.IMREAD_GRAYSCALE)
        current_mask = cv2.imread(current_mask_path, cv2.IMREAD_GRAYSCALE)
        
        if etalon_mask is None or current_mask is None:
            continue
            
        h, w = etalon_mask.shape
        
        # Create an RGB image for overlay of the two masks on black background
        # Etalon mask in Red, Current mask in Green
        # Intersection will be Yellow
        
        overlay = np.zeros((h, w, 3), dtype=np.uint8)
        
        # In BGR format: R is index 2, G is index 1
        overlay[:, :, 2] = etalon_mask  # Red for Etalon (Step 4)
        overlay[:, :, 1] = current_mask # Green for Current (Step 6)
        
        compare_file = f'compare_{cam}.png'
        compare_path = os.path.join(results_dir, compare_file)
        cv2.imwrite(compare_path, overlay)
        
        results[cam] = {
            "etalon_mask_path": f"/files/{args.session}/etalon_3d_mask_{cam}.png",
            "current_mask_path": f"/files/{args.session}/current_3d_mask_{cam}.png",
            "compare_file": compare_file,
            "compare_path": f"/files/{args.session}/{compare_file}"
        }
        
    # Now calculate delta_3d
    # Load step04 global_3d
    step04_file = os.path.join(results_dir, 'step04_result.json')
    step06_file = os.path.join(results_dir, 'step06_result.json')
    
    if os.path.exists(step04_file) and os.path.exists(step06_file):
        with open(step04_file, 'r') as f:
            s4 = json.load(f).get("global_3d", {})
        with open(step06_file, 'r') as f:
            s6 = json.load(f).get("global_3d", {})
            
        if s4 and s6:
            results["delta_3d"] = {
                "x_mm": s6.get("x_mm", 0) - s4.get("x_mm", 0),
                "y_mm": s6.get("y_mm", 0) - s4.get("y_mm", 0),
                "z_mm": s6.get("z_mm", 0) - s4.get("z_mm", 0),
                "roll_deg": s6.get("roll_deg", 0) - s4.get("roll_deg", 0),
                "pitch_deg": s6.get("pitch_deg", 0) - s4.get("pitch_deg", 0),
                "yaw_deg": s6.get("yaw_deg", 0) - s4.get("yaw_deg", 0)
            }
            
    with open(os.path.join(results_dir, 'step07_result.json'), 'w') as f:
        json.dump(results, f, indent=4)
        
if __name__ == '__main__':
    main()
