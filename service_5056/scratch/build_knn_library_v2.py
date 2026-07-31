import os
import json
import numpy as np
import cv2

# Build the expanded k-NN reference library (Variant 1, round 2): v1-v5 (original) plus the
# 9 new archive variants v7,v8,v9,v10,v11,v12,v14,v15,v16 (the 10th new capture, v13, and the
# original v6 are BOTH held out for validation only - never in this library).

TRAIN_VARIANTS = ['v1', 'v2', 'v3', 'v4', 'v5', 'v7', 'v8', 'v9', 'v10', 'v11', 'v12', 'v14', 'v15', 'v16']
HELD_OUT = ['v6', 'v13']
views = ['back', 'left', 'top']


def session_for(v):
    return f'test_eval_{v}'


def extract_feat(v):
    r = session_for(v)
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
    return np.array(feats)


def extract_gt(v):
    r = session_for(v)
    s5 = json.load(open(f'results/{r}/step05_result.json', encoding='utf-8'))
    gt = s5.get('gt_delta_3d', {})
    return np.array([gt.get('x_mm', 0), gt.get('y_mm', 0), gt.get('z_mm', 0),
                      gt.get('roll_deg', 0), gt.get('pitch_deg', 0), gt.get('yaw_deg', 0)])


raw_features = {v: extract_feat(v) for v in TRAIN_VARIANTS}
gt_ref_all = {v: extract_gt(v) for v in TRAIN_VARIANTS}

active_cols = [0, 1, 3, 4, 5, 6, 7, 8]  # drop back_top (index 2) - zero variance, matches step04 feat_vec order

X_all = np.array([raw_features[v][active_cols] for v in TRAIN_VARIANTS])
scale = np.std(X_all, axis=0)
scale[scale < 1e-6] = 1.0

# Fit W_calib: ridge regression anchored at V3 (arbitrary but consistent with prior rounds -
# anchor choice barely affects accuracy, already verified in Stage 1/2 of this project).
ANCHOR = 'v3'
X_mat = np.array([raw_features[v][active_cols] - raw_features[ANCHOR][active_cols] for v in TRAIN_VARIANTS])
Y_mat = np.array([gt_ref_all[v] - gt_ref_all[ANCHOR] for v in TRAIN_VARIANTS])

lam = 0.01
W = np.linalg.inv(X_mat.T @ X_mat + lam * np.eye(len(active_cols))) @ X_mat.T @ Y_mat
Y_pred = X_mat @ W

print("=== CALIBRATION CHECK (14-point library, anchor V3) ===")
target_names = ['X_mm', 'Y_mm', 'Z_mm', 'Roll_deg', 'Pitch_deg', 'Yaw_deg']
for i, v in enumerate(TRAIN_VARIANTS):
    diffs = Y_pred[i] - Y_mat[i]
    print(f"{v:4s}: max|diff| = {np.max(np.abs(diffs)):.3f}  ({dict(zip(target_names, np.round(diffs,2)))})")

print("\n=== KNN_SCALE ===")
print("KNN_SCALE = np.array(", list(np.round(scale, 4)), ")")

print("\n=== KNN_LIBRARY ===")
print("KNN_LIBRARY = {")
for v in TRAIN_VARIANTS:
    feat9 = raw_features[v]
    g = gt_ref_all[v]
    print(f'    "{v}": {{')
    print(f'        "ref_cm": {{')
    for i, view in enumerate(views):
        cx, cy, top_y = feat9[i*3], feat9[i*3+1], feat9[i*3+2]
        print(f'            "{view}": ({cx:.2f}, {cy:.2f}, {top_y:.2f}),')
    print(f'        }},')
    print(f'        "gt_ref": np.array({list(np.round(g, 2))}),')
    print(f'    }},')
print("}")

print("\n=== W_calib ===")
print("W_calib = np.array([")
for row in W:
    print("    [" + ", ".join(f"{x: .8f}" for x in row) + "],")
print("])")

# Pairwise gaps for OUT_OF_RANGE_THRESHOLD
print("\n=== Pairwise nearest-neighbor gaps ===")
nearest_gaps = []
for a in TRAIN_VARIANTS:
    row = []
    for b in TRAIN_VARIANTS:
        if a == b:
            continue
        d = np.linalg.norm((raw_features[a][active_cols] - raw_features[b][active_cols]) / scale)
        row.append(d)
    nearest = min(row)
    nearest_gaps.append(nearest)
    print(f"{a}: nearest-neighbor gap = {nearest:.3f}")

max_gap = max(nearest_gaps)
print(f"\nMax nearest-neighbor gap = {max_gap:.3f}")
print(f"Suggested OUT_OF_RANGE_THRESHOLD (x1.5) = {max_gap*1.5:.3f}")

# Held-out distances
print("\n=== Held-out variant distances to library ===")
for v in HELD_OUT:
    f = extract_feat(v)[active_cols]
    dists = {t: float(np.linalg.norm((f - raw_features[t][active_cols]) / scale)) for t in TRAIN_VARIANTS}
    ranked = sorted(dists.items(), key=lambda kv: kv[1])
    print(f"{v}: nearest={ranked[0]}, second={ranked[1]}")
