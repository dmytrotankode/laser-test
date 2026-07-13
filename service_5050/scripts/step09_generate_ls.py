import os
import sys
import json
import numpy as np
import re
import argparse
from logger import PipelineLogger

def get_rotation_matrix(rx, ry, rz):
    rx, ry, rz = np.radians(rx), np.radians(ry), np.radians(rz)
    Rx = np.array([[1, 0, 0], [0, np.cos(rx), -np.sin(rx)], [0, np.sin(rx), np.cos(rx)]])
    Ry = np.array([[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]])
    Rz = np.array([[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx

def get_transform_matrix(tx, ty, tz, rx, ry, rz):
    T = np.eye(4)
    T[:3, :3] = get_rotation_matrix(rx, ry, rz)
    T[0, 3] = tx
    T[1, 3] = ty
    T[2, 3] = tz
    return T

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    parser.add_argument('--source', default='step10_final_pose.json',
                         help="Which *_pose_fit.json in the session dir to pull delta_translation/delta_rotvec from.")
    parser.add_argument('--label', default='',
                         help="Suffix for the output filename, e.g. 'mask' -> TORXL_corrected_mask.ls")
    args = parser.parse_args()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    logger = PipelineLogger(args.session, base_dir, "STEP 08: GENERATE LS FILE")

    config_path = os.path.join(base_dir, 'pipeline_config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Load Final Current Pose
    session_dir = os.path.join(base_dir, 'results', args.session)
    pose_file = os.path.join(session_dir, args.source)
    if not os.path.exists(pose_file):
        logger.log(f"Error: {pose_file} not found! Cannot apply correction.")
        sys.exit(1)
    with open(pose_file, 'r') as f:
        delta_data = json.load(f)

    dx, dy, dz = delta_data['delta_translation']
    from scipy.spatial.transform import Rotation
    r = Rotation.from_rotvec(delta_data['delta_rotvec'])
    R_delta = r.as_matrix()
    t_delta = np.array([dx, dy, dz])
    drx, dry, drz = r.as_euler('xyz', degrees=True)

    ls_in_path = os.path.join(base_dir, config['paths']['ls_file'])
    with open(ls_in_path, 'r') as f:
        lines = f.readlines()

    # The delta pose (rotation + translation) describes how the helmet moved as a
    # RIGID BODY. Rotating raw robot coordinates around the world origin (0,0,0) -
    # which can be >1000mm away from the helmet - turns a few mm/deg of real motion
    # into tens of mm of spurious lever-arm displacement. Rotation must pivot around
    # the helmet's own center instead. We use the centroid of the original LS points
    # as that pivot (same convention app.py already uses for etalon_center elsewhere).
    coord_pattern = re.compile(
        r"X\s*=\s*([-+]?\d*\.?\d+).*?Y\s*=\s*([-+]?\d*\.?\d+).*?Z\s*=\s*([-+]?\d*\.?\d+)",
        re.DOTALL
    )
    raw_text = ''.join(lines)
    all_xyz = []
    for block in re.findall(r"P\[\d+\]\{(.*?)\}", raw_text, re.DOTALL):
        cm = coord_pattern.search(block)
        if cm:
            all_xyz.append([float(cm.group(1)), float(cm.group(2)), float(cm.group(3))])
    all_xyz = np.array(all_xyz, dtype=float)
    if len(all_xyz) == 0:
        logger.log("Error: could not parse any points from LS file to compute pivot center!")
        sys.exit(1)
    pivot_center = all_xyz.mean(axis=0)
    logger.log(f"Rotation pivot (centroid of {len(all_xyz)} LS points): "
               f"({pivot_center[0]:.2f}, {pivot_center[1]:.2f}, {pivot_center[2]:.2f})")

    # Process LS lines point by point, handling multi-line point definitions
    out_lines = []
    points_modified = 0
    in_point_block = False
    point_lines = []  # buffer for lines belonging to the current point

    for line in lines:
        # Detect the start of a point block (e.g., "P[12]{")
        if re.match(r"\s*P\[\d+\]\{", line):
            in_point_block = True
            point_lines = [line]
            continue
        if in_point_block:
            point_lines.append(line)
            # End of point block detected by a line containing a closing brace
            if line.strip().startswith('}'):
                # Extract coordinate and orientation values from the collected lines
                x = y = z = w = p = r_val = None
                for pl in point_lines:
                    m = re.search(r"X\s*=\s*([-+]?\d*\.?\d+)", pl)
                    if m:
                        x = float(m.group(1))
                    m = re.search(r"Y\s*=\s*([-+]?\d*\.?\d+)", pl)
                    if m:
                        y = float(m.group(1))
                    m = re.search(r"Z\s*=\s*([-+]?\d*\.?\d+)", pl)
                    if m:
                        z = float(m.group(1))
                    m = re.search(r"W\s*=\s*([-+]?\d*\.?\d+)", pl)
                    if m:
                        w = float(m.group(1))
                    m = re.search(r"P\s*=\s*([-+]?\d*\.?\d+)", pl)
                    if m:
                        p = float(m.group(1))
                    m = re.search(r"R\s*=\s*([-+]?\d*\.?\d+)", pl)
                    if m:
                        r_val = float(m.group(1))
                # Apply the pose correction if XYZ were found
                if x is not None and y is not None and z is not None:
                    p_orig = np.array([x, y, z])
                    p_new = pivot_center + R_delta @ (p_orig - pivot_center) + t_delta
                    x_new, y_new, z_new = p_new
                    # Adjust orientation values
                    w_new = (w if w is not None else 0.0) + drx
                    p_new = (p if p is not None else 0.0) + dry
                    r_new = (r_val if r_val is not None else 0.0) + drz
                    # Rebuild the point block with updated values
                    new_block = []
                    for pl in point_lines:
                        if 'X =' in pl:
                            new_block.append(re.sub(r"X\s*=\s*[-+]?\d*\.?\d+", f"X = {x_new:.3f}", pl))
                        elif 'Y =' in pl:
                            new_block.append(re.sub(r"Y\s*=\s*[-+]?\d*\.?\d+", f"Y = {y_new:.3f}", pl))
                        elif 'Z =' in pl:
                            new_block.append(re.sub(r"Z\s*=\s*[-+]?\d*\.?\d+", f"Z = {z_new:.3f}", pl))
                        elif 'W =' in pl:
                            new_block.append(re.sub(r"W\s*=\s*[-+]?\d*\.?\d+", f"W = {w_new:.3f}", pl))
                        elif re.search(r"P\s*=", pl):
                            new_block.append(re.sub(r"P\s*=\s*[-+]?\d*\.?\d+", f"P = {p_new:.3f}", pl))
                        elif 'R =' in pl:
                            new_block.append(re.sub(r"R\s*=\s*[-+]?\d*\.?\d+", f"R = {r_new:.3f}", pl))
                        else:
                            new_block.append(pl)
                    out_lines.extend(new_block)
                    points_modified += 1
                else:
                    # If parsing failed, keep original lines
                    out_lines.extend(point_lines)
                # Reset state for next point
                in_point_block = False
                point_lines = []
            continue
        # Lines outside point blocks are copied verbatim
        out_lines.append(line)

    out_name = f'TORXL_corrected_{args.label}.ls' if args.label else 'TORXL_corrected.ls'
    out_ls_path = os.path.join(logger.results_dir, out_name)
    with open(out_ls_path, 'w') as f:
        f.writelines(out_lines)

    logger.log(f"Generated new LS file with {points_modified} corrected points.")
    logger.log(f"Saved to: {out_ls_path}")

if __name__ == '__main__':
    main()
