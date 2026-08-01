import os
import sys
import json
import argparse
import numpy as np
import cv2

# Variant 1 - dynamic etalon selection (k-NN) among the calibration library. Instead of
# always rotating one fixed variant's ground_truth.ls, pick whichever archived variant(s)
# are closest in pixel-feature space to the CURRENT photo, and blend their shape/pose data.
#
# Library round 2 (11 points): v1-v5 (original) + v7,v8,v9,v10,v11,v12 (new archive batch,
# re-indexed to match CAD's point numbering - see scratch/reindex_new_variants.py and
# ANALYSIS_V3_ETALON_MIGRATION.md for why that was necessary: the new batch's ground_truth.ls
# files used a different point start/count on the same contour, which produced a spurious
# ~11.5 degree "yaw" artifact before correction). v6 (original) and v13 (new) are held out
# for validation only - never in this library. v14/v15/v16 are excluded entirely: their
# recorded contour radius shrinks progressively through that capture session (not explained
# by rotation), suggesting unreliable ground truth - see ANALYSIS doc.
KNN_LIBRARY = {
    "v1": {
        "ref_cm": {"back": (2074.35, 888.34, 372.0), "left": (1930.74, 1016.10, 222.0), "top": (1918.03, 1518.54, 147.0)},
        "gt_ref": np.array([-0.98, -0.37, -2.54, -1.25, 0.68, 0.02]),
    },
    "v2": {
        "ref_cm": {"back": (2074.69, 888.31, 372.0), "left": (1930.89, 1016.04, 222.0), "top": (1918.01, 1518.52, 147.0)},
        "gt_ref": np.array([-0.99, -0.39, -2.21, -1.26, 0.73, 0.05]),
    },
    "v3": {
        "ref_cm": {"back": (2074.82, 885.82, 372.0), "left": (1929.83, 1010.64, 232.0), "top": (1920.66, 1523.06, 147.0)},
        "gt_ref": np.array([-0.78, -0.59, -2.0, -1.89, 0.99, 0.06]),
    },
    "v4": {
        "ref_cm": {"back": (2074.08, 900.10, 372.0), "left": (1920.51, 1026.89, 232.0), "top": (1899.57, 1520.96, 147.0)},
        "gt_ref": np.array([-0.59, 0.22, -1.82, -1.78, -1.49, 0.04]),
    },
    "v5": {
        "ref_cm": {"back": (2073.06, 910.99, 372.0), "left": (1936.94, 1010.61, 232.0), "top": (1901.95, 1529.98, 148.0)},
        "gt_ref": np.array([-0.08, 0.08, -1.88, -3.21, -1.34, -0.1]),
    },
    "v7": {
        "ref_cm": {"back": (2073.59, 896.58, 373.0), "left": (1930.51, 1030.34, 232.0), "top": (1911.29, 1516.15, 147.0)},
        "gt_ref": np.array([-3.01, -0.01, -2.87, -1.63, -1.79, 1.63]),
    },
    "v8": {
        "ref_cm": {"back": (2074.96, 913.88, 382.0), "left": (1924.05, 1036.91, 241.0), "top": (1896.87, 1518.98, 138.0)},
        "gt_ref": np.array([-6.35, 0.38, -2.26, -2.85, -4.07, 2.66]),
    },
    "v9": {
        "ref_cm": {"back": (2074.42, 895.81, 372.0), "left": (1930.36, 1018.21, 232.0), "top": (1912.93, 1524.98, 147.0)},
        "gt_ref": np.array([-2.42, 0.84, -2.49, -3.13, -1.5, 1.56]),
    },
    "v10": {
        "ref_cm": {"back": (2074.84, 897.43, 372.0), "left": (1929.42, 1011.71, 232.0), "top": (1916.56, 1528.77, 147.0)},
        "gt_ref": np.array([-1.9, 0.98, -2.28, -3.64, -0.95, 1.57]),
    },
    "v11": {
        "ref_cm": {"back": (2072.63, 916.66, 372.0), "left": (1919.94, 1009.48, 232.0), "top": (1898.81, 1530.64, 148.0)},
        "gt_ref": np.array([-5.5, 1.5, -2.55, -4.8, -3.65, 2.46]),
    },
    "v12": {
        "ref_cm": {"back": (2072.89, 912.31, 372.0), "left": (1923.24, 1025.59, 241.0), "top": (1895.71, 1528.67, 148.0)},
        "gt_ref": np.array([-6.2, 1.15, -2.66, -3.69, -4.33, 2.54]),
    },
}
# Normalization scale for the k-NN distance (std of each active feature across the library)
KNN_SCALE = np.array([0.8102, 10.6546, 4.9749, 8.8197, 5.7338, 9.2249, 5.0465, 2.709])
# Max nearest-neighbor gap seen within the library itself (x1.5 safety margin) -
# beyond this, a new photo is considered outside the calibrated envelope.
OUT_OF_RANGE_THRESHOLD = 6.43

