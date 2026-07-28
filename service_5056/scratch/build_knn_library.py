import os
import json
import numpy as np
import cv2

# Build the k-NN reference library for Variant 1 (dynamic etalon selection among v1-v5).
# v6 is intentionally excluded - held out for validation only.

runs = {'v1': 'test_eval_v1', 'v2': 'test_eval_v2', 'v3': 'test_eval_v3', 'v4': 'test_eval_v4', 'v5': 'test_eval_v5'}
views = ['back', 'left', 'top']

raw_features = {}
for v, r in runs.items():
    s3 = json.load(open(f'results/{r}/step03_result.json', encoding='utf-8'))
    feats = []
    for view in views:
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

gt_ref = {}
for v, r in runs.items():
    s5 = json.load(open(f'results/{r}/step05_result.json', encoding='utf-8'))
    gt = s5.get('gt_delta_3d', {})
    gt_ref[v] = np.array([gt.get('x_mm', 0), gt.get('y_mm', 0), gt.get('z_mm', 0),
                           gt.get('roll_deg', 0), gt.get('pitch_deg', 0), gt.get('yaw_deg', 0)])

v_list = ['v1', 'v2', 'v3', 'v4', 'v5']
active_cols = [0, 1, 3, 4, 5, 6, 7, 8]  # drop back_top (index 2), zero variance - matches step04 feat_vec order

# Normalization scale: std of each active feature across the library (for distance calc)
X_all = np.array([raw_features[v][active_cols] for v in v_list])
scale = np.std(X_all, axis=0)
scale[scale < 1e-6] = 1.0

print("=== KNN_LIBRARY (paste into step04) ===")
print("KNN_SCALE = np.array(", list(np.round(scale, 4)), ")")
print()
print("KNN_LIBRARY = {")
for v in v_list:
    feat9 = raw_features[v]
    g = gt_ref[v]
    print(f'    "{v}": {{')
    print(f'        "ref_cm": {{')
    for i, view in enumerate(views):
        cx, cy, top_y = feat9[i*3], feat9[i*3+1], feat9[i*3+2]
        print(f'            "{view}": ({cx:.2f}, {cy:.2f}, {top_y:.2f}),')
    print(f'        }},')
    print(f'        "gt_ref": np.array({list(np.round(g, 2))}),')
    print(f'    }},')
print("}")

# Typical inter-sample gap: for each library point, distance to its nearest OTHER library point
print("\n=== Pairwise distances (normalized) between library points ===")
dists = {}
for a in v_list:
    row = []
    for b in v_list:
        if a == b:
            continue
        d = np.linalg.norm((raw_features[a][active_cols] - raw_features[b][active_cols]) / scale)
        row.append(d)
        dists[(a, b)] = d
    nearest = min(row)
    print(f"{a}: nearest-neighbor gap = {nearest:.3f}  (all: {np.round(row,3)})")

max_gap = max(min(d for (a2,b2),d in dists.items() if a2==a) for a in v_list)
print(f"\nMax nearest-neighbor gap among library = {max_gap:.3f}")
print(f"Suggested OUT_OF_RANGE_THRESHOLD (x1.5 safety margin) = {max_gap*1.5:.3f}")
