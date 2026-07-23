import sys
import os
import json
import argparse

def main():
    parser = argparse.ArgumentParser(description='Step 8: Visualize 3D Offset')
    parser.add_argument('--session', required=True)
    args = parser.parse_args()
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    results_dir = os.path.join(base_dir, 'results', args.session)
    
    step02_file = os.path.join(results_dir, 'step02_result.json')
    step07_file = os.path.join(results_dir, 'step07_result.json')
    
    if not os.path.exists(step02_file):
        print("Error: Missing step02_result.json")
        sys.exit(1)
        
    if not os.path.exists(step07_file):
        print("Error: Missing step07_result.json")
        sys.exit(1)
        
    with open(step02_file, 'r', encoding='utf-8') as f:
        s2 = json.load(f)
        
    with open(step07_file, 'r', encoding='utf-8') as f:
        s7 = json.load(f)
        
    results = {
        "step02_data": s2,
        "delta_3d": s7.get("delta_3d", {
            "x_mm": 0, "y_mm": 0, "z_mm": 0,
            "roll_deg": 0, "pitch_deg": 0, "yaw_deg": 0
        })
    }
    
    # Generate current_helmet.ls
    import re
    import numpy as np
    from scipy.spatial.transform import Rotation as R
    
    out_ls_file = "current_helmet.ls"
    out_ls_path = os.path.join(results_dir, out_ls_file)
    results["current_ls_file"] = out_ls_file
    results["current_ls_path"] = f"/files/{args.session}/{out_ls_file}"
    
    # Try to find original ls file from step01
    step01_file = os.path.join(results_dir, 'step01_result.json')
    if os.path.exists(step01_file):
        with open(step01_file, 'r', encoding='utf-8') as f:
            s1 = json.load(f)
            
        orig_ls_path = s1.get('ls_path')
        if orig_ls_path:
            # Reconstruct absolute path
            abs_ls_path = os.path.join(base_dir, orig_ls_path.lstrip('/'))
            # If path changed due to /files/, use local results dir
            if not os.path.exists(abs_ls_path):
                abs_ls_path = os.path.join(results_dir, os.path.basename(orig_ls_path))
                
            if os.path.exists(abs_ls_path):
                with open(abs_ls_path, 'r', encoding='utf-8') as f:
                    ls_content = f.read()
                    
                # delta params
                d = results["delta_3d"]
                q_delta = R.from_euler('ZYX', [d['yaw_deg'], d['pitch_deg'], d['roll_deg']], degrees=True)
                center = np.array([s2['tx'], s2['ty'], s2['tz']])
                trans = np.array([d['x_mm'], d['y_mm'], d['z_mm']])
                
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
                    
    out_file = os.path.join(results_dir, 'step08_result.json')
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)
        
    print(f"Saved step 8 results to {out_file}")

if __name__ == '__main__':
    main()
