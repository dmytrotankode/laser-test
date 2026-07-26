import os
import json
import shutil
import subprocess
import numpy as np
from scipy.spatial.transform import Rotation as R

variants = ['v1', 'v2', 'v3', 'v4', 'v5']
results_summary = {}

ref_step02 = os.path.join("results", "run_20260726_202818", "step02_result.json")

for v in variants:
    print(f"=== Running Pipeline for Variant {v} ===")
    sess = f"test_eval_{v}"
    res_dir = os.path.join("results", sess)
    os.makedirs(res_dir, exist_ok=True)
    
    # Copy step02_result.json
    if os.path.exists(ref_step02):
        shutil.copy(ref_step02, os.path.join(res_dir, "step02_result.json"))
    
    # Write config.json for variant selection
    with open(os.path.join(res_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump({"variant": v}, f)
    
    # Run Step 3
    cmd3 = f"python scripts/step03_segment_monochrome.py --session {sess}"
    subprocess.run(cmd3, shell=True, check=True)
    
    # Run Step 4
    cmd4 = f"python scripts/step04_fit_3d_pose.py --session {sess}"
    subprocess.run(cmd4, shell=True, check=True)
    
    # Run Step 5
    cmd5 = f"python scripts/step05_visualize_export.py --session {sess}"
    subprocess.run(cmd5, shell=True, check=True)
    
    # Load Step 2, Step 4 and Step 5 results
    s2 = json.load(open(os.path.join(res_dir, "step02_result.json")))
    s4 = json.load(open(os.path.join(res_dir, "step04_result.json")))
    s5 = json.load(open(os.path.join(res_dir, "step05_result.json")))
    
    calc_d = s4["delta_3d"]
    gt_d = s5.get("gt_delta_3d", {})
    
    # Compute calc_pts by transforming s2["original_points"]
    orig_pts = np.array([[p["x"], p["y"], p["z"]] for p in s2["original_points"]])
    center = np.array([s2["tx"], s2["ty"], s2["tz"]])
    trans = np.array([calc_d["x_mm"], calc_d["y_mm"], calc_d["z_mm"]])
    q_delta = R.from_euler('ZYX', [calc_d['yaw_deg'], calc_d['pitch_deg'], calc_d['roll_deg']], degrees=True)
    
    calc_pts = q_delta.apply(orig_pts - center) + center + trans
    gt_pts = np.array([[p["x"], p["y"], p["z"]] for p in s5["ground_truth_points"]]) if "ground_truth_points" in s5 and s5["ground_truth_points"] else []
    
    if len(gt_pts) > 0:
        min_len = min(len(calc_pts), len(gt_pts))
        c_slice = calc_pts[:min_len]
        g_slice = gt_pts[:min_len]
        
        diffs = np.linalg.norm(c_slice - g_slice, axis=1)
        mean_err = float(np.mean(diffs))
        max_err = float(np.max(diffs))
        median_err = float(np.median(diffs))
    else:
        mean_err = 0.0
        max_err = 0.0
        median_err = 0.0
    
    # Difference between calc_d and gt_d
    x_diff = round(calc_d["x_mm"] - gt_d.get("x_mm", 0), 2) if gt_d else 0.0
    y_diff = round(calc_d["y_mm"] - gt_d.get("y_mm", 0), 2) if gt_d else 0.0
    z_diff = round(calc_d["z_mm"] - gt_d.get("z_mm", 0), 2) if gt_d else 0.0
    roll_diff = round(calc_d["roll_deg"] - gt_d.get("roll_deg", 0), 2) if gt_d else 0.0
    pitch_diff = round(calc_d["pitch_deg"] - gt_d.get("pitch_deg", 0), 2) if gt_d else 0.0
    yaw_diff = round(calc_d["yaw_deg"] - gt_d.get("yaw_deg", 0), 2) if gt_d else 0.0
    
    results_summary[v] = {
        "calc": calc_d,
        "gt": gt_d,
        "diff": {"x": x_diff, "y": y_diff, "z": z_diff, "roll": roll_diff, "pitch": pitch_diff, "yaw": yaw_diff} if gt_d else "N/A (Reference position)",
        "ls_error_mm": {"mean": round(mean_err, 2), "median": round(median_err, 2), "max": round(max_err, 2)} if len(gt_pts) > 0 else "N/A"
    }

print("\n" + "="*80)
print("FINAL DEEP ANALYSIS SUMMARY ACROSS ALL VARIANTS:")
print("="*80)
for v, r in results_summary.items():
    print(f"\n--- VARIANT {v.upper()} ---")
    print(f"  Calculated Shift (White) : {r['calc']}")
    print(f"  Ground Truth Shift (Yel) : {r['gt']}")
    print(f"  Pose Discrepancy (Δ)     : {r['diff']}")
    print(f"  LS 3D Line Error         : {r['ls_error_mm']}")
