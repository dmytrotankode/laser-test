import os
import sys
import json
import math
import numpy as np
from stl import mesh
from scipy.optimize import minimize
import argparse

def get_rotation_matrix(rx, ry, rz):
    rx, ry, rz = np.radians(rx), np.radians(ry), np.radians(rz)
    Rx = np.array([[1, 0, 0], [0, np.cos(rx), -np.sin(rx)], [0, np.sin(rx), np.cos(rx)]])
    Ry = np.array([[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]])
    Rz = np.array([[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx

def get_transform_matrix(tx, ty, tz, rx, ry, rz, s=1.0):
    T = np.eye(4)
    T[:3, :3] = get_rotation_matrix(rx, ry, rz)
    T[0, 3] = tx
    T[1, 3] = ty
    T[2, 3] = tz
    S = np.diag([s, s, s, 1.0])
    return T @ S

def transform_points(points, T):
    ones = np.ones((points.shape[0], 1))
    pts_4d = np.hstack([points, ones])
    transformed = (T @ pts_4d.T).T
    return transformed[:, :3]

def get_stl_outer_rim(stl_mesh, max_z_threshold=45):
    vertices = stl_mesh.vectors.reshape(-1, 3)
    min_z = np.min(vertices[:, 2])
    mask = vertices[:, 2] <= (min_z + max_z_threshold)
    rim_pts = vertices[mask]
    
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

def align_cost(params, ls_points, stl_rim_points):
    tx, ty, tz, rx, ry, rz = params
    T = get_transform_matrix(tx, ty, tz, rx, ry, rz, 1.0)
    transformed_stl = transform_points(stl_rim_points, T)
    from scipy.spatial.distance import cdist
    dists = cdist(ls_points, transformed_stl)
    min_dists = np.min(dists, axis=1)
    return np.mean(min_dists**2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    args = parser.parse_args()
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_dir = os.path.join(base_dir, 'results', args.session)
    
    step01_path = os.path.join(results_dir, 'step01_result.json')
    if not os.path.exists(step01_path):
        print("Missing step01_result.json")
        sys.exit(1)
        
    with open(step01_path, 'r') as f:
        step01_data = json.load(f)
        
    contact_points = np.array([[p['x'], p['y'], p['z']] for p in step01_data['contact_points']])
    
    stl_path = os.path.join(base_dir, 'input', 'model_3d', 'helmet_ref.stl')
    if not os.path.exists(stl_path):
        print(f"Missing {stl_path}")
        sys.exit(1)
        
    helmet_mesh = mesh.Mesh.from_file(stl_path)
    stl_rim = get_stl_outer_rim(helmet_mesh, max_z_threshold=45)
    
    ls_center = np.mean(contact_points, axis=0)
    stl_center = np.mean(stl_rim, axis=0)
    
    tx_init = ls_center[0] - stl_center[0]
    ty_init = ls_center[1] - stl_center[1]
    tz_init = ls_center[2] - stl_center[2]
    
    best_res = None
    best_cost = float('inf')
    
    for init_rx in [0, 180]:
        for init_rz in [0, 90, 180, 270]:
            initial_guess = [tx_init, ty_init, tz_init, init_rx, 0.0, init_rz]
            res = minimize(
                align_cost, initial_guess, args=(contact_points, stl_rim),
                method='Powell', options={'maxiter': 100}
            )
            if res.fun < best_cost:
                best_cost = res.fun
                best_res = res
                
    tx, ty, tz, rx, ry, rz = best_res.x
    s = 1.0
    T_best = get_transform_matrix(tx, ty, tz, rx, ry, rz, s)
    
    transformed_stl = transform_points(stl_rim, T_best)
    
    vertices = helmet_mesh.vectors.reshape(-1, 3)
    transformed_full_mesh = transform_points(vertices, T_best)
    subsampled = transformed_full_mesh[::30]
    
    result_data = {
        "model_path": stl_path,
        "tx": float(tx), "ty": float(ty), "tz": float(tz),
        "rx": float(rx), "ry": float(ry), "rz": float(rz),
        "scale": float(s),
        "cost": float(best_cost),
        "stl_rim": [{"x": float(p[0]), "y": float(p[1]), "z": float(p[2])} for p in transformed_stl],
        "stl_mesh": [{"x": float(p[0]), "y": float(p[1]), "z": float(p[2])} for p in subsampled],
        "original_points": step01_data['original_points'],
        "ls_contour": step01_data['contour_points'],
        "contact_points": step01_data['contact_points']
    }
    
    with open(os.path.join(results_dir, 'step02_result.json'), 'w') as f:
        json.dump(result_data, f)

if __name__ == '__main__':
    main()
