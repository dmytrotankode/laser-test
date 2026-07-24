"""
Standalone validation tool - NOT part of the main pipeline/UI.

Swaps input/photos_current for a converted archive test set (v1..v5),
re-runs steps 05-08 unchanged, then compares the generated current_helmet.ls
against the reference .ls recorded on production for that same set.

Does not modify any file under scripts/ or app.py. Restores the original
photos_current afterward. Safe to run repeatedly; does not run automatically
as part of the normal session flow.
"""
import os
import re
import sys
import json
import shutil
import subprocess
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVE_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'archive'))
PHOTOS_CURRENT = os.path.join(BASE_DIR, 'input', 'photos_current')
PYTHON = os.path.join(BASE_DIR, 'venv', 'Scripts', 'python.exe')

ARCHIVE_SETS = {
    'v1': 'TORXL_NEW_PROG2.LS',
    'v2': 'TORXL_NEW_PROG2_2.LS',
    'v3': 'TORXL_NEW_PROG2_3.LS',
    'v4': 'TORXL_NEW_PROG2_4.LS',
    'v5': 'TORXL_NEW_PROG2_5.LS',
}


def load_ls_points(path):
    pts = []
    pat = re.compile(
        r'P\[(\d+)\]\{[^}]*X\s*=\s*([-\d.]+)[^}]*Y\s*=\s*([-\d.]+)[^}]*Z\s*=\s*([-\d.]+)',
        re.IGNORECASE | re.DOTALL)
    txt = open(path, errors='replace').read()
    for m in pat.finditer(txt):
        pts.append((int(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))))
    return pts


def kabsch(P, Q):
    cP = P.mean(axis=0)
    cQ = Q.mean(axis=0)
    P0 = P - cP
    Q0 = Q - cQ
    H = P0.T @ Q0
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1, 1, d])
    R = Vt.T @ D @ U.T
    t = cQ - R @ cP
    return R, t


def rot_angle_deg(R):
    tr = np.clip((np.trace(R) - 1) / 2, -1, 1)
    return np.degrees(np.arccos(tr))


def run_script(script_name, session_id, extra_args=None):
    script_path = os.path.join(BASE_DIR, 'scripts', script_name)
    args = [PYTHON, script_path, '--session', session_id] + (extra_args or [])
    result = subprocess.run(args, cwd=BASE_DIR, capture_output=True, text=True)
    return result


def swap_photos(v_label):
    conv_dir = os.path.join(ARCHIVE_DIR, v_label, 'converted')
    frames = sorted(f for f in os.listdir(conv_dir) if f.startswith('frame') and not f.endswith('_thumb.png'))
    mapping = {'frame1': 'back.png', 'frame2': 'left.png', 'frame3': 'top.png'}
    for f in frames:
        prefix = f.split('_')[0]  # frame1 / frame2 / frame3
        dest_name = mapping[prefix]
        shutil.copyfile(os.path.join(conv_dir, f), os.path.join(PHOTOS_CURRENT, dest_name))


def compare_to_reference(generated_ls_path, reference_ls_path, base_dir):
    """
    Primary metric is direct point-by-point distance between the generated
    and reference .ls (same point IDs, no fitting involved) - this is what
    you actually see when overlaying the two paths visually.

    The Kabsch-based t/angle numbers are kept only as a secondary diagnostic:
    comparing the *translation vectors* of two independently-fit rigid
    transforms is misleading whenever their fitted rotations differ, because
    t is defined relative to that fit's own rotation (t = centroid_target -
    R @ centroid_source) - a rotation difference of even 1-2 degrees can make
    the two t vectors diverge by tens of mm even when the actual points end
    up close together. Point-by-point distance has no such coupling.
    """
    orig_ls_path = os.path.join(base_dir, 'input', 'ls_file', 'TORXL_NEW_PROG.LS')
    orig = load_ls_points(orig_ls_path)
    o = np.array([[p[1], p[2], p[3]] for p in orig])
    mask = np.ones(len(o), dtype=bool)
    mask[[0, 97]] = False  # exclude outlier ids 1 and 98

    gen = load_ls_points(generated_ls_path)
    g = np.array([[p[1], p[2], p[3]] for p in gen])[:98]

    ref = load_ls_points(reference_ls_path)
    r = np.array([[p[1], p[2], p[3]] for p in ref])[:98]

    point_dist = np.linalg.norm(g[mask] - r[mask], axis=1)

    R_gen, t_gen = kabsch(o[mask], g[mask])
    R_ref, t_ref = kabsch(o[mask], r[mask])

    return {
        'point_by_point_mm': {
            'mean': float(point_dist.mean()),
            'median': float(np.median(point_dist)),
            'max': float(point_dist.max()),
            'min': float(point_dist.min()),
        },
        'kabsch_diagnostic': {
            'generated': {'t': t_gen.tolist(), 'angle_deg': float(rot_angle_deg(R_gen))},
            'reference': {'t': t_ref.tolist(), 'angle_deg': float(rot_angle_deg(R_ref))},
            't_error_mm': float(np.linalg.norm(t_gen - t_ref)),
            'angle_error_deg': float(abs(rot_angle_deg(R_gen) - rot_angle_deg(R_ref))),
        },
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: validate_against_archive.py <session_id> <v1|v2|v3|v4|v5>")
        sys.exit(1)
    session_id = sys.argv[1]
    v_label = sys.argv[2]

    swap_photos(v_label)

    for step in ['step05_segment_current.py', 'step06_fit_3d.py', 'step07_compare.py', 'step08_visualize.py']:
        res = run_script(step, session_id)
        if res.returncode != 0:
            print(f"FAILED at {step}")
            print(res.stdout)
            print(res.stderr)
            sys.exit(1)

    results_dir = os.path.join(BASE_DIR, 'results', session_id)
    with open(os.path.join(results_dir, 'step07_result.json')) as f:
        step07 = json.load(f)
    delta_3d = step07.get('delta_3d', {})

    generated_ls = os.path.join(results_dir, 'current_helmet.ls')
    # Keep a labeled copy so a later run for a different v-set doesn't clobber this one.
    labeled_copy = os.path.join(results_dir, f'current_helmet_{v_label}.ls')
    shutil.copyfile(generated_ls, labeled_copy)

    reference_ls = os.path.join(ARCHIVE_DIR, v_label, ARCHIVE_SETS[v_label])
    comparison = compare_to_reference(generated_ls, reference_ls, BASE_DIR)

    output = {
        'v_label': v_label,
        'delta_3d': delta_3d,
        'comparison': comparison,
    }
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
