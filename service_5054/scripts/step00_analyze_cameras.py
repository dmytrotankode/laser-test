import os
import sys
import json
import argparse
import cv2
import numpy as np
from rembg import remove

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    args = parser.parse_args()
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    results_dir = os.path.join(base_dir, 'results', args.session)
    os.makedirs(results_dir, exist_ok=True)
    
    input_dir = os.path.join(base_dir, 'input', 'photos_etalon')
    
    # 4096x3000
    img_w = 4096
    img_h = 3000
    center_x = img_w / 2.0
    center_y = img_h / 2.0
    
    # Cameras info
    cameras_info = {
        "Сзади": {"file": "back.png", "dist_mm": 2500, "phys_size_mm": 264, "measure": "width"},
        "Слева": {"file": "left.png", "dist_mm": 1650, "phys_size_mm": 286, "measure": "width"},  # Length is 286
        "Сверху": {"file": "top.png", "dist_mm": 2000, "phys_size_mm": 264, "measure": "width"}
    }
    
    camera_config = {}
    
    for cam_name, info in cameras_info.items():
        in_path = os.path.join(input_dir, info["file"])
        if not os.path.exists(in_path):
            print(f"Error: Missing {in_path}")
            sys.exit(1)
            
        img = cv2.imread(in_path)
        
        # Scale down for much faster rembg (approx 33s -> 3s)
        scale = 0.25
        small_img = cv2.resize(img, (0,0), fx=scale, fy=scale)
        output_data = remove(small_img)
        mask = output_data[:, :, 3].copy()
        
        y_indices, x_indices = np.where(mask > 0)
        
        if len(y_indices) == 0:
            print(f"Warning: No helmet found in {info['file']}!")
            continue
            
        min_x, max_x = np.min(x_indices), np.max(x_indices)
        min_y, max_y = np.min(y_indices), np.max(y_indices)
        
        if cam_name == "Сзади":
            # Remove stand
            bottom_y = max_y
            top_y = min_y
            small_w = int(img_w * scale)
            small_h = int(img_h * scale)
            for y in range(bottom_y, top_y, -1):
                row_x = np.where(mask[y, :] > 0)[0]
                if len(row_x) > 0:
                    width = row_x[-1] - row_x[0]
                    if width > small_w * 0.4:
                        cutoff_y = min(bottom_y, y + int(small_h * 0.015))
                        mask[cutoff_y:, :] = 0
                        break
            y_indices, x_indices = np.where(mask > 0)
            min_x, max_x = np.min(x_indices), np.max(x_indices)
            min_y, max_y = np.min(y_indices), np.max(y_indices)

        # Scale bbox back up to original resolution
        min_x = min_x / scale
        max_x = max_x / scale
        min_y = min_y / scale
        max_y = max_y / scale

        width_px = max_x - min_x
        height_px = max_y - min_y
        
        cx_px = (min_x + max_x) / 2.0
        cy_px = (min_y + max_y) / 2.0
        
        size_px = width_px if info["measure"] == "width" else height_px
        
        # Calculate focal length
        f_px = (size_px * info["dist_mm"]) / info["phys_size_mm"]
        
        # Calculate offset in mm
        dx_mm = ((cx_px - center_x) * info["dist_mm"]) / f_px
        dy_mm = ((cy_px - center_y) * info["dist_mm"]) / f_px
        
        camera_config[cam_name] = {
            "bbox_min_x": int(min_x),
            "bbox_max_x": int(max_x),
            "bbox_min_y": int(min_y),
            "bbox_max_y": int(max_y),
            "width_px": int(width_px),
            "height_px": int(height_px),
            "f_px": float(f_px),
            "look_at_offset_x_mm": float(dx_mm),
            "look_at_offset_y_mm": float(-dy_mm) # Three.js Y is up, but image Y is down
        }

    out_file = os.path.join(results_dir, 'step00_cameras.json')
    with open(out_file, 'w') as f:
        json.dump(camera_config, f, indent=4)
        
    print(json.dumps({"status": "success", "data": camera_config}))

if __name__ == "__main__":
    main()