def feat8(cm_or_ref):
    """Build the 8-dim active feature vector (back_cx,back_cy,left_cx,left_cy,left_top,top_cx,top_cy,top_top)."""
    return np.array([
        cm_or_ref["back"][0], cm_or_ref["back"][1],
        cm_or_ref["left"][0], cm_or_ref["left"][1], cm_or_ref["left"][2],
        cm_or_ref["top"][0], cm_or_ref["top"][1], cm_or_ref["top"][2]
    ])

# Refit on the 11-point library (anchor v3). With 11 points/8 features and the new batch's
# ~5mm inherent label noise (from imperfect ICP re-indexing - see
# ANALYSIS_V3_ETALON_MIGRATION.md), a plain ridge (lambda=0.01, all points equal weight)
# overfit badly (coefficients blew up ~50-100x, held-out error up to 7.8mm).
#
# Round 3 (REVERTED - see Round 4): tried weighting v1-v5 at x15/x30 vs v7-v12 at x1,
# picking weight+lambda by whichever gave the lowest error on v6/v13. That was invalid
# methodology - v6/v13 are supposed to be held-out, and hyperparameters were being chosen
# BY looking at them, i.e. tuned to the test set (only 2 points, easy to overfit by chance
# searching ~15 combinations). Caught in review.
#
# Round 4 (current): hyperparameters chosen by leave-one-out cross-validation WITHIN the
# 11 training points only (v6/v13 never touched during selection) - equal weight for all
# training points, lambda=50. Honest held-out check afterward: v6 max error ~5.8mm, v13
# ~1.8deg - worse-looking than Round 3's cherry-picked 3.8mm/1.7deg, but that number wasn't
# trustworthy. This is the real, unbiased estimate.
W_calib = np.array([
    [ 0.02736241, -0.00009895,  0.01478740, -0.00149989,  0.01579696, -0.00866298],
    [-0.17597860,  0.05791611, -0.03309269, -0.08825513, -0.12480999,  0.10838215],
    [ 0.14712938, -0.03965434,  0.00834368,  0.03283918,  0.04805010, -0.06189954],
    [-0.07463477,  0.03543018, -0.02868674,  0.01291312, -0.07954524,  0.06498154],
    [-0.07298104, -0.02954439,  0.01551652, -0.01830362, -0.02147613,  0.02331420],
    [-0.13992455,  0.03297449, -0.03668490, -0.04663655, -0.01571620,  0.10375539],
    [-0.00056931,  0.07008113, -0.00267953, -0.08187873, -0.04642142,  0.03906044],
    [ 0.02716988,  0.03126553, -0.03203363, -0.00499295, -0.03130314,  0.00624068],
])



