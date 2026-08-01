import os
import sys
import json
import argparse
import numpy as np
import re
import cv2

def load_ls_file(path):
    points = []
    if not os.path.exists(path):
        raise FileNotFoundError(f"LS file not found: {path}")
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    point_pattern = re.compile(
        r'P\[(\d+)\]\{\s*GP1:\s*UF\s*:\s*(\d+),\s*UT\s*:\s*(\d+).*?X\s*=\s*([-\d.]+).*?Y\s*=\s*([-\d.]+).*?Z\s*=\s*([-\d.]+).*?W\s*=\s*([-\d.]+).*?P\s*=\s*([-\d.]+).*?R\s*=\s*([-\d.]+)',
        re.DOTALL | re.IGNORECASE
    )
    for match in point_pattern.findall(content):
        points.append({
            'id': int(match[0]),
            'x': float(match[3]),
            'y': float(match[4]),
            'z': float(match[5])
        })
    return points

def main():
    parser = argparse.ArgumentParser(description="Step 2: Align Etalon LS & Contact Points")
    parser.add_argument("--session", required=True)
    args = parser.parse_args()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    results_dir = os.path.join(base_dir, 'results', args.session)
    os.makedirs(results_dir, exist_ok=True)

    ls_path = os.path.join(base_dir, 'input', 'ls_file', 'TORXL_NEW_PROG.LS')
    if not os.path.exists(ls_path):
        print(f"Error: missing {ls_path}")
        sys.exit(1)

    print("Loading Etalon LS file...")
    points = load_ls_file(ls_path)
    print(f"Loaded {len(points)} points.")

    # tx/ty/tz is the pivot the pose delta is rotated about. It is NOT the output of an
    # ICP alignment - no ICP has ever run in this project, and the CAD mesh is in its own
    # coordinate frame with no registration to machine coordinates (see step 1).
    #
    # Its provenance is unknown. It is close to the CAD contour centroid in X and Y
    # (2.2 mm, 0.9 mm) but 21 mm above it in Z, and matches no obvious quantity of the
    # mesh or the programme. Do not "fix" it casually:
    #   * it does NOT affect the exported geometry - the same pivot is used when labels
    #     are extracted and when the rotation is applied, so the composition is exact for
    #     any choice;
    #   * it DOES affect model quality - a pivot far from the object couples rotation
    #     into translation, which makes the linear regression's job harder. Re-deriving
    #     it belongs with the refit (PLAN.md stage 4), together with the labels.
    #
    # rx/ry/rz are written to the result for backwards compatibility and read by nothing.
    tx, ty, tz = 1170.98, 785.15, -191.86
    rx, ry, rz = 181.89, -2.72, 90.53

    # Draw diagnostic visualization of the Etalon laser trajectory in 2D projections
    vis_img = np.full((500, 800, 3), 40, dtype=np.uint8)
    cv2.putText(vis_img, "Etalon Laser Trajectory (Top & Side Projections)", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    if len(points) > 0:
        pts_arr = np.array([[p['x'], p['y'], p['z']] for p in points])
        # Normalize to draw on image
        min_p = pts_arr.min(axis=0)
        max_p = pts_arr.max(axis=0)
        scale = 200.0 / max(max_p[0]-min_p[0], max_p[1]-min_p[1], 1.0)
        
        # Draw top view (XY) on left half
        cv2.putText(vis_img, "Top Projection (XY)", (80, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        for i in range(len(pts_arr)-1):
            pt1 = (int(200 + (pts_arr[i][0]-min_p[0])*scale - 100), int(280 + (pts_arr[i][1]-min_p[1])*scale - 100))
            pt2 = (int(200 + (pts_arr[i+1][0]-min_p[0])*scale - 100), int(280 + (pts_arr[i+1][1]-min_p[1])*scale - 100))
            cv2.line(vis_img, pt1, pt2, (0, 0, 255), 2)
            
        # Draw side view (XZ) on right half
        cv2.putText(vis_img, "Side Projection (XZ)", (480, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        for i in range(len(pts_arr)-1):
            pt1 = (int(600 + (pts_arr[i][0]-min_p[0])*scale - 100), int(350 - (pts_arr[i][2]-min_p[2])*scale))
            pt2 = (int(600 + (pts_arr[i+1][0]-min_p[0])*scale - 100), int(350 - (pts_arr[i+1][2]-min_p[2])*scale))
            cv2.line(vis_img, pt1, pt2, (0, 255, 0), 2)

    cv2.putText(vis_img, f"Total Points: {len(points)} | pivot ({tx:.1f}, {ty:.1f}, {tz:.1f})",
                (180, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    vis_filename = "step02_trim_line.png"
    vis_path = os.path.join(results_dir, vis_filename)
    cv2.imwrite(vis_path, vis_img)

    results = {
        "status": "success",
        "ls_path": "/input/ls_file/TORXL_NEW_PROG.LS",
        "num_points": len(points),
        "tx": tx, "ty": ty, "tz": tz,
        "rx": rx, "ry": ry, "rz": rz,
        "original_points": points,
        "vis_image": f"/files/{args.session}/{vis_filename}",
        "pivot_source": "hardcoded constant of unknown provenance - see comment in step02",
        "icp_performed": False,
        "caption": f"Завантажено CAD-програму лазера ({len(points)} точок). Точка повороту (pivot) для 6-осевої корекції: ({tx}, {ty}, {tz}) — це зашита константа, а НЕ результат ICP: ICP у цьому проєкті ніколи не виконувався, а CAD-меш узагалі не прив'язаний до координат верстата. На геометрію експорту вибір цієї точки не впливає (та сама точка використовується і при витягуванні, і при застосуванні повороту), але впливає на якість регресії — переоцінка запланована разом з перенавчанням моделі."
    }

    out_path = os.path.join(results_dir, "step02_result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"Saved step 2 alignment results to {out_path}")

if __name__ == "__main__":
    main()
