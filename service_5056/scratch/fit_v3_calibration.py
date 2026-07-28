import os
import json
import numpy as np
import cv2

# Recompute W_calib and reference constants centered on V3 instead of V1,
# using cached pipeline results in results/test_eval_v1..v5.
# v6 is intentionally NEVER touched here - held out for independent validation.

runs = {'v1': 'test_eval_v1', 'v2': 'test_eval_v2', 'v3': 'test_eval_v3', 'v4': 'test_eval_v4', 'v5': 'test_eval_v5'}

raw_features = {}
for v, r in runs.items():
    s3_path = f'results/{r}/step03_result.json'
    s3 = json.load(open(s3_path, encoding='utf-8'))
    feats = []
    for view in ['back', 'left', 'top']:
        m_path = f'results/{r}/' + s3['views'][view]['mask_file'].split('/')[-1]
        img = cv2.imread(m_path, cv2.IMREAD_GRAYSCALE)
        img[:100, :] = 0
        M = cv2.moments(img)
        cx = float(M['m10']/M['m00']) if M['m00'] > 0 else 512.0
        cy = float(M['m01']/M['m00']) if M['m00'] > 0 else 512.0
        pts = np.where(img > 0)
        top_y = float(np.min(pts[0])) if len(pts[0]) > 0 else cy
        feats.extend([cx, cy, top_y])
    raw_features[v] = np.array(feats)

gt_shifts = {}
for v, r in runs.items():
    s5 = json.load(open(f'results/{r}/step05_result.json', encoding='utf-8'))
    gt = s5.get('gt_delta_3d', {})
    gt_shifts[v] = np.array([gt.get('x_mm', 0), gt.get('y_mm', 0), gt.get('z_mm', 0),
                              gt.get('roll_deg', 0), gt.get('pitch_deg', 0), gt.get('yaw_deg', 0)])

ANCHOR = 'v3'
v_list = ['v1', 'v2', 'v3', 'v4', 'v5']

X_mat = np.array([raw_features[v] - raw_features[ANCHOR] for v in v_list])
Y_mat = np.array([gt_shifts[v] - gt_shifts[ANCHOR] for v in v_list])

stds = np.std(X_mat, axis=0)
active_cols = [i for i, s in enumerate(stds) if s > 1e-4]
X_active = X_mat[:, active_cols]

print(f"Active feature columns (0-8, back_cx,back_cy,back_top,left_cx,left_cy,left_top,top_cx,top_cy,top_top): {active_cols}")

lam = 0.01
W = np.linalg.inv(X_active.T @ X_active + lam * np.eye(len(active_cols))) @ X_active.T @ Y_mat

Y_pred = X_active @ W

print("\n=== CALIBRATION CHECK, anchored on V3 ===")
target_names = ['X_mm', 'Y_mm', 'Z_mm', 'Roll_deg', 'Pitch_deg', 'Yaw_deg']
for i, v in enumerate(v_list):
    print(f"\n--- {v.upper()} ---")
    for j, name in enumerate(target_names):
        print(f"  {name:10s} : Actual GT_delta = {Y_mat[i, j]:6.2f} | Predicted = {Y_pred[i, j]:6.2f} | Diff = {Y_pred[i, j] - Y_mat[i, j]:6.2f}")

print("\n=== NEW CONSTANTS FOR step04_fit_3d_pose.py ===")
views = ['back', 'left', 'top']
print("ref_cm = {")
feat_v3 = raw_features[ANCHOR]
for i, view in enumerate(views):
    cx, cy, top_y = feat_v3[i*3], feat_v3[i*3+1], feat_v3[i*3+2]
    print(f'    "{view}": ({cx:.2f}, {cy:.2f}, {top_y:.2f}),')
print("}")

print(f"\ngt_ref = np.array({list(np.round(gt_shifts[ANCHOR], 2))})")

print("\nW_calib (active_cols order preserved, shape {}x6) =".format(len(active_cols)))
np.set_printoptions(suppress=True, precision=8)
print(repr(W))
print("\nactive_cols indices used (must match feature vector order built in step04):", active_cols)
