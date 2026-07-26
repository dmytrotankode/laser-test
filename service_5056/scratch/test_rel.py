import json
import os

runs = {'v1': 'test_eval_v1', 'v2': 'test_eval_v2', 'v3': 'test_eval_v3', 'v4': 'test_eval_v4', 'v5': 'test_eval_v5'}
gt_v1 = json.load(open(f'results/{runs["v1"]}/step05_result.json'))['gt_delta_3d']

print("=== RELATIVE SHIFT FROM V1 BASELINE (ACTUAL MOVEMENT ON TABLE) ===")
for v, r in runs.items():
    s4 = json.load(open(f'results/{r}/step04_result.json'))
    s5 = json.load(open(f'results/{r}/step05_result.json'))
    calc = s4['delta_3d']
    gt = s5['gt_delta_3d']
    
    gt_rel = {k: round(gt[k] - gt_v1[k], 2) for k in ['x_mm', 'y_mm', 'z_mm', 'roll_deg', 'pitch_deg', 'yaw_deg']}
    err = {k: round(calc[k] - gt_rel[k], 2) for k in calc}
    
    print(f"\n--- {v.upper()} ---")
    print(f"  Vision Calc (vs v1)  : {calc}")
    print(f"  Actual CNC Move (GT) : {gt_rel}")
    print(f"  Vision Error         : {err}")
