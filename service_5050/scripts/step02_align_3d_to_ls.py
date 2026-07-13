import os
import sys
import json
import math
import numpy as np
from stl import mesh
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import argparse
from logger import PipelineLogger

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
    tx, ty, tz, rx, ry, rz, s = params
    T = get_transform_matrix(tx, ty, tz, rx, ry, rz, s)
    transformed_stl = transform_points(stl_rim_points, T)
    from scipy.spatial.distance import cdist
    dists = cdist(ls_points, transformed_stl)
    min_dists = np.min(dists, axis=1)
    return np.mean(min_dists**2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    args = parser.parse_args()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    logger = PipelineLogger(args.session, base_dir, "STEP 02: ALIGN 3D TO LS")
    
    config_path = os.path.join(base_dir, 'pipeline_config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    ls_points_path = os.path.join(logger.results_dir, 'step01_ls_points.json')
    if not os.path.exists(ls_points_path):
        logger.log(f"[FAIL] Missing {ls_points_path}. Run Step 01 first.")
        sys.exit(1)
        
    with open(ls_points_path, 'r') as f:
        ls_data = json.load(f)
        
    raw_points = np.array([[p['x'], p['y'], p['z']] for p in ls_data])
    
    contact_points = []
    n_pts = len(raw_points)
    centroid_xy = np.mean(raw_points[:, :2], axis=0)
    
    for i in range(n_pts):
        P = raw_points[i]
        
        if i == 0:
            T = raw_points[i+1] - raw_points[i]
        elif i == n_pts - 1:
            T = raw_points[i] - raw_points[i-1]
        else:
            T = raw_points[i+1] - raw_points[i-1]
            
        T_xy = T[:2]
        T_norm = np.linalg.norm(T_xy)
        if T_norm > 0:
            T_xy = T_xy / T_norm
        else:
            T_xy = np.array([1.0, 0.0])
            
        outward = P[:2] - centroid_xy
        N_xy = np.array([-T_xy[1], T_xy[0]])
        if np.dot(N_xy, outward) > 0:
            N_xy = -N_xy 
            
        angle_rad = math.radians(15)
        # Looking inward (N), Left is opposite to CCW tangent (-T)
        D_xy = N_xy * math.cos(angle_rad) - T_xy * math.sin(angle_rad)
        
        P_contact_xy = P[:2] + 10.0 * D_xy
        # Robot Z is inverted (-Z is UP), so to go DOWN we ADD to Z
        P_contact_z = P[2] + 10.0 * math.tan(angle_rad)
        
        contact_points.append([P_contact_xy[0], P_contact_xy[1], P_contact_z])
        
    ls_points = np.array(contact_points)
    logger.log(f"Calculated {len(ls_points)} contact points (10mm offset, 15deg down/left).")
    
    contact_out_path = os.path.join(logger.results_dir, 'step02_contact_points.json')
    with open(contact_out_path, 'w') as f:
        json.dump([{'x': float(p[0]), 'y': float(p[1]), 'z': float(p[2])} for p in ls_points], f)
    
    stl_path = os.path.join(base_dir, config['paths']['model_stl'])
    if not os.path.exists(stl_path):
        logger.log(f"[FAIL] Missing {stl_path}.")
        sys.exit(1)
        
    helmet_mesh = mesh.Mesh.from_file(stl_path)
    logger.log(f"Loaded STL with {len(helmet_mesh.vectors)} triangles.")
    
    stl_rim = get_stl_outer_rim(helmet_mesh, max_z_threshold=45)
    logger.log(f"Extracted {len(stl_rim)} points from STL OUTER rim.")
    
    ls_center = np.mean(ls_points, axis=0)
    stl_center = np.mean(stl_rim, axis=0)
    
    tx_init = ls_center[0] - stl_center[0]
    ty_init = ls_center[1] - stl_center[1]
    tz_init = ls_center[2] - stl_center[2]
    
    best_res = None
    best_cost = float('inf')
    best_initial_rz = 0
    best_initial_rx = 0
    
    logger.log("Running PASS 1: optimization with multiple configurations...")
    for init_rx in [0, 180]:
        for init_rz in [0, 90, 180, 270]:
            initial_guess = [tx_init, ty_init, tz_init, init_rx, 0.0, init_rz, 1.0]
            res = minimize(
                align_cost, initial_guess, args=(ls_points, stl_rim),
                method='Powell', options={'maxiter': 800, 'disp': False}
            )
            logger.log(f"  Init Rx={init_rx:3d}°, Rz={init_rz:3d}° -> Cost: {res.fun:.2f} (Scale: {res.x[6]:.3f})")
            if res.fun < best_cost:
                best_cost = res.fun
                best_res = res
                best_initial_rz = init_rz
                best_initial_rx = init_rx
            
    logger.log(f"Best initial configuration was Rx={best_initial_rx}°, Rz={best_initial_rz}° with cost {best_cost:.2f}")
    
    logger.log("Running PASS 2: refinement pass to fine-tune scale and pose...")
    res_refined = minimize(
        align_cost, best_res.x, args=(ls_points, stl_rim),
        method='Nelder-Mead', options={'maxiter': 2000, 'xatol': 1e-4, 'fatol': 1e-4, 'disp': False}
    )
    
    if res_refined.fun < best_res.fun:
        res = res_refined
        logger.log(f"Refinement improved cost to {res.fun:.4f}")
    else:
        res = best_res
        logger.log(f"Refinement did not improve cost. Kept {res.fun:.4f}")
    
    logger.log("Running PASS 3: balancing pass (Bounding Box 'Cross-Check')...")
    T_current = get_transform_matrix(res.x[0], res.x[1], res.x[2], res.x[3], res.x[4], res.x[5], res.x[6])
    transformed_stl = transform_points(stl_rim, T_current)
    
    trans_stl_min = np.min(transformed_stl[:, :2], axis=0)
    trans_stl_max = np.max(transformed_stl[:, :2], axis=0)
    trans_stl_center_xy = (trans_stl_min + trans_stl_max) / 2.0
    
    ls_min = np.min(ls_points[:, :2], axis=0)
    ls_max = np.max(ls_points[:, :2], axis=0)
    ls_center_xy = (ls_min + ls_max) / 2.0
    
    offset_x = ls_center_xy[0] - trans_stl_center_xy[0]
    offset_y = ls_center_xy[1] - trans_stl_center_xy[1]
    
    tx_bal = res.x[0] + offset_x
    ty_bal = res.x[1] + offset_y
    
    logger.log(f"Balancing adjusted Tx: {res.x[0]:.2f} -> {tx_bal:.2f}, Ty: {res.x[1]:.2f} -> {ty_bal:.2f}")
    res.x[0] = tx_bal
    res.x[1] = ty_bal
    
    if not res.success:
        logger.log("[WARNING] Optimization might not have fully converged!")
        
    tx_opt, ty_opt, tz_opt, rx_opt, ry_opt, rz_opt, s_opt = res.x
    logger.log(f"Optimized Transform:")
    logger.log(f"  Translation (mm): tx={tx_opt:.2f}, ty={ty_opt:.2f}, tz={tz_opt:.2f}")
    logger.log(f"  Rotation (deg):   rx={rx_opt:.2f}, ry={ry_opt:.2f}, rz={rz_opt:.2f}")
    logger.log(f"  Scale:            s={s_opt:.4f}")
    logger.log(f"  Final Cost (MSE): {res.fun:.4f}")
    
    T_opt = get_transform_matrix(tx_opt, ty_opt, tz_opt, rx_opt, ry_opt, rz_opt, s_opt)
    
    out_dict = {
        'tx': float(tx_opt),
        'ty': float(ty_opt),
        'tz': float(tz_opt),
        'rx': float(rx_opt),
        'ry': float(ry_opt),
        'rz': float(rz_opt),
        'scale': float(s_opt),
        'matrix_4x4': T_opt.tolist(),
        'mse_cost': float(res.fun)
    }
    
    out_path = os.path.join(logger.results_dir, 'step02_alignment.json')
    with open(out_path, 'w') as f:
        json.dump(out_dict, f, indent=2)
    logger.log(f"Saved transform matrix to {out_path}")
    
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(ls_points[:, 0], ls_points[:, 1], ls_points[:, 2], c='red', s=10, label='LS Points')
    transformed_rim = transform_points(stl_rim, T_opt)
    ax.scatter(transformed_rim[:, 0], transformed_rim[:, 1], transformed_rim[:, 2], c='blue', s=2, alpha=0.3, label='Transformed STL Rim')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.legend()
    plt.title("3D Alignment: LS Oval vs STL Bottom Rim")
    
    plot_path = os.path.join(logger.results_dir, 'step02_alignment_plot.png')
    plt.savefig(plot_path)
    logger.log(f"Saved visualization plot to {plot_path}")

if __name__ == '__main__':
    main()
