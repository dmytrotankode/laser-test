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
        
        # Scale down to avoid OOM
        orig_h, orig_w = img.shape[:2]
        max_dim = 1024
        if max(orig_h, orig_w) > max_dim:
            scale = max_dim / max(orig_h, orig_w)
            new_w, new_h = int(orig_w * scale), int(orig_h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
        # remove background
        _, encoded_img = cv2.imencode('.png', img)
        output_data = remove(encoded_img.tobytes(), only_mask=True)
        nparr = np.frombuffer(output_data, np.uint8)
        mask = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        
        # Morphological open to remove noise
        _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Create RGBA (Cropped)
        rgba = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        rgba[:, :, 3] = mask
        rgba_file = f"rgba_{cam}.png"
        rgba_path = os.path.join(results_dir, rgba_file)
        cv2.imwrite(rgba_path, rgba)
        
        # Create Solid Mask
        h, w = mask.shape
        solid = np.zeros((h, w, 4), dtype=np.uint8)
        c_bgr = colors[cam]
        solid[:, :, 0] = c_bgr[0]
        solid[:, :, 1] = c_bgr[1]
        solid[:, :, 2] = c_bgr[2]
        solid[:, :, 3] = mask
        solid_file = f"solid_{cam}.png"
        solid_path = os.path.join(results_dir, solid_file)
        cv2.imwrite(solid_path, solid)
        
        results[cam] = {
            "rgba_file": rgba_file,
            "rgba_path": rgba_path,
            "solid_file": solid_file,
            "solid_path": solid_path
        }
        
    result_file = os.path.join(results_dir, 'step04_result.json')
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=4)
        
    print(f"Saved step 4 results to {result_file}")

if __name__ == '__main__':
    main()