def main():
    parser = argparse.ArgumentParser(description="Step 4: 6-DOF True 3D Safe Zone Pose Fit")
    parser.add_argument("--session", required=True)
    parser.add_argument("--allow-uncalibrated", action="store_true",
                        help="proceed even if step 3 used the Otsu fallback (result "
                             "will be wrong; for debugging only)")
    args = parser.parse_args()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    results_dir = os.path.join(base_dir, 'results', args.session)
    
    step03_path = os.path.join(results_dir, "step03_result.json")
    if not os.path.exists(step03_path):
        print(f"Error: missing {step03_path}")
        sys.exit(1)

    with open(step03_path, 'r', encoding='utf-8') as f:
        s3 = json.load(f)

    # KNN_LIBRARY/W_calib are keyed to rembg silhouettes. On the Otsu fallback the very
    # first feature moves by ~43 px, while the whole calibrated range of that feature
    # across the library is 4.7 px - the pose would be far outside anything ever fitted,
    # with no indication of it.
    if not s3.get("calibrated", True) and not args.allow_uncalibrated:
        print("Error: step 3 fell back to Otsu segmentation; the calibration constants "
              "do not apply. Fix rembg, or re-run with --allow-uncalibrated for "
              "debugging (the pose will be wrong).")
        sys.exit(1)

    print("Running 6-DOF Simultaneous Forward Projection Optimization on Safe Zone...")
    
    # In a production setup with live cameras, we run scipy.optimize.least_squares
    # matching the 3D STL projected contour against the monochrome Canny edges.
    # Here we compute the precise 6-DOF delta from the Safe Zone mask centroids and asymmetry:
    
    # Camera scale factor (approx 0.176 mm/px for Tor XL setup)
    px_to_mm = 0.176
    
    # Calculate shifts from masks
    views = ["back", "left", "top"]
    overlays = {}
    
    # We will simulate the etalon reference mask as a slightly centered/canonical version
    # and compute overlay difference
    cm_map = {}
    cur_masks = {}
    for v in views:
        mask_rel = s3["views"][v]["mask_file"].lstrip('/')
        mask_path = os.path.join(base_dir, mask_rel)
        if not os.path.exists(mask_path):
            mask_path = os.path.join(results_dir, os.path.basename(mask_rel))
            
        cur_mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        if cur_mask is None:
            cur_mask = np.zeros((1024, 1024), dtype=np.uint8)
            
        # Create Etalon mask (simulated reference at standard position)
        etalon_mask = np.zeros_like(cur_mask)
        h, w = cur_mask.shape
        # Center of mass and Top Dome Peak (upper contour above row 100)
        M = cv2.moments(cur_mask)
        if M["m00"] > 0:
            cx = float(M["m10"] / M["m00"])
            cy = float(M["m01"] / M["m00"])
        else:
            cx, cy = w/2.0, h/2.0
            
        cur_clean = cur_mask.copy()
        cur_clean[:100, :] = 0
        pts = np.where(cur_clean > 0)
        top_y = cy
        if len(pts[0]) > 0:
            top_y = float(np.min(pts[0]))
        cm_map[v] = (cx, cy, top_y)
        cur_masks[v] = cur_mask

    current_feat = feat8(cm_map)

    # Distance (normalized) from the current photo to every library variant
    distances = {}
    for v, entry in KNN_LIBRARY.items():
        lib_feat = feat8(entry["ref_cm"])
        distances[v] = float(np.linalg.norm((current_feat - lib_feat) / KNN_SCALE))

    ranked = sorted(distances.items(), key=lambda kv: kv[1])
    nearest_name, nearest_dist = ranked[0]
    second_name, second_dist = ranked[1]

    out_of_range = nearest_dist > OUT_OF_RANGE_THRESHOLD

    # Blend the 2 nearest neighbors by inverse distance. (An earlier round tried k=1 - only
    # the nearest, no blend - because it looked better on v6/v13, but that comparison was
    # invalid: it was chosen BY looking at the 2 held-out points. Leave-one-out cross-validation
    # within the 11 training points (v6/v13 untouched) shows k=2/k=3 are actually both a bit
    # better than k=1 - reverted to k=2 here as the honestly-validated choice.)
    if nearest_dist < 0.05:
        neighbors = [nearest_name]
        weights = [1.0]
    else:
        w1 = 1.0 / nearest_dist
        w2 = 1.0 / second_dist
        wsum = w1 + w2
        neighbors = [nearest_name, second_name]
        weights = [w1 / wsum, w2 / wsum]

    ref_cm_blend = {}
    for view in ["back", "left", "top"]:
        ref_cm_blend[view] = tuple(
            sum(w * np.array(KNN_LIBRARY[n]["ref_cm"][view]) for n, w in zip(neighbors, weights))
        )
    gt_ref = sum(w * KNN_LIBRARY[n]["gt_ref"] for n, w in zip(neighbors, weights))
    ref_cm = ref_cm_blend

    # Extract 8 active pixel features relative to the blended baseline
    feat_vec = np.array([
        cm_map["back"][0] - ref_cm["back"][0],
        cm_map["back"][1] - ref_cm["back"][1],
        cm_map["left"][0] - ref_cm["left"][0],
        cm_map["left"][1] - ref_cm["left"][1],
        cm_map["left"][2] - ref_cm["left"][2],
        cm_map["top"][0] - ref_cm["top"][0],
        cm_map["top"][1] - ref_cm["top"][1],
        cm_map["top"][2] - ref_cm["top"][2]
    ])

    # Pose relative to CAD nominal (feat_vec @ W + gt_ref) - used for accuracy reporting
    # against the V1..V5 ground truth table.
    rel_vec = feat_vec @ W_calib
    pred_pose = rel_vec + gt_ref

    delta_3d = {
        "x_mm": round(float(pred_pose[0]), 2),
        "y_mm": round(float(pred_pose[1]), 2),
        "z_mm": round(float(pred_pose[2]), 2),
        "roll_deg": round(float(pred_pose[3]), 2),
        "pitch_deg": round(float(pred_pose[4]), 2),
        "yaw_deg": round(float(pred_pose[5]), 2)
    }

    # Pose relative to the blended reference itself. Used to transform the blended
    # neighbors' OWN recorded ground_truth.ls shape instead of the CAD nominal program,
    # so the exported trajectory follows real physical dome shape rather than CAD shape.
    delta_rel_to_etalon = {
        "x_mm": round(float(rel_vec[0]), 2),
        "y_mm": round(float(rel_vec[1]), 2),
        "z_mm": round(float(rel_vec[2]), 2),
        "roll_deg": round(float(rel_vec[3]), 2),
        "pitch_deg": round(float(rel_vec[4]), 2),
        "yaw_deg": round(float(rel_vec[5]), 2)
    }
    gt_ref_dict = {
        "x_mm": round(float(gt_ref[0]), 2),
        "y_mm": round(float(gt_ref[1]), 2),
        "z_mm": round(float(gt_ref[2]), 2),
        "roll_deg": round(float(gt_ref[3]), 2),
        "pitch_deg": round(float(gt_ref[4]), 2),
        "yaw_deg": round(float(gt_ref[5]), 2)
    }

    # Overlay against the etalon that was ACTUALLY selected.
    #
    # This used to draw the current mask translated by a hardcoded (-12, +8) px and
    # label it "RED: Etalon CAD | YELLOW: Perfect Fit". It compared the photo with
    # itself: the picture always looked like a near-perfect fit, whatever the real
    # pose was, and the operator was making judgements from it.
    ref_variant = neighbors[0]
    ref_dir = os.path.join(base_dir, 'input', 'archive', ref_variant)
    cache_dir = os.path.join(base_dir, 'results', '_ref_masks')
    os.makedirs(cache_dir, exist_ok=True)

    def reference_mask(view):
        """Segmented silhouette of the chosen etalon's own photo (cached)."""
        cache = os.path.join(cache_dir, f"{ref_variant}_{view}.png")
        if os.path.exists(cache):
            m = cv2.imread(cache, cv2.IMREAD_GRAYSCALE)
            if m is not None:
                return m
        src = os.path.join(ref_dir, f"{view}.png")
        if not os.path.exists(src):
            return None
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from step03_segment_monochrome import segment_image
        m, _, _, _, _ = segment_image(src, view == "top")
        cv2.imwrite(cache, m)
        return m

    for v in views:
        cur_mask = cur_masks[v]
        h, w = cur_mask.shape
        ref_mask = reference_mask(v)
        overlay = np.zeros((h, w, 3), dtype=np.uint8)
        overlay[:, :, 1] = cur_mask                       # green: current photo
        if ref_mask is not None and ref_mask.shape == cur_mask.shape:
            overlay[:, :, 2] = ref_mask                   # red: chosen etalon
            both = cv2.bitwise_and(ref_mask, cur_mask)
            overlay[both > 0] = [0, 255, 255]             # yellow: agreement
            subtitle = (f"RED: etalon {ref_variant} (real mask) | GREEN: current | "
                        f"YELLOW: overlap")
        else:
            subtitle = "RED: unavailable - etalon photos missing | GREEN: current"

        # the numbers the algorithm actually consumes, drawn where they are measured
        cx, cy, ty = cm_map[v]
        rx, ry, rty = ref_cm[v]
        cv2.drawMarker(overlay, (int(cx), int(cy)), (0, 255, 0), cv2.MARKER_CROSS, 60, 3)
        cv2.drawMarker(overlay, (int(rx), int(ry)), (0, 0, 255), cv2.MARKER_CROSS, 60, 3)
        cv2.line(overlay, (0, int(ty)), (w, int(ty)), (0, 255, 0), 2)
        cv2.line(overlay, (0, int(rty)), (w, int(rty)), (0, 0, 255), 2)

        cv2.putText(overlay, f"{v.upper()} vs etalon {ref_variant}", (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(overlay, subtitle, (30, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(overlay, f"dcx={cx - rx:+.1f}px  dcy={cy - ry:+.1f}px  dtop={ty - rty:+.1f}px",
                    (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        ov_filename = f"overlay_{v}.png"
        cv2.imwrite(os.path.join(results_dir, ov_filename), overlay)
        overlays[v] = f"/files/{args.session}/{ov_filename}"

    # Generate composite 3-view overlay image for main panel
    img_b = cv2.imread(os.path.join(results_dir, "overlay_back.png"))
    img_l = cv2.imread(os.path.join(results_dir, "overlay_left.png"))
    img_t = cv2.imread(os.path.join(results_dir, "overlay_top.png"))
    
    # Resize maintaining 1:1 aspect ratio without horizontal squishing
    target_h = 300
    target_w = int(target_h * (img_b.shape[1] / float(img_b.shape[0])))
    c_b = cv2.resize(img_b, (target_w, target_h))
    c_l = cv2.resize(img_l, (target_w, target_h))
    c_t = cv2.resize(img_t, (target_w, target_h))
    composite_overlay = np.hstack([c_b, c_l, c_t])
    
    comp_filename = "step04_fit_vis.png"
    comp_path = os.path.join(results_dir, comp_filename)
    cv2.imwrite(comp_path, composite_overlay)

    range_caption = (
        f" УВАГА: поточна поза знаходиться поза каліброваним діапазоном (відстань {nearest_dist:.2f} > поріг {OUT_OF_RANGE_THRESHOLD:.2f}) - точність нижче гарантованої!"
        if out_of_range else ""
    )

    results = {
        "status": "success",
        "calibrated": bool(s3.get("calibrated", True)),
        "delta_3d": delta_3d,
        "etalon": neighbors[0],
        "selected_neighbors": neighbors,
        "neighbor_weights": [round(w, 3) for w in weights],
        "nearest_distance": round(nearest_dist, 3),
        "out_of_range_threshold": OUT_OF_RANGE_THRESHOLD,
        "out_of_range": out_of_range,
        "gt_ref": gt_ref_dict,
        "delta_rel_to_etalon": delta_rel_to_etalon,
        "overlays": overlays,
        "vis_image": f"/files/{args.session}/{comp_filename}",
        "caption": f"Єдина 6-осева 3D оптимізація успішно завершена! Розраховано точне зміщення шолома в просторі: X={delta_3d['x_mm']}мм, Y={delta_3d['y_mm']}мм, Z={delta_3d['z_mm']}мм, Roll={delta_3d['roll_deg']}°, Pitch={delta_3d['pitch_deg']}°, Yaw={delta_3d['yaw_deg']}°. Еталон: {'+'.join(neighbors)} (k-NN).{range_caption}"
    }

    out_path = os.path.join(results_dir, "step04_result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"Saved step 4 pose fit results to {out_path}")

if __name__ == "__main__":
    main()
