import cv2
import numpy as np
import os
import glob

# Find the latest session
results_dir = r"C:\__TARAS_\__DISTI__\helmet_pipeline\results"
sessions = [d for d in os.listdir(results_dir) if d.startswith("run_")]
latest_session = sorted(sessions)[-1]

mask_path = os.path.join(results_dir, latest_session, "step_etalon_masks", "mask_back.png")
print(f"Analyzing {mask_path}")

mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
if mask is None:
    print("Mask not found.")
    exit(1)

def remove_stand(mask):
    height, width = mask.shape
    row_widths = np.count_nonzero(mask, axis=1)
    max_w = np.max(row_widths)
    
    # We look from bottom up to find where the helmet starts
    # The stand is typically narrow (e.g. ~200px) compared to helmet (~2000px)
    # Threshold for "helmet body" vs "stand": 30% of max width
    threshold = max_w * 0.3
    
    cut_y = height
    for y in range(height - 1, height // 2, -1):
        if row_widths[y] > threshold:
            cut_y = y
            break
            
    # If we found a significant drop at the bottom, we cut it
    if cut_y < height - 50: # Only cut if it's a real stand, not just the bottom edge of the image
        print(f"Stand detected! Cutting image at Y={cut_y} (Max width: {max_w}, Threshold: {threshold:.1f})")
        mask[cut_y:, :] = 0
    else:
        print("No stand detected.")
        
    return mask

mask = remove_stand(mask)
