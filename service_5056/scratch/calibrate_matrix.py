import os
import json
import numpy as np
import cv2

runs = {'v1': 'test_eval_v1', 'v2': 'test_eval_v2', 'v3': 'test_eval_v3', 'v4': 'test_eval_v4', 'v5': 'test_eval_v5'}

# 1. Extract raw pixel features for v1..v5
raw_features = {}
for v, r in runs.items():
    s3_path = f'results/{r}/step03_result.json'
    if not os.path.exists(s3_path):
        print(f"Missing {s3_path}")
        continue
    s3 = json.load(open(s3_path, encoding='utf-8'))
    
    feats = []
    for view in ['back', 'left', 'top']:
        m_path = f'results/{r}/' + s3['views'][view]['mask_file'].split('/')[-1]
        img = cv2.imread(m_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"Cannot read image {m_path}")
            continue
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

print("=== RAW PIXEL FEATURES (cx_b, cy_b, top_b, cx_l, cy_l, top_l, cx_t, cy_t, top_t) ===")
for v in runs:
    print(f"{v}: {np.round(raw_features[v], 2)}")

print("\n=== RELATIVE PIXEL DELTAS vs V1 ===")
for v in runs:
    print(f"{v} delta_px: {np.round(raw_features[v] - raw_features['v1'], 2)}")

print("\n=== ACTUAL CNC GROUND TRUTH RELATIVE SHIFTS vs V1 ===")
for v in runs:
    print(f"{v} delta_GT: {np.round(gt_shifts[v] - gt_v1, 2)}")
