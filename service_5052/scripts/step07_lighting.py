import os
import sys
import json
import argparse
import cv2
import numpy as np

def analyze_lights(img, mask):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Only consider helmet area
    gray = cv2.bitwise_and(gray, gray, mask=mask)
    
    # Find bright spots (specular highlights)
    # We use a high threshold to find the brightest spots
    _, thresh = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY)
    
    # Find contours of bright spots
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    lights = []
    for c in contours:
        area = cv2.contourArea(c)
        if area > 10:  # ignore tiny noise
            M = cv2.moments(c)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                
                # Heuristic: convert 2D image coordinate to a relative 3D direction
                # For simplicity, we just assume the light comes from the general direction of the camera
                # and is slightly offset based on where the highlight is in the 2D image.
                # Here we just pass the 2D coordinates and area, and the JS will map it to a 3D vector.
                lights.append({
                    "cx": cX,
                    "cy": cY,
                    "area": float(area),
                    "intensity": min(1.0, area / 1000.0) # normalize brightness
                })
    return lights

def get_3d_direction(cam_name, lx, ly, img_w, img_h):
    # Convert 2D pixel to normalized device coordinates [-1, 1]
    nx = (lx / img_w) * 2 - 1
    ny = -(ly / img_h) * 2 + 1 # invert Y
    
    # Base camera vectors (approximate)
    cam_dirs = {
        "back": np.array([0, 1, 0]),
        "left": np.array([1, 0, 0]),
        "top": np.array([0, 0, 1])
    }
    
    # Heuristic: we perturb the camera direction slightly based on the highlight position
    base_dir = cam_dirs[cam_name]
    
    if cam_name == "back":
        v = base_dir + np.array([nx, 0, ny])
    elif cam_name == "left":
        v = base_dir + np.array([0, nx, ny])
    else: # top
        v = base_dir + np.array([nx, ny, 0])
        
    v = v / np.linalg.norm(v)
    return v.tolist()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    args = parser.parse_args()
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    results_dir = os.path.join(base_dir, 'results', args.session)
    os.makedirs(results_dir, exist_ok=True)
    
    input_dir = os.path.join(base_dir, 'input', 'photos_etalon')
    
    cameras = ["back", "left", "top"]
    
    results = {"lights": {}}
    
    for cam in cameras:
        img_path = os.path.join(input_dir, f"{cam}.png")
        mask_path = os.path.join(results_dir, f"rgba_{cam}.png") # step 4 output
        
        if not os.path.exists(img_path) or not os.path.exists(mask_path):
            print(f"Skipping {cam}, missing images.")
            continue
            
        img = cv2.imread(img_path)
        
        # We need the original mask, or we can just read the alpha channel of rgba
        rgba = cv2.imread(mask_path, cv2.IMREAD_UNCHANGED)
        mask = rgba[:, :, 3]
        
        # resize img to match mask if needed
        if img.shape[:2] != mask.shape[:2]:
            img = cv2.resize(img, (mask.shape[1], mask.shape[0]), interpolation=cv2.INTER_AREA)
            
        lights_2d = analyze_lights(img, mask)
        
        lights_3d = []
        for l in lights_2d:
            d3_dir = get_3d_direction(cam, l["cx"], l["cy"], img.shape[1], img.shape[0])
            lights_3d.append({
                "dir": d3_dir,
                "intensity": l["intensity"],
                "distance": 2000.0 # approximate light distance
            })
            
        results["lights"][cam] = lights_3d
        
    result_file = os.path.join(results_dir, 'step05_result.json')
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=4)
        
    print(f"Saved step 5 results to {result_file}")

if __name__ == '__main__':
    main()
