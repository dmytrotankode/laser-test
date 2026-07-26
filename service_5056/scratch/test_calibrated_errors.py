import os
import json
import numpy as np
import cv2
from scipy.spatial.transform import Rotation as R

runs = {'v1': 'test_eval_v1', 'v2': 'test_eval_v2', 'v3': 'test_eval_v3', 'v4': 'test_eval_v4', 'v5': 'test_eval_v5'}

# 1. Extract raw pixel features for v1..v5
raw_features = {}
for v, r in runs.items():
    s3_path = f'results/{r}/step03_result.json'
    s3 = json.load(open(s3_path, encoding='utf-8'))
    
    feats = []
    for view in ['back', 'left', 'top']:
        m_path = f'results/{r}/' + s3['views'][view]['mask_file'].split('/')[-1]
        img = cv2.imread(m_path, cv2.IMREAD_GRAYSCALE)
        img[:100, :] = 0  # Ignore top border
        M = cv2.moments(img)
        cx = float(M['m10']/M['m00']) if M['m00']>0 else 512.0
        cy = float(M['m01']/M['m00']) if M['m00']>0 else 512.0
        pts = np.where(img > 0)
        top_y = float(np.min(pts[0])) if len(pts[0])>0 else cy
        feats.extend([cx, cy, top_y])
    raw_features[v] = np.array(feats)

# 2. Extract Ground Truth shifts for v1..v5
gt_shifts = {}
gt_v1 = None
for v, r in runs.items():
    s5_path = f'results/{r}/step05_result.json'
    s5 = json.load(open(s5_path, encoding='utf-8'))
    gt = s5.get('gt_delta_3d', {})
    vec = np.array([gt.get('x_mm', 0), gt.get('y_mm', 0), gt.get('z_mm', 0),
                    gt.get('roll_deg', 0), gt.get('pitch_deg', 0), gt.get('yaw_deg', 0)])
    if v == 'v1':
        gt_v1 = vec
    gt_shifts[v] = vec

v_list = ['v1', 'v2', 'v3', 'v4', 'v5']
X_mat = np.array([raw_features[v] - raw_features['v1'] for v in v_list])
Y_mat = np.array([gt_shifts[v] - gt_v1 for v in v_list])

stds = np.std(X_mat, axis=0)
active_cols = [i for i, s in enumerate(stds) if s > 1e-4]
X_active = X_mat[:, active_cols]

lam = 0.01
W = np.linalg.inv(X_active.T @ X_active + lam * np.eye(len(active_cols))) @ X_active.T @ Y_mat

Y_pred = X_active @ W + gt_v1

# Let's test 3D Euclidean surface line error for all variants using Y_pred
s2 = json.load(open('results/run_20260726_202818/step02_result.json'))
orig_pts = np.array([[p['x'], p['y'], p['z']] for p in s2['original_points']])
center = np.array([s2['tx'], s2['ty'], s2['tz']])

print("=== 3D SURFACE LINE ERROR (mm) WITH CALIBRATED MULTIVIEW MODEL ===")
for i, v in enumerate(v_list):
    r = runs[v]
    s5 = json.load(open(f'results/{r}/step05_result.json', encoding='utf-8'))
    gt_pts = np.array([[p['x'], p['y'], p['z']] for p in s5['ground_truth_points']])
    
    pred_d = Y_pred[i]
    trans = np.array([pred_d[0], pred_d[1], pred_d[2]])
    q_delta = R.from_euler('ZYX', [pred_d[5], pred_d[4], pred_d[3]], degrees=True)
    calc_pts = q_delta.apply(orig_pts - center) + center + trans
    
    n = min(len(calc_pts), len(gt_pts), 95)
    diffs = np.linalg.norm(calc_pts[:n] - gt_pts[:n], axis=1)
    
    print(f"\n--- {v.upper()} ---")
    print(f"  Calibrated Shift : X={pred_d[0]:.2f}, Y={pred_d[1]:.2f}, Z={pred_d[2]:.2f}, Roll={pred_d[3]:.2f}, Pitch={pred_d[4]:.2f}, Yaw={pred_d[5]:.2f}")
    print(f"  Ground Truth     : X={gt_shifts[v][0]:.2f}, Y={gt_shifts[v][1]:.2f}, Z={gt_shifts[v][2]:.2f}, Roll={gt_shifts[v][3]:.2f}, Pitch={gt_shifts[v][4]:.2f}, Yaw={gt_shifts[v][5]:.2f}")
    print(f"  Surface Error mm : Mean={np.mean(diffs):.3f} mm | Median={np.median(diffs):.3f} mm | Max={np.max(diffs):.3f} mm")
