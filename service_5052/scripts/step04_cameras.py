import os
import sys
import json
import argparse
import numpy as np

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    args = parser.parse_args()
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    results_dir = os.path.join(base_dir, 'results', args.session)
    os.makedirs(results_dir, exist_ok=True)
    
    # Cameras from service_5050
    # Center of helmet is approximately (0, 0, 85)
    center = np.array([0, 0, 85])
    
    cameras = {
        "back": {"pos": [0, 2500, 0]},
        "left": {"pos": [1650, 0, 0]},
        "top": {"pos": [0, 0, 2000]}
    }
    
    results = {"cameras": {}}
    for cam, info in cameras.items():
        pos = np.array(info["pos"])
        dist = np.linalg.norm(pos - center)
        results["cameras"][cam] = {
            "pos": pos.tolist(),
            "distance": float(dist)
        }
        
    result_file = os.path.join(results_dir, 'step04_result.json')
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=4)
        
    print(f"Saved step 3 results to {result_file}")

if __name__ == '__main__':
    main()
