import os
import sys
import json
import numpy as np
from stl import mesh
import argparse
from logger import PipelineLogger
from scipy.spatial.distance import cdist

def get_stl_outer_rim(stl_mesh, max_z_threshold=45):
    vertices = stl_mesh.vectors.reshape(-1, 3)
    min_z = np.min(vertices[:, 2])
    mask = vertices[:, 2] <= (min_z + max_z_threshold)
    rim_pts = vertices[mask]
    
    if len(rim_pts) == 0:
        return np.array([])
        
    centroid = np.mean(rim_pts, axis=0)
    dx = rim_pts[:, 0] - centroid[0]
    dy = rim_pts[:, 1] - centroid[1]
    angles = np.arctan2(dy, dx)
    radii = np.sqrt(dx**2 + dy**2)
    
    bins = np.linspace(-np.pi, np.pi, 361)
    indices = np.digitize(angles, bins)
    
    outer_pts = []
    for i in range(1, len(bins)):
        in_bin = np.where(indices == i)[0]
        if len(in_bin) > 0:
            max_idx = in_bin[np.argmax(radii[in_bin])]
            outer_pts.append(rim_pts[max_idx])
            
    return np.array(outer_pts)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    args = parser.parse_args()
    
    session_id = args.session
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    session_dir = os.path.join(base_dir, 'results', session_id)
    
    logger = PipelineLogger(session_id, base_dir, "STEP 03: FREEZE 3D SPACE")
    
    config_path = os.path.join(base_dir, 'pipeline_config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
        
    # 1. Load Step 1 LS Points
    ls_points_path = os.path.join(session_dir, 'step01_ls_points.json')
    if not os.path.exists(ls_points_path):
        logger.log("Error: step01_ls_points.json not found!")
        sys.exit(1)
        
    with open(ls_points_path, 'r') as f:
        ls_data = json.load(f)
    ls_points = np.array([[p['x'], p['y'], p['z']] for p in ls_data])
    
    # 2. Load Step 2 Alignment
    align_file = os.path.join(session_dir, 'step02_alignment.json')
    if not os.path.exists(align_file):
        logger.log("Error: step02_alignment.json not found!")
        sys.exit(1)
        
    with open(align_file, 'r') as f:
        align_data = json.load(f)
        T_matrix = np.array(align_data['matrix_4x4'])
        
    # 3. Load and Transform STL
    stl_path = os.path.join(base_dir, config['paths']['model_stl'])
    helmet_mesh = mesh.Mesh.from_file(stl_path)
    
    # Extract rim from ORIGINAL mesh before transformation to avoid orientation bugs (e.g. Rx=180)
    stl_rim_original = get_stl_outer_rim(helmet_mesh, max_z_threshold=45)
    
    # Now we can apply transformation to the full mesh
    vertices = helmet_mesh.vectors.reshape(-1, 3)
    ones = np.ones((vertices.shape[0], 1))
    vertices_4d = np.hstack([vertices, ones])
    transformed_vertices = (T_matrix @ vertices_4d.T).T[:, :3]
    
    # Save aligned STL
    helmet_mesh.vectors = transformed_vertices.reshape(-1, 3, 3)
    aligned_stl_path = os.path.join(session_dir, 'helmet_aligned.stl')
    helmet_mesh.save(aligned_stl_path)
    logger.log(f"Saved aligned 3D model to {aligned_stl_path}")
    
    # Transform the rim points
    if len(stl_rim_original) > 0:
        rim_ones = np.ones((stl_rim_original.shape[0], 1))
        rim_4d = np.hstack([stl_rim_original, rim_ones])
        transformed_rim = (T_matrix @ rim_4d.T).T[:, :3]
    else:
        transformed_rim = np.array([])
        
    # Calculate distance from each LS point to the nearest transformed STL rim point
    dists = cdist(ls_points, transformed_rim)
    min_dists = np.min(dists, axis=1)
    
    # Filter out points that are too far away (e.g. > 35mm from the helmet rim)
    # This removes scanning artifacts far outside the head bounding box
    threshold = 35.0
    valid_mask = min_dists < threshold
    filtered_ls_points = ls_points[valid_mask]
    
    dropped_count = len(ls_points) - len(filtered_ls_points)
    logger.log(f"Filtered {dropped_count} outlier LS points (distance > {threshold}mm).")
    
    # Save filtered LS points
    filtered_ls_data = []
    for i, p in enumerate(filtered_ls_points):
        filtered_ls_data.append({'id': i, 'x': float(p[0]), 'y': float(p[1]), 'z': float(p[2])})
        
    filtered_ls_path = os.path.join(session_dir, 'step03_filtered_ls.json')
    with open(filtered_ls_path, 'w') as f:
        json.dump(filtered_ls_data, f, indent=4)
        
    logger.log(f"Saved {len(filtered_ls_points)} filtered LS points to {filtered_ls_path}")
    
    out_dict = {
        'status': 'success',
        'points_dropped': int(dropped_count),
        'remaining_points': len(filtered_ls_points)
    }
    
    out_json = os.path.join(session_dir, 'step03_freeze_space.json')
    with open(out_json, 'w') as f:
        json.dump(out_dict, f, indent=2)

if __name__ == '__main__':
    main()
