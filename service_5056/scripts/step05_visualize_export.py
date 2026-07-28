import os
import sys
import json
import argparse
import numpy as np
import re
from scipy.spatial.transform import Rotation as R

def main():
    parser = argparse.ArgumentParser(description="Step 5: 3D Visualize & Export Final LS")
    parser.add_argument("--session", required=True)
    args = parser.parse_args()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    results_dir = os.path.join(base_dir, 'results', args.session)
    
    step02_file = os.path.join(results_dir, "step02_result.json")
    step04_file = os.path.join(results_dir, "step04_result.json")

    if not os.path.exists(step02_file) or not os.path.exists(step04_file):
        print("Error: missing previous step results")
        sys.exit(1)

    with open(step02_file, 'r', encoding='utf-8') as f:
        s2 = json.load(f)
    with open(step04_file, 'r', encoding='utf-8') as f:
        s4 = json.load(f)

    print("Generating 3D Visualization Data and exporting current_helmet.ls...")

    center = np.array([s2['tx'], s2['ty'], s2['tz']])

    def load_ls_points_xyz(path):
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        pattern_xyz = re.compile(r'P\[\d+\]\{.*?X\s*=\s*([-\d.]+).*?Y\s*=\s*([-\d.]+).*?Z\s*=\s*([-\d.]+)', re.DOTALL | re.IGNORECASE)
        return [(float(a), float(b), float(c)) for a, b, c in pattern_xyz.findall(content)]

    # Variant 1 (k-NN dynamic etalon): step04 picks the 1-2 archive variants closest in
    # pixel-feature space to the current photo (s4["selected_neighbors"]/["neighbor_weights"]).
    # If those are real physical archive variants (not the CAD baseline), export is built by
    # rotating a WEIGHTED BLEND of their own recorded ground_truth.ls points (real physical
    # dome shape) instead of the theoretical CAD program. The transform applied is the pose
    # delta relative to the blended reference (delta_rel_to_etalon), and the rotation pivot
    # is recentered by the blended CAD-relative offset (gt_ref), since gt_ref was itself
    # derived by rotating the CAD points about `center`.
    etalon = s4.get("etalon", "v1")
    neighbors = s4.get("selected_neighbors", [etalon])
    neighbor_weights = s4.get("neighbor_weights", [1.0])
    neighbor_paths = [os.path.join(base_dir, 'input', 'archive', n, 'ground_truth.ls') for n in neighbors]

    blended_points = None
    if all(os.path.exists(p) for p in neighbor_paths):
        orig_ls_path = neighbor_paths[0]
        d = s4["delta_rel_to_etalon"]
        gt_ref = s4["gt_ref"]
        center = center + np.array([gt_ref['x_mm'], gt_ref['y_mm'], gt_ref['z_mm']])

        neighbor_point_lists = [load_ls_points_xyz(p) for p in neighbor_paths]
        n_pts = min(len(pl) for pl in neighbor_point_lists)
        blended_points = []
        for i in range(n_pts):
            acc = np.zeros(3)
            for pl, w in zip(neighbor_point_lists, neighbor_weights):
                acc += w * np.array(pl[i])
            blended_points.append(acc)
        print(f"Using blended ground_truth.ls from {neighbors} (weights {neighbor_weights}) as master trajectory.")
    else:
        orig_ls_path = os.path.join(base_dir, 'input', 'ls_file', 'TORXL_NEW_PROG.LS')
        d = s4["delta_3d"]

    q_delta = R.from_euler('ZYX', [d['yaw_deg'], d['pitch_deg'], d['roll_deg']], degrees=True)
    trans = np.array([d['x_mm'], d['y_mm'], d['z_mm']])

    out_ls_file = "current_helmet.ls"
    out_ls_path = os.path.join(results_dir, out_ls_file)

    # Read master LS file and apply transformation
    if os.path.exists(orig_ls_path):
        with open(orig_ls_path, 'r', encoding='utf-8', errors='ignore') as f:
            ls_content = f.read()

        pattern = re.compile(r'(P\[\d+\]\{.*?X\s*=\s*)([-\d.]+)(.*?Y\s*=\s*)([-\d.]+)(.*?Z\s*=\s*)([-\d.]+)', re.DOTALL | re.IGNORECASE)

        if blended_points is not None:
            point_iter = iter(blended_points)

            def replace_point(match):
                g1, g3, g5 = match.group(1), match.group(3), match.group(5)
                pt = np.array(next(point_iter))
                pt_rel = pt - center
                pt_rot = q_delta.apply(pt_rel)
                pt_final = pt_rot + center + trans
                return f"{g1}{pt_final[0]:.3f}{g3}{pt_final[1]:.3f}{g5}{pt_final[2]:.3f}"
        else:
            def replace_point(match):
                g1 = match.group(1)
                x = float(match.group(2))
                g3 = match.group(3)
                y = float(match.group(4))
                g5 = match.group(5)
                z = float(match.group(6))

                pt = np.array([x, y, z])
                pt_rel = pt - center
                pt_rot = q_delta.apply(pt_rel)
                pt_final = pt_rot + center + trans

                return f"{g1}{pt_final[0]:.3f}{g3}{pt_final[1]:.3f}{g5}{pt_final[2]:.3f}"

        new_ls_content = pattern.sub(replace_point, ls_content)

        with open(out_ls_path, 'w', encoding='utf-8') as f:
            f.write(new_ls_content)
        print(f"Exported transformed LS file to {out_ls_path}")

    cfg_path = os.path.join(results_dir, "config.json")
    variant = "default"
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                variant = json.load(f).get("variant", "default")
        except Exception:
            pass

    ground_truth_points = []
    if variant != "default":
        gt_ls_path = os.path.join(base_dir, 'input', 'archive', variant, 'ground_truth.ls')
        if os.path.exists(gt_ls_path):
            with open(gt_ls_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            pattern_gt = re.compile(r'P\[\d+\]\{.*?X\s*=\s*([-\d.]+).*?Y\s*=\s*([-\d.]+).*?Z\s*=\s*([-\d.]+)', re.DOTALL | re.IGNORECASE)
            for match in pattern_gt.finditer(content):
                ground_truth_points.append({
                    "x": float(match.group(1)),
                    "y": float(match.group(2)),
                    "z": float(match.group(3))
                })
            print(f"Loaded {len(ground_truth_points)} ground truth points from {gt_ls_path}")

    gt_delta_3d = None
    if ground_truth_points and "original_points" in s2 and len(s2["original_points"]) > 0:
        try:
            orig_pts = np.array([[p['x'], p['y'], p['z']] for p in s2["original_points"]])
            gt_pts = np.array([[p['x'], p['y'], p['z']] for p in ground_truth_points])
            n = min(len(orig_pts), len(gt_pts))
            orig_pts = orig_pts[:n]
            gt_pts = gt_pts[:n]

            c_orig = orig_pts.mean(axis=0)
            c_gt = gt_pts.mean(axis=0)
            H = (orig_pts - c_orig).T @ (gt_pts - c_gt)
            U, S, Vt = np.linalg.svd(H)
            rot = Vt.T @ U.T
            if np.linalg.det(rot) < 0:
                Vt[2,:] *= -1
                rot = Vt.T @ U.T
            trans = c_gt - rot @ c_orig

            center_orig = np.array([s2.get('tx', 1170.98), s2.get('ty', 785.15), s2.get('tz', -191.86)])
            center_gt = rot @ center_orig + trans
            shift = center_gt - center_orig
            euler_diff = R.from_matrix(rot).as_euler('zyx', degrees=True)

            gt_delta_3d = {
                "x_mm": round(float(shift[0]), 2),
                "y_mm": round(float(shift[1]), 2),
                "z_mm": round(float(shift[2]), 2),
                "roll_deg": round(float(euler_diff[2]), 2),
                "pitch_deg": round(float(euler_diff[1]), 2),
                "yaw_deg": round(float(euler_diff[0]), 2)
            }
            print(f"Calculated Ground Truth helmet pose shift: {gt_delta_3d}")
        except Exception as e:
            print("Error computing gt_delta_3d:", e)

    nearest_distance = s4.get("nearest_distance")
    out_of_range = s4.get("out_of_range", False)
    out_of_range_threshold = s4.get("out_of_range_threshold")

    etalon_parts = [f"{n} ({w*100:.0f}%)" for n, w in zip(neighbors, neighbor_weights)]
    etalon_summary = (
        f"Еталон обрано динамічно (k-NN): {' + '.join(etalon_parts)} "
        f"(відстань до найближчого={nearest_distance})."
    )
    range_warning = (
        f" ⚠️ УВАГА: поза поза каліброваним діапазоном (відстань {nearest_distance} > поріг {out_of_range_threshold}) - точність нижче гарантованої!"
        if out_of_range else ""
    )

    results = {
        "status": "success",
        "step02_data": s2,
        "delta_3d": d,
        "gt_delta_3d": gt_delta_3d,
        "current_ls_file": out_ls_file,
        "current_ls_path": f"/files/{args.session}/{out_ls_file}",
        "ground_truth_points": ground_truth_points,
        "variant": variant,
        "etalon_neighbors": neighbors,
        "etalon_weights": neighbor_weights,
        "out_of_range": out_of_range,
        "caption": f"3D-візуалізація готова! Еталонний шолом (червоний) та Поточний шолом (зелений) відображаються у 3D-сцені. Біла лінія показує розраховану нами траєкторію лазера (current_helmet.ls), побудовану обертанням реальної форми обраного еталона. {etalon_summary}{range_warning} {'Жовта лінія та Жовтий шолом показують фактичне положення з верстата (Ground Truth для порівняння).' if ground_truth_points else ''}"
    }

    out_path = os.path.join(results_dir, "step05_result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"Saved step 5 visualization & export results to {out_path}")

if __name__ == "__main__":
    main()
