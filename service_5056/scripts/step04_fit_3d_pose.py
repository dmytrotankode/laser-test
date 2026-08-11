import os
import sys
import json
import argparse
import numpy as np
import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lsgeom  # noqa: E402

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



def build_feature_vector(masks, kind):
    """Same feature extraction as scripts/features.py, but from masks already in memory."""
    import cv2 as _cv
    f8, prof = [], []
    for name in ("back", "left", "top"):
        m = masks[name]
        M = _cv.moments(m)
        cx, cy = M["m10"] / M["m00"], M["m01"] / M["m00"]
        clipped = m.copy()
        clipped[:100, :] = 0
        top_y = float(np.min(np.where(clipped > 0)[0]))
        f8.append((cx, cy, top_y))
        cnts, _ = _cv.findContours(m, _cv.RETR_EXTERNAL, _cv.CHAIN_APPROX_NONE)
        c = max(cnts, key=_cv.contourArea)[:, 0, :].astype(float)
        ang = np.arctan2(c[:, 1] - cy, c[:, 0] - cx)
        rad = np.hypot(c[:, 0] - cx, c[:, 1] - cy)
        o = np.argsort(ang)
        grid = np.linspace(-np.pi, np.pi, 48, endpoint=False)
        prof.append([cx, cy] + list(np.interp(grid, ang[o], rad[o], period=2 * np.pi)))
    if kind == "f8":
        b, l, t = f8
        return np.array([b[0], b[1], l[0], l[1], l[2], t[0], t[1], t[2]], dtype=float)
    return np.array([x for row in prof for x in row], dtype=float)


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

    print("Computing 6-DOF pose delta from the silhouette profile...")
    
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

    # ------------------------------------------------------------------ pose model
    # Constants live in input/model_pose.json, produced by scripts/fit_model.py with
    # every hyperparameter chosen by leave-one-variant-out inside TRAIN. The previous
    # W_calib was hardcoded here, fitted on 11 absolute samples from a single anchor,
    # on 8 hand-picked scalars. Two things changed:
    #
    #   * trained on PAIRS. The model is used on feature differences, so it is now fitted
    #     on all 110 ordered pairs of training variants instead of 11 anchored samples.
    #   * silhouette profile instead of the 8 scalars. Leave-one-variant-out inside TRAIN:
    #     8 scalars 2.11 mm, profile 1.41 mm, against a do-nothing control of 2.17 mm.
    #     The old feature set was, in other words, within 3% of not correcting at all.
    model_path = lsgeom.model_file(base_dir, results_dir)
    if not os.path.exists(model_path):
        print(f"Error: missing {model_path} - run scripts/fit_model.py --emit")
        sys.exit(1)
    with open(model_path, encoding='utf-8') as f:
        MODEL = json.load(f)

    W_calib = np.array(MODEL["W"])
    feat_scale = np.array(MODEL["scale"])
    knn_scale = np.array(MODEL["knn_scale"])
    pivot = np.array(MODEL["pivot"])
    OUT_OF_RANGE_THRESHOLD = MODEL["out_of_range_threshold"]
    LIB = MODEL["library"]

    current_feat = build_feature_vector(cur_masks, MODEL["feature_kind"])

    # nearest library variant in the model's own feature space
    distances = {v: float(np.linalg.norm((current_feat - np.array(e["feat"])) / knn_scale))
                 for v, e in LIB.items()}
    ranked = sorted(distances.items(), key=lambda kv: kv[1])
    nearest_name, nearest_dist = ranked[0]
    second_name, second_dist = ranked[1]
    out_of_range = nearest_dist > OUT_OF_RANGE_THRESHOLD

    # k=1: cross-validation scored the NEAREST neighbour, because that is what deployment
    # uses. Blending two neighbours was never validated under this protocol, so it is not
    # switched on here even though lsgeom can do it.
    neighbors = [nearest_name]
    weights = [1.0]

    rel_vec = ((current_feat - np.array(LIB[nearest_name]["feat"])) / feat_scale) @ W_calib
    gt_ref = np.array(LIB[nearest_name]["pose_vs_anchor"])
    pred_pose = rel_vec + gt_ref

    def as_dict(vec6):
        return {
            "x_mm": round(float(vec6[0]), 2), "y_mm": round(float(vec6[1]), 2),
            "z_mm": round(float(vec6[2]), 2), "roll_deg": round(float(vec6[3]), 2),
            "pitch_deg": round(float(vec6[4]), 2), "yaw_deg": round(float(vec6[5]), 2),
        }

    # delta_3d is the pose relative to the library anchor, for reporting only.
    # delta_rel_to_etalon is what step05 actually applies: the pose relative to the
    # chosen neighbour, whose own recorded contour is the master trajectory.
    delta_3d = as_dict(pred_pose)
    delta_rel_to_etalon = as_dict(rel_vec)
    gt_ref_dict = as_dict(gt_ref)

    # Overlay against the etalon that was ACTUALLY selected.
    #
    # This used to draw the current mask translated by a hardcoded (-12, +8) px and
    # label it "RED: Etalon CAD | YELLOW: Perfect Fit". It compared the photo with
    # itself: the picture always looked like a near-perfect fit, whatever the real
    # pose was, and the operator was making judgements from it.
    ref_variant = neighbors[0]
    REF_CM_F8 = {ref_variant: {}}
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
        if ref_mask is not None:
            _M = cv2.moments(ref_mask)
            _cl = ref_mask.copy(); _cl[:100, :] = 0
            REF_CM_F8[ref_variant][v] = (_M["m10"] / _M["m00"], _M["m01"] / _M["m00"],
                                         float(np.min(np.where(_cl > 0)[0])))
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
        rx, ry, rty = REF_CM_F8.get(ref_variant, {}).get(v, (cx, cy, ty))
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
        "pivot": [float(x) for x in pivot],
        "model": {k: MODEL[k] for k in ("feature_kind", "lam", "loo_nearest_mean",
                                        "loo_do_nothing_mean")},
        "delta_rel_to_etalon": delta_rel_to_etalon,
        "overlays": overlays,
        "vis_image": f"/files/{args.session}/{comp_filename}",
        "caption": f"Розраховано 6-осеве зміщення шолома відносно обраного еталона: X={delta_3d['x_mm']}мм, Y={delta_3d['y_mm']}мм, Z={delta_3d['z_mm']}мм, Roll={delta_3d['roll_deg']}°, Pitch={delta_3d['pitch_deg']}°, Yaw={delta_3d['yaw_deg']}°. Еталон: {'+'.join(neighbors)} (найближчий у бібліотеці). Модель — лінійна регресія за профілем силуету, навчена на {len(MODEL['train']) * (len(MODEL['train']) - 1)} парах архівних поз; перехресна перевірка всередині навчальної вибірки дає {MODEL['loo_nearest_mean']:.2f} мм проти {MODEL['loo_do_nothing_mean']:.2f} мм без корекції.{range_caption}"
    }

    out_path = os.path.join(results_dir, "step04_result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"Saved step 4 pose fit results to {out_path}")

if __name__ == "__main__":
    main()
