import os
import sys
import json
import argparse
import numpy as np
import re
from scipy.spatial.transform import Rotation as R

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lsgeom


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

    # Variant 1 (k-NN dynamic etalon): step04 picks the 1-2 archive variants closest in
    # pixel-feature space to the current photo (s4["selected_neighbors"]/["neighbor_weights"]).
    # If those are real physical archive variants (not the CAD baseline), the export is built
    # by rotating a WEIGHTED BLEND of their own recorded ground_truth.ls points (real physical
    # dome shape) instead of the theoretical CAD program. The transform applied is the pose
    # delta relative to the blended reference (delta_rel_to_etalon), and the rotation pivot is
    # recentered by the blended CAD-relative offset (gt_ref), since gt_ref was itself derived
    # by rotating the CAD points about `center`.
    #
    # Point numbering is NOT consistent between the two archive batches (old: the contour runs
    # P[2], P[99], P[3]..P[97], retreat P[98];  new: contour P[2]..P[98], retreat P[99]), so
    # nothing below may assume that index i of one file is index i of another. Traversal order
    # comes from /MN, blending happens in arc-length space with an explicit phase alignment,
    # and approach/retreat points are identified from the motion program rather than from
    # position in the file. The earlier index-based version froze the mid-contour P[99] as if
    # it were a retreat point, and blended points a full ~10 mm step apart across batches.
    etalon = s4.get("etalon", "v1")
    neighbors = s4.get("selected_neighbors", [etalon])
    neighbor_weights = s4.get("neighbor_weights", [1.0])
    neighbor_paths = [os.path.join(base_dir, 'input', 'archive', n, 'ground_truth.ls')
                      for n in neighbors]

    if all(os.path.exists(p) for p in neighbor_paths):
        d = s4["delta_rel_to_etalon"]
        # The rotation pivot must be the one the model was FITTED about, otherwise the
        # predicted rotation and translation are applied around a different point than
        # they were measured around. step04 passes it through from input/model_pose.json.
        if "pivot" in s4:
            center = np.array(s4["pivot"], dtype=float)
        else:
            gt_ref = s4["gt_ref"]
            center = center + np.array([gt_ref['x_mm'], gt_ref['y_mm'], gt_ref['z_mm']])

        # The nearest neighbour supplies the program template (headers, speeds, motion
        # instructions, approach/retreat) and defines the phase origin of the blend.
        orig_ls_path = neighbor_paths[0]
        progs = [lsgeom.load(p) for p in neighbor_paths]
        broken = [(n, p.problems()) for n, p in zip(neighbors, progs) if p.problems()]
        if broken:
            print(f"Error: unusable source program(s): {broken}")
            sys.exit(1)

        tmpl = progs[0]
        app_ids, cont_ids, ret_ids = tmpl.split_path()

        # Everything below happens in CUT-LINE space: each neighbour's recorded path is
        # pushed back along its own tool axis by its own standoff, so what gets blended
        # and rotated is where the beam LANDED, not where the nozzle happened to sit.
        #
        # This matters because the standoff drifted between capture sessions by up to
        # 6.3 mm (v15/v16), and the customer confirmed it is slack, not a setpoint - the
        # beam runs along the tool axis, so that drift never moved the cut. Blending
        # nozzle paths would mix in that drift as if it were part of the helmet's shape.
        # The nominal standoff is put back at the end, so the exported program still
        # tells the robot to stand off 10 mm. See PLAN.md sections 2 and 4.
        model_path = os.path.join(base_dir, 'input', 'model_pose.json')
        with open(model_path, 'r', encoding='utf-8') as f:
            model = json.load(f)
        standoff_out = float(model.get("nominal_standoff", lsgeom.NOMINAL_STANDOFF))
        standoffs = dict(model.get("standoff", {}))
        missing = [n for n in neighbors if n not in standoffs]
        if missing:
            # A template outside the library (a hand-supplied program, a test fixture).
            # Assuming the nominal here would silently bake a several-mm offset into the
            # export, so measure it instead - the same fit fit_model.py uses, against the
            # library anchor's cut line.
            anchor = model.get("anchor")
            anchor_prog = os.path.join(base_dir, 'input', 'archive', anchor,
                                       'ground_truth.ls')
            if anchor not in standoffs or not os.path.exists(anchor_prog):
                print(f"Error: no fitted standoff for {missing} and no usable anchor "
                      f"in {model_path}; re-run scripts/fit_model.py --emit")
                sys.exit(1)
            ref, _ = lsgeom.cut_surface(lsgeom.load(anchor_prog), standoffs[anchor])
            for n, p in zip(neighbors, progs):
                if n in standoffs:
                    continue
                standoffs[n], res = lsgeom.fit_standoff(p, ref)
                print(f"Note: {n} is not in the library; standoff measured on the fly "
                      f"= {standoffs[n]:.2f} mm (shape residual {res:.2f} mm)")

        # blend_contours evaluates at the template's own vertices, so the exported
        # program keeps exactly the point count and spacing the robot expects, and a
        # single-neighbour blend reproduces that neighbour bit-for-bit
        blended_cut = lsgeom.blend_contours(
            [lsgeom.cut_surface(p, standoffs[n], full=True)[0]
             for n, p in zip(neighbors, progs)], neighbor_weights)

        # The export rewrites X/Y/Z only and leaves W/P/R untouched, so the tool axes the
        # robot will actually use are the template's. Re-projecting along those same axes
        # is therefore self-consistent by construction, not an approximation.
        axis_by_id = dict(zip(cont_ids, lsgeom.tool_axes(tmpl, cont_ids)))

        src_xyz = {i: np.array(tmpl.points[i][:3]) for i in tmpl.points}
        for k, i in enumerate(cont_ids):
            src_xyz[i] = blended_cut[k]
        transform_ids = set(cont_ids)
        print(f"Master trajectory: blend of {neighbors} (weights {neighbor_weights}) "
              f"in cut-line space, standoffs "
              f"{[round(standoffs[n], 2) for n in neighbors]} -> {standoff_out:g} mm; "
              f"template {neighbors[0]}, {len(cont_ids)} contour points, "
              f"approach {app_ids} / retreat {ret_ids} kept fixed in machine space.")
    else:
        orig_ls_path = os.path.join(base_dir, 'input', 'ls_file', 'TORXL_NEW_PROG.LS')
        d = s4["delta_3d"]
        cad = lsgeom.load(orig_ls_path)
        _, cad_cont, _ = cad.split_path()
        src_xyz = {i: np.array(cad.points[i][:3]) for i in cad.points}
        transform_ids = set(cad_cont)
        # CAD fallback stays in nozzle coordinates: the CAD program already carries the
        # standoff the CAM operator asked for, and there is no fitted value to strip.
        axis_by_id, standoff_out = {}, 0.0
        print(f"Master trajectory: CAD program (no archive neighbour available), "
              f"{len(cad_cont)} contour points.")

    q_delta = lsgeom.rot_from_ypr(d['yaw_deg'], d['pitch_deg'], d['roll_deg'])
    trans = np.array([d['x_mm'], d['y_mm'], d['z_mm']])

    out_ls_file = "current_helmet.ls"
    out_ls_path = os.path.join(results_dir, out_ls_file)

    with open(orig_ls_path, 'r', encoding='utf-8', errors='ignore') as f:
        ls_content = f.read()

    # Rewrite the X/Y/Z of each P[i] record in place, keeping every other byte of the
    # program (headers, speeds, /MN body, W/P/R) untouched.
    pattern = re.compile(
        r'(P\[(\d+)\]\{.*?X\s*=\s*)([-\d.]+)(.*?Y\s*=\s*)([-\d.]+)(.*?Z\s*=\s*)([-\d.]+)',
        re.DOTALL | re.IGNORECASE)

    def replace_point(match):
        i = int(match.group(2))
        pt = src_xyz[i]
        if i in transform_ids:
            pt = q_delta.apply(pt - center) + center + trans
            if i in axis_by_id:
                # back from the cut line to a nozzle pose, at the nominal standoff
                pt = pt + standoff_out * axis_by_id[i]
        return f"{match.group(1)}{pt[0]:.3f}{match.group(4)}{pt[1]:.3f}{match.group(6)}{pt[2]:.3f}"

    new_ls_content = pattern.sub(replace_point, ls_content)

    with open(out_ls_path, 'w', encoding='utf-8') as f:
        f.write(new_ls_content)

    # An unloadable program is worse than no program: fail loudly instead of handing the
    # operator a file the controller will reject (or, worse, one it accepts with no moves).
    check = lsgeom.load(out_ls_path)
    problems = check.problems()
    if len(check.order) < 90:
        problems.append(f"only {len(check.order)} motion instructions")
    if set(check.points) != set(src_xyz):
        problems.append("exported point set differs from the template")
    if problems:
        os.remove(out_ls_path)
        print(f"Error: refusing to emit an invalid program: {problems}")
        sys.exit(1)
    print(f"Exported transformed LS file to {out_ls_path} "
          f"({len(check.order)} motion instructions, {len(check.points)} points)")

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
            gt_prog = lsgeom.load(gt_ls_path)
            for i in sorted(gt_prog.points):
                x, y, z = gt_prog.points[i][:3]
                ground_truth_points.append({"x": x, "y": y, "z": z})
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
                Vt[2, :] *= -1
                rot = Vt.T @ U.T
            tr = c_gt - rot @ c_orig

            center_orig = np.array([s2.get('tx', 1170.98), s2.get('ty', 785.15), s2.get('tz', -191.86)])
            center_gt = rot @ center_orig + tr
            shift = center_gt - center_orig
            # Same convention as the one used to APPLY the rotation above. This used to
            # be as_euler('zyx') - extrinsic - while application was from_euler('ZYX') -
            # intrinsic. Different compositions; on this data the mismatch is worth
            # ~0.4 mm mean on the contour. See PLAN.md B8.
            yaw_d, pitch_d, roll_d = lsgeom.ypr_from_rot(rot)

            gt_delta_3d = {
                "x_mm": round(float(shift[0]), 2),
                "y_mm": round(float(shift[1]), 2),
                "z_mm": round(float(shift[2]), 2),
                "roll_deg": round(roll_d, 2),
                "pitch_deg": round(pitch_d, 2),
                "yaw_deg": round(yaw_d, 2)
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
