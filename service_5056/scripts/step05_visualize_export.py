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

    d = s4["delta_3d"]
    q_delta = R.from_euler('ZYX', [d['yaw_deg'], d['pitch_deg'], d['roll_deg']], degrees=True)
    center = np.array([s2['tx'], s2['ty'], s2['tz']])
    trans = np.array([d['x_mm'], d['y_mm'], d['z_mm']])

    out_ls_file = "current_helmet.ls"
    out_ls_path = os.path.join(results_dir, out_ls_file)

    # Read original LS file and apply transformation
    orig_ls_path = os.path.join(base_dir, 'input', 'ls_file', 'TORXL_NEW_PROG.LS')
    if os.path.exists(orig_ls_path):
        with open(orig_ls_path, 'r', encoding='utf-8', errors='ignore') as f:
            ls_content = f.read()

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

        pattern = re.compile(r'(P\[\d+\]\{.*?X\s*=\s*)([-\d.]+)(.*?Y\s*=\s*)([-\d.]+)(.*?Z\s*=\s*)([-\d.]+)', re.DOTALL | re.IGNORECASE)
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

    results = {
        "status": "success",
        "step02_data": s2,
        "delta_3d": d,
        "gt_delta_3d": gt_delta_3d,
        "current_ls_file": out_ls_file,
        "current_ls_path": f"/files/{args.session}/{out_ls_file}",
        "ground_truth_points": ground_truth_points,
        "variant": variant,
        "caption": f"3D-візуалізація готова! Еталонний шолом (червоний) та Поточний шолом (зелений) відображаються у 3D-сцені. Біла лінія показує розраховану нами траєкторію лазера (current_helmet.ls). {'Жовта лінія та Жовтий шолом показують фактичне положення з верстата (Ground Truth для порівняння).' if ground_truth_points else ''}"
    }

    out_path = os.path.join(results_dir, "step05_result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"Saved step 5 visualization & export results to {out_path}")

if __name__ == "__main__":
    main()
