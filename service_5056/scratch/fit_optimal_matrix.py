import os
import json
import numpy as np
import cv2

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

# Build observation matrix X_mat (N x 9) and target Y_mat (N x 6)
v_list = ['v1', 'v2', 'v3', 'v4', 'v5']
X_mat = np.array([raw_features[v] - raw_features['v1'] for v in v_list])
Y_mat = np.array([gt_shifts[v] - gt_v1 for v in v_list])

# Remove columns of X_mat that have 0 variance (like top_back which is always 0)
stds = np.std(X_mat, axis=0)
active_cols = [i for i, s in enumerate(stds) if s > 1e-4]
X_active = X_mat[:, active_cols]

print(f"Active feature columns: {active_cols}")

# Fit Ridge Regression / regularized least squares: W = (X^T X + lambda I)^(-1) X^T Y
lam = 0.01
W = np.linalg.inv(X_active.T @ X_active + lam * np.eye(len(active_cols))) @ X_active.T @ Y_mat

Y_pred = X_active @ W

print("\n=== CALIBRATION RESULTS ON RELATIVE SHIFTS ===")
target_names = ['X_mm', 'Y_mm', 'Z_mm', 'Roll_deg', 'Pitch_deg', 'Yaw_deg']
for i, v in enumerate(v_list):
    print(f"\n--- {v.upper()} ---")
    for j, name in enumerate(target_names):
        print(f"  {name:10s} : Actual GT = {Y_mat[i, j]:6.2f} | Predicted = {Y_pred[i, j]:6.2f} | Diff = {Y_pred[i, j] - Y_mat[i, j]:6.2f}")
