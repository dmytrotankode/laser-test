import os
import sys
import json
import numpy as np
import argparse
from logger import PipelineLogger

def get_distance(v1, v2):
    return np.linalg.norm(np.array(v1) - np.array(v2))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', type=str, required=True)
    args = parser.parse_args()
    
    session_id = args.session
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    session_dir = os.path.join(base_dir, 'results', session_id)
    
    logger = PipelineLogger(session_id, base_dir, "STEP 12: ANALYZE RESULTS & SELECT")
    
    f9 = os.path.join(session_dir, 'step08_current_pose_fit.json')
    f10 = os.path.join(session_dir, 'step09b_current_pose_fit.json')
    f11 = os.path.join(session_dir, 'step09c_current_pose_fit.json')
    f11b = os.path.join(session_dir, 'step09d_ai_reconstruct_fit.json')
    
    results = {}
    metrics = {}
    
    for key, path in [('mask', f9), ('texture', f10), ('contour', f11), ('ai', f11b)]:
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                results[key] = data
                metrics[key] = np.array([
                    data['metrics']['shift_horizontal_mm'],
                    data['metrics']['shift_depth_mm'],
                    data['metrics']['shift_vertical_mm'],
                    data['metrics']['tilt_pitch_deg'],
                    data['metrics']['tilt_roll_deg'],
                    data['metrics']['tilt_yaw_deg']
                ])
                
    if not results:
        logger.log("Error: No pose fit results found!")
        sys.exit(1)
        
    logger.log(f"Loaded {len(results)} calculation results.")
    for k, v in metrics.items():
        logger.log(f"  {k}: {np.round(v, 2)}")
        
    final_data = None
    chosen_method = ""
    
    # Pairwise comparison between all loaded methods to find the closest pair
    keys = list(metrics.keys())
    if len(keys) >= 2:
        distances = {}
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                k1, k2 = keys[i], keys[j]
                dist = get_distance(metrics[k1], metrics[k2])
                distances[(k1, k2)] = dist
                logger.log(f"Distance {k1} <-> {k2}: {dist:.2f}")
        
        best_pair = min(distances, key=distances.get)
        min_dist = distances[best_pair]
        
        k1, k2 = best_pair
        logger.log(f"Methods '{k1}' and '{k2}' agree the most (diff={min_dist:.2f}). Averaging them for final output.")
        
        t1 = np.array(results[k1]['delta_translation'])
        t2 = np.array(results[k2]['delta_translation'])
        avg_t = (t1 + t2) / 2.0
        
        r1 = np.array(results[k1]['delta_rotvec'])
        r2 = np.array(results[k2]['delta_rotvec'])
        avg_r = (r1 + r2) / 2.0
        
        def _metric_vec(d):
            return np.array([
                d['metrics']['shift_horizontal_mm'],
                d['metrics']['shift_depth_mm'],
                d['metrics']['shift_vertical_mm'],
                d['metrics']['tilt_pitch_deg'],
                d['metrics']['tilt_roll_deg'],
                d['metrics']['tilt_yaw_deg']
            ])
        m1 = _metric_vec(results[k1])
        m2 = _metric_vec(results[k2])
        avg_m = (m1 + m2) / 2.0
        
        method_names_map = {
            'mask': 'Mask',
            'texture': 'Texture',
            'contour': 'Contour',
            'ai': 'AI 3D Reconstruction'
        }
        
        final_data = {
            'delta_translation': avg_t.tolist(),
            'delta_rotvec': avg_r.tolist(),
            'metrics': {
                'shift_horizontal_mm': round(float(avg_m[0]), 2),
                'shift_depth_mm': round(float(avg_m[1]), 2),
                'shift_vertical_mm': round(float(avg_m[2]), 2),
                'tilt_pitch_deg': round(float(avg_m[3]), 2),
                'tilt_roll_deg': round(float(avg_m[4]), 2),
                'tilt_yaw_deg': round(float(avg_m[5]), 2)
            },
            'chosen_method': f"Averaged {method_names_map[k1]} and {method_names_map[k2]}",
            'reasoning': f"Методи «{method_names_map[k1]}» та «{method_names_map[k2]}» узгоджуються найкраще (відхилення {min_dist:.2f} мм/°). Результати між ними було усереднено."
        }
    else:
        # Fallback if only 1 method loaded
        k_single = keys[0]
        final_data = results[k_single]
        final_data['chosen_method'] = k_single.upper()
        final_data['reasoning'] = f"Завантажено лише один метод: {k_single.upper()}."
        
    logger.log(f"FINAL CHOSEN METHOD: {final_data['chosen_method']}")
    
    out_file = os.path.join(session_dir, 'step10_final_pose.json')
    with open(out_file, 'w') as f:
        json.dump(final_data, f, indent=4)
        
    logger.log(f"Saved final pose to {out_file}")

if __name__ == '__main__':
    main()
