import os
import sys
import json
import math
import argparse
import numpy as np

import re

def load_ls_file(path):
    """
    Load coordinates from an LS file using regex.
    """
    points = []
    if not os.path.exists(path):
        raise FileNotFoundError(f"LS file not found: {path}")
        
    with open(path, 'r') as f:
        content = f.read()
        
    point_pattern = re.compile(
        r'P\[(\d+)\]\{\s*GP1:\s*UF\s*:\s*(\d+),\s*UT\s*:\s*(\d+).*?X\s*=\s*([-\d.]+).*?Y\s*=\s*([-\d.]+).*?Z\s*=\s*([-\d.]+).*?W\s*=\s*([-\d.]+).*?P\s*=\s*([-\d.]+).*?R\s*=\s*([-\d.]+)',
        re.DOTALL | re.IGNORECASE
    )
    
    matches = point_pattern.findall(content)
    for match in matches:
        points.append({
            'id': int(match[0]),
            'x': float(match[3]),
            'y': float(match[4]),
            'z': float(match[5])
        })
    return points

def filter_contour_points(points):
    """
    Remove external start/finish points to get the continuous contour.
    Typically, the contour is the main body of points, 
    while the first few and last few are approach/retreat points.
    We'll do a simple heuristic: remove the first 2 and last 2 points 
    (or any that jump significantly).
    For simplicity and reliability based on standard robot paths, 
    we slice the array.
    """
    if len(points) < 10:
        return points
        
    # Heuristic: the start and end of the actual cutting path
    # Often, approach is 2-3 points, retreat is 2-3 points.
    return points[3:-3]

def calculate_trim_line(contour_points, tilt_down_deg=15, yaw_ccw_deg=15, offset_mm=10.0):
    """
    Calculate the actual trim line (contact points) by offsetting the contour points.
    """
    pts = np.array([[p['x'], p['y'], p['z']] for p in contour_points])
    if len(pts) < 2:
        return contour_points
        
    # Calculate centroid
    centroid_xy = np.mean(pts[:, :2], axis=0)
    
    contact_points = []
    angle_rad = math.radians(tilt_down_deg)
    
    for i in range(len(pts)):
        p = pts[i]
        
        # Calculate tangent
        if i < len(pts) - 1:
            T = pts[i+1] - p
        else:
            T = p - pts[i-1]
            
        T_xy = T[:2]
        norm = np.linalg.norm(T_xy)
        if norm > 0:
            T_xy = T_xy / norm
        else:
            T_xy = np.array([1.0, 0.0])
            
        # Outward normal
        outward = p[:2] - centroid_xy
        N_xy = np.array([-T_xy[1], T_xy[0]])
        if np.dot(N_xy, outward) > 0:
            N_xy = -N_xy 
            
        # D_xy direction
        D_xy = N_xy * math.cos(angle_rad) - T_xy * math.sin(angle_rad)
        
        # Offset 10mm
        p_contact_xy = p[:2] + offset_mm * D_xy
        p_contact_z = p[2] + offset_mm * math.tan(angle_rad)
        
        contact_points.append({'x': float(p_contact_xy[0]), 'y': float(p_contact_xy[1]), 'z': float(p_contact_z)})
        
    return contact_points

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    args = parser.parse_args()
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ls_path = os.path.join(base_dir, 'input', 'ls_file', 'TORXL_NEW_PROG.LS')
    results_dir = os.path.join(base_dir, 'results', args.session)
    
    # 1. Load LS
    original_points = load_ls_file(ls_path)
    
    # 2. Filter external points
    contour_points = filter_contour_points(original_points)
    
    # 3. Calculate metrics
    tilt_down_deg = 15
    yaw_ccw_deg = 15
    offset_mm = 10.0
    
    contact_points = calculate_trim_line(contour_points, tilt_down_deg, yaw_ccw_deg, offset_mm)
    
    # 4. Save results
    result_data = {
        "ls_path": ls_path,
        "tilt_down_deg": tilt_down_deg,
        "yaw_ccw_deg": yaw_ccw_deg,
        "offset_mm": offset_mm,
        "original_points": original_points,
        "contour_points": contour_points,
        "contact_points": contact_points
    }
    
    with open(os.path.join(results_dir, 'step01_result.json'), 'w') as f:
        json.dump(result_data, f)

if __name__ == '__main__':
    main()
