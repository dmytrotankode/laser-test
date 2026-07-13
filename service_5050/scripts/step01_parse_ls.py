import os
import sys
import json
import re
import argparse
from logger import PipelineLogger

def parse_ls_file(filepath, logger):
    logger.log(f"Parsing LS file: {filepath}")
    points = []
    
    with open(filepath, 'r') as f:
        content = f.read()
        
    point_pattern = re.compile(
        r'P\[(\d+)\]\{\s*GP1:\s*UF\s*:\s*(\d+),\s*UT\s*:\s*(\d+).*?X\s*=\s*([-\d.]+).*?Y\s*=\s*([-\d.]+).*?Z\s*=\s*([-\d.]+).*?W\s*=\s*([-\d.]+).*?P\s*=\s*([-\d.]+).*?R\s*=\s*([-\d.]+)',
        re.DOTALL | re.IGNORECASE
    )
    
    matches = point_pattern.findall(content)
    
    for match in matches:
        p_id, p_uf, p_ut, x, y, z, w, p, r = match
        points.append({
            'id': int(p_id),
            'uf': int(p_uf),
            'ut': int(p_ut),
            'x': float(x),
            'y': float(y),
            'z': float(z),
            'w': float(w),
            'p': float(p),
            'r': float(r)
        })
        
    logger.log(f"Found {len(points)} position points.")
    
    # Filter outliers
    import numpy as np
    coords = np.array([[p['x'], p['y'], p['z']] for p in points])
    median_center = np.median(coords, axis=0)
    dists = np.linalg.norm(coords - median_center, axis=1)
    
    median_dist = np.median(dists)
    threshold = median_dist * 1.5
    
    filtered_points = []
    for i, p in enumerate(points):
        if dists[i] <= threshold:
            filtered_points.append(p)
        else:
            logger.log(f"  Excluded outlier point P[{p['id']}] (dist {dists[i]:.1f} > threshold {threshold:.1f})")
            
    logger.log(f"Kept {len(filtered_points)} points after filtering outliers.")
    return filtered_points

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True, help="Session ID for output directory")
    args = parser.parse_args()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    logger = PipelineLogger(args.session, base_dir, "STEP 01: PARSE LS FILE")
    
    config_path = os.path.join(base_dir, 'pipeline_config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    ls_path = os.path.join(base_dir, config['paths']['ls_file'])
    
    if not os.path.exists(ls_path):
        logger.log(f"[FAIL] LS file not found: {ls_path}")
        sys.exit(1)
        
    points = parse_ls_file(ls_path, logger)
    
    if not points:
        logger.log("[FAIL] No points parsed.")
        sys.exit(1)
        
    output_path = os.path.join(logger.results_dir, 'step01_ls_points.json')
    with open(output_path, 'w') as f:
        json.dump(points, f, indent=2)
        
    logger.log(f"Successfully saved {len(points)} points to {output_path}")

if __name__ == '__main__':
    main()
