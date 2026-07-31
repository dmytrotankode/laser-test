"""Regression suite for the .LS export path (step05).

Deliberately structured so that most tests are PASS/FAIL on structure or on an
invariant, not on "the error number got smaller". A number that improves on two
held-out variants proves very little; an export that a robot cannot load, or a
result that changes depending on which template file was picked, is a hard failure.

Run:  python tests/test_export.py
Assumes results/audit_<v>/ sessions already exist (step03+step04 done); it only
re-runs step05, which is fast. Rebuild them with tests/rebuild_sessions.py.
"""
import os
import sys
import json
import shutil
import subprocess
import numpy as np

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import lsgeom  # noqa: E402

from scipy.spatial.transform import Rotation as R  # noqa: E402

VARIANTS = [f"v{i}" for i in range(1, 17)]
OLD_BATCH = ["v1", "v2", "v3", "v4", "v5", "v6"]
NEW_BATCH = [f"v{i}" for i in range(7, 17)]

FAILURES = []
NOTES = []


def check(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if detail else ""))
    if not ok:
        FAILURES.append(f"{name}: {detail}")
    return ok


def sess_dir(v):
    return os.path.join(BASE, 'results', f'audit_{v}')


def run_step05(session):
    r = subprocess.run([sys.executable, os.path.join(BASE, 'scripts', 'step05_visualize_export.py'),
                        '--session', session], cwd=BASE, capture_output=True, text=True)
    return r.returncode == 0, r.stdout + r.stderr


def gt_program(v):
    return lsgeom.load(os.path.join(BASE, 'input', 'archive', v, 'ground_truth.ls'))


# ---------------------------------------------------------------- T1
def t1_structural():
    """Every export must be a program a robot can actually load."""
    print("\nT1  structural validity of every export")
    for v in VARIANTS:
        d = sess_dir(v)
        exp = os.path.join(d, 'current_helmet.ls')
        if not os.path.exists(exp):
            check(f"T1 {v} export exists", False, "missing")
            continue
        prog = lsgeom.load(exp)
        probs = prog.problems()
        check(f"T1 {v} loadable", not probs, "; ".join(probs))

        s4 = json.load(open(os.path.join(d, 'step04_result.json'), encoding='utf-8'))
        nb = s4['selected_neighbors']
        tmpl = min((gt_program(n) for n in nb), key=lambda p: len(p.points))
        # absolute floor first: "same as the template" is worthless if the template is
        # itself corrupted (both sides being 1 would pass a relative check)
        check(f"T1 {v} has a real program body",
              len(prog.order) >= 90, f"{len(prog.order)} motion instructions, expected ~99")
        check(f"T1 {v} motion count matches template",
              len(prog.order) == len(tmpl.order),
              f"export {len(prog.order)} vs template {len(tmpl.order)}")
        check(f"T1 {v} point set matches template",
              set(prog.points) == set(tmpl.points),
              f"export {len(prog.points)} vs template {len(tmpl.points)} points")


# ---------------------------------------------------------------- T2
def t2_identity():
    """When the computed delta is zero the export must reproduce the source exactly.

    Any drift here is pure plumbing error (parsing, formatting, pivot), independent
    of whether the pose model is any good."""
    print("\nT2  zero-delta identity")
    for v in VARIANTS:
        d = sess_dir(v)
        s4 = json.load(open(os.path.join(d, 'step04_result.json'), encoding='utf-8'))
        rel = s4['delta_rel_to_etalon']
        if max(abs(x) for x in rel.values()) > 1e-6:
            continue                       # only meaningful for exact self-matches
        nb = s4['selected_neighbors']
        if len(nb) != 1:
            continue
        src = gt_program(nb[0])
        exp = lsgeom.load(os.path.join(d, 'current_helmet.ls'))
        common = sorted(set(src.points) & set(exp.points))
        if not common:
            check(f"T2 {v} shares points with source", False, "no common P[i]")
            continue
        err = max(np.linalg.norm(src.xyz(i) - exp.xyz(i)) for i in common)
        check(f"T2 {v} identity (delta=0, etalon={nb[0]})", err < 1e-3, f"max drift {err:.4f} mm")


# ---------------------------------------------------------------- T3
def t3_roundtrip():
    """Feed step05 a KNOWN 6-DOF delta, check every contour point landed where asked.

    Scope note: this verifies step05's PLUMBING (which points get transformed, pivot,
    translation) against the same 'ZYX' convention step05 itself uses. It does NOT
    validate that convention - catching the extrinsic/intrinsic mismatch between label
    extraction and application (see PLAN.md B8) needs a test that goes through the
    label-extraction path, which lives in step04/gt_delta_3d, not here."""
    print("\nT3  synthetic round-trip through step05")
    truth = dict(x_mm=1.7, y_mm=-0.9, z_mm=2.3, roll_deg=-2.5, pitch_deg=3.1, yaw_deg=1.4)
    for etalon in ("v1", "v7"):
        s = f"test_roundtrip_{etalon}"
        d = os.path.join(BASE, 'results', s)
        os.makedirs(d, exist_ok=True)
        shutil.copy(os.path.join(sess_dir('v1'), 'step02_result.json'), d)
        json.dump({"variant": "default"}, open(os.path.join(d, 'config.json'), 'w', encoding='utf-8'))
        s4 = json.load(open(os.path.join(sess_dir('v1'), 'step04_result.json'), encoding='utf-8'))
        s4['selected_neighbors'] = [etalon]
        s4['neighbor_weights'] = [1.0]
        s4['etalon'] = etalon
        s4['delta_rel_to_etalon'] = truth
        s4['gt_ref'] = dict(x_mm=0.0, y_mm=0.0, z_mm=0.0,
                            roll_deg=0.0, pitch_deg=0.0, yaw_deg=0.0)
        json.dump(s4, open(os.path.join(d, 'step04_result.json'), 'w', encoding='utf-8'), ensure_ascii=False)

        ok, log = run_step05(s)
        if not check(f"T3 {etalon} step05 ran", ok, log[-300:] if not ok else ""):
            continue

        src = gt_program(etalon)
        exp = lsgeom.load(os.path.join(d, 'current_helmet.ls'))
        _, cids, _ = src.split_path()
        A = np.array([src.points[i][:3] for i in cids])
        B = np.array([exp.points[i][:3] for i in cids])

        s2 = json.load(open(os.path.join(d, 'step02_result.json'), encoding='utf-8'))
        pivot = np.array([s2['tx'], s2['ty'], s2['tz']])
        Rm = R.from_euler('ZYX', [truth['yaw_deg'], truth['pitch_deg'], truth['roll_deg']],
                          degrees=True)
        want = Rm.apply(A - pivot) + pivot + np.array([truth['x_mm'], truth['y_mm'], truth['z_mm']])
        err = float(np.abs(B - want).max())
        check(f"T3 {etalon} applied transform matches requested", err < 1e-2,
              f"max deviation {err:.4f} mm")


# ---------------------------------------------------------------- T4
def renumber_ls(text, shift):
    """Cyclically renumber the contour points of an .LS program.

    Produces a file describing the SAME physical trajectory under a different point
    numbering - exactly the difference between the two archive batches. Rewrites both
    /MN motion lines and /POS blocks so the file stays self-consistent."""
    prog = lsgeom.Program(text)
    app, cont, ret = prog.split_path()
    if len(cont) < 10:
        return None
    fixed = list(app) + list(ret)
    rolled = cont[shift:] + cont[:shift]        # same ring, different start
    # new label for each old id: contour slot k keeps label cont[k]
    mapping = {old: new for old, new in zip(rolled, cont)}
    for i in fixed:
        mapping[i] = i
    # traversal must follow the rolled ring so the physical path is unchanged
    new_order = list(app) + [mapping[i] for i in rolled] + list(ret)

    body = []
    for i in new_order:
        x, y, z, w, pp, r = prog.points[{v: k for k, v in mapping.items()}[i]]
        body.append((i, x, y, z, w, pp, r))

    out = ["/PROG  RENUM", "/ATTR", 'OWNER		= MNEDITOR;', "/MN"]
    for n, i in enumerate(new_order, 1):
        out.append(f"  {n:3d}:L P[{i}] 100mm/sec FINE    ;")
    out.append("/POS")
    for i, x, y, z, w, pp, r in sorted(body):
        out.append(
            f"P[{i}]{{\n   GP1:\n\tUF : 2, UT : 2,\t\tCONFIG : 'F D T, 0, 0, 0',\n"
            f"\tX = {x:9.3f}  mm,\tY = {y:9.3f}  mm,\tZ = {z:9.3f}  mm,\n"
            f"\tW = {w:9.3f} deg,\tP = {pp:9.3f} deg,\tR = {r:9.3f} deg\n}};")
    out.append("/END")
    return "\n".join(out) + "\n"


def _export_with_template(tag, tmpl_path, delta):
    """Run step05 forcing a specific template file, return the exported contour."""
    s = f"test_tmpl_{tag}"
    d = os.path.join(BASE, 'results', s)
    os.makedirs(d, exist_ok=True)
    shutil.copy(os.path.join(sess_dir('v1'), 'step02_result.json'), d)
    json.dump({"variant": "default"}, open(os.path.join(d, 'config.json'), 'w', encoding='utf-8'))
    # step05 resolves neighbours to input/archive/<name>/ground_truth.ls, so stage the
    # template under a throwaway variant name
    stage = os.path.join(BASE, 'input', 'archive', f'_tmp_{tag}')
    os.makedirs(stage, exist_ok=True)
    shutil.copy(tmpl_path, os.path.join(stage, 'ground_truth.ls'))
    s4 = json.load(open(os.path.join(sess_dir('v1'), 'step04_result.json'), encoding='utf-8'))
    s4.update(selected_neighbors=[f'_tmp_{tag}'], neighbor_weights=[1.0], etalon=f'_tmp_{tag}',
              delta_rel_to_etalon=delta,
              gt_ref=dict(x_mm=0.0, y_mm=0.0, z_mm=0.0,
                          roll_deg=0.0, pitch_deg=0.0, yaw_deg=0.0))
    json.dump(s4, open(os.path.join(d, 'step04_result.json'), 'w', encoding='utf-8'),
              ensure_ascii=False)
    ok, log = run_step05(s)
    if not ok:
        return None, log
    return lsgeom.load(os.path.join(d, 'current_helmet.ls')).contour_xyz()[0], ""


def t4_order_invariance():
    """The export must not depend on HOW the template numbers its points.

    Tolerance-free by construction: the two templates describe the identical physical
    trajectory, so the two exported curves must coincide. Comparing templates from
    different helmet POSES (an earlier draft of this test) would have measured the
    shape difference between them instead, with an arbitrary tolerance."""
    print("\nT4  point-numbering invariance of the export")
    delta = dict(x_mm=1.0, y_mm=-0.5, z_mm=0.8, roll_deg=-1.2, pitch_deg=0.9, yaw_deg=0.3)
    tmpdir = os.path.join(BASE, 'results', '_t4_tmp')
    os.makedirs(tmpdir, exist_ok=True)
    for src_v in ('v1', 'v14'):
        orig = os.path.join(BASE, 'input', 'archive', src_v, 'ground_truth.ls')
        text = open(orig, encoding='utf-8', errors='ignore').read()
        perm = renumber_ls(text, shift=23)
        if perm is None:
            check(f"T4 {src_v} renumbering built", False, "contour too short")
            continue
        # sanity: the permuted file must describe the same point cloud
        a = {tuple(round(c, 3) for c in v[:3]) for v in lsgeom.Program(text).points.values()}
        b = {tuple(round(c, 3) for c in v[:3]) for v in lsgeom.Program(perm).points.values()}
        if not check(f"T4 {src_v} permuted file has same point cloud", a == b,
                     f"{len(a ^ b)} differing points"):
            continue
        pf = os.path.join(tmpdir, f'{src_v}_perm.ls')
        open(pf, 'w', encoding='utf-8').write(perm)

        c0, e0 = _export_with_template(f'{src_v}_orig', orig, delta)
        c1, e1 = _export_with_template(f'{src_v}_perm', pf, delta)
        if c0 is None or c1 is None:
            check(f"T4 {src_v} both exports ran", False, (e0 + e1)[-300:])
            continue
        d01 = lsgeom.curve_distance(c0, c1)
        d10 = lsgeom.curve_distance(c1, c0)
        worst = max(d01.max(), d10.max())
        check(f"T4 {src_v} export invariant to point numbering", worst < 0.05,
              f"curves differ by up to {worst:.3f} mm")
        NOTES.append(f"T4 {src_v} numbering invariance {worst:.3f} mm")


def t4b_blend_betweenness():
    """A blend of two templates must lie BETWEEN them, not beside both.

    Also tolerance-free: whatever the two curves are, the weighted blend can never be
    further from either one than they are from each other. Blending index-by-index
    across the two batches violates this, because index i of one is a full ~10 mm step
    away from index i of the other."""
    print("\nT4b blend lies between its inputs")
    A = lsgeom.load(os.path.join(BASE, 'input', 'archive', 'v1', 'ground_truth.ls')).contour_xyz()[0]
    B = lsgeom.load(os.path.join(BASE, 'input', 'archive', 'v14', 'ground_truth.ls')).contour_xyz()[0]
    sep = float(lsgeom.curve_distance(A, B).mean())
    mix = lsgeom.blend_contours([A, B], [0.5, 0.5])
    dA = float(lsgeom.curve_distance(mix, A).mean())
    dB = float(lsgeom.curve_distance(mix, B).mean())
    # A 50/50 blend of correctly-corresponded points sits at the midpoint, so each
    # distance should be about sep/2. Merely being "between" is too weak a criterion -
    # the naive index-wise blend passes that too, so require the midpoint.
    for lbl, dd in (("A", dA), ("B", dB)):
        check(f"T4b 50/50 blend sits midway to {lbl}", 0.35 * sep <= dd <= 0.65 * sep,
              f"blend->{lbl} {dd:.2f} mm, expected ~{sep / 2:.2f} (A<->B {sep:.2f})")
    # the naive index-wise blend, for contrast
    n = min(len(A), len(B))
    naive = 0.5 * A[:n] + 0.5 * B[:n]
    nA = float(lsgeom.curve_distance(naive, A).mean())
    NOTES.append(f"T4b arc-length blend->A {dA:.2f} | naive index blend->A {nA:.2f} "
                 f"| A<->B {sep:.2f} (ideal {sep / 2:.2f})")


# ---------------------------------------------------------------- T5
def t5_whiskers():
    """Only genuine approach/retreat points may be left untransformed.

    In the old batch P[99] sits mid-contour (traversal is P[2] -> P[99] -> P[3]); a
    file-order heuristic mistakes it for a retreat point and exports it unrotated."""
    print("\nT5  approach/retreat classification")
    for v in VARIANTS:
        d = sess_dir(v)
        s4 = json.load(open(os.path.join(d, 'step04_result.json'), encoding='utf-8'))
        if max(abs(x) for x in s4['delta_rel_to_etalon'].values()) < 1e-6:
            continue                       # zero delta: nothing moves, test is vacuous
        nb = s4['selected_neighbors']
        src = min((gt_program(n) for n in nb), key=lambda p: len(p.points))
        exp = lsgeom.load(os.path.join(d, 'current_helmet.ls'))
        if exp.problems():
            check(f"T5 {v} export parseable", False, "; ".join(exp.problems()))
            continue
        app, cont, ret = src.split_path()
        unmoved = [i for i in sorted(set(src.points) & set(exp.points))
                   if np.linalg.norm(src.xyz(i) - exp.xyz(i)) < 1e-6]
        stuck_contour = sorted(set(unmoved) & set(cont))
        check(f"T5 {v} no contour point left untransformed", not stuck_contour,
              f"P{stuck_contour} frozen (should have moved)")


# ---------------------------------------------------------------- T6
def t6_regression():
    """Curve error per variant against a recorded baseline."""
    print("\nT6  accuracy regression (metric: point -> GT curve)")
    base_file = os.path.join(os.path.dirname(__file__), 'baseline_errors.json')
    cur = {}
    for v in VARIANTS:
        exp = lsgeom.load(os.path.join(sess_dir(v), 'current_helmet.ls'))
        if exp.problems():
            cur[v] = None
            continue
        C, _ = exp.contour_xyz()
        G, _ = gt_program(v).contour_xyz()
        e = lsgeom.curve_distance(C, G)
        cur[v] = dict(mean=round(float(e.mean()), 3), max=round(float(e.max()), 3))

    if not os.path.exists(base_file):
        json.dump(cur, open(base_file, 'w', encoding='utf-8'), indent=2)
        print(f"  (no baseline yet - recorded current values to {os.path.basename(base_file)})")
        for v in VARIANTS:
            print(f"    {v:5s} {cur[v]}")
        return
    old = json.load(open(base_file, encoding='utf-8'))
    for v in VARIANTS:
        o, c = old.get(v), cur.get(v)
        if o is None and c is not None:
            print(f"  [ OK ] T6 {v} was broken, now {c['mean']:.2f} mm")
            continue
        if c is None:
            check(f"T6 {v} still produces a valid export", False, "export unparseable")
            continue
        check(f"T6 {v} no accuracy regression", c['mean'] <= o['mean'] + 0.1,
              f"{o['mean']:.2f} -> {c['mean']:.2f} mm")


# ---------------------------------------------------------------- T7
def t7_euler_convention():
    """Rotate a contour by a known amount, then recover it the way step05 does.

    This is the check T3 cannot make. T3 hands step05 a delta and verifies it against
    the same formula step05 applies, so a wrong convention would agree with itself.
    Here the angles make a full round trip: applied to real geometry, then extracted
    back through the Kabsch + euler path used for gt_delta_3d. Before the fix,
    extraction used extrinsic 'zyx' while application used intrinsic 'ZYX' - a
    different composition, worth ~0.4 mm mean on this contour."""
    print("\nT7  Euler convention survives an apply -> extract round trip")
    C, _ = gt_program('v1').contour_xyz()
    pivot = C.mean(0)
    for ypr in [(1.4, 3.1, -2.5), (-0.6, 0.9, 0.3), (2.7, -4.4, 5.1)]:
        Rm = lsgeom.rot_from_ypr(*ypr)
        moved = Rm.apply(C - pivot) + pivot

        # the extraction path used by step05's gt_delta_3d
        ca, cb = C.mean(0), moved.mean(0)
        H = (C - ca).T @ (moved - cb)
        U, S, Vt = np.linalg.svd(H)
        rot = Vt.T @ U.T
        if np.linalg.det(rot) < 0:
            Vt[2, :] *= -1
            rot = Vt.T @ U.T
        back = lsgeom.ypr_from_rot(rot)

        err = max(abs(a - b) for a, b in zip(ypr, back))
        check(f"T7 yaw/pitch/roll {ypr} recovered", err < 1e-6,
              f"got {tuple(round(x, 4) for x in back)}, max error {err:.4f} deg")

        # and what that error would cost in millimetres on the real contour
        wrong = R.from_euler('zyx', list(ypr), degrees=True).apply(C - pivot) + pivot
        gap = float(np.linalg.norm(moved - wrong, axis=1).mean())
        NOTES.append(f"T7 {ypr}: wrong convention would cost {gap:.2f} mm")


if __name__ == '__main__':
    for v in VARIANTS:
        if not os.path.exists(os.path.join(sess_dir(v), 'step04_result.json')):
            sys.exit(f"missing results/audit_{v} - run tests/rebuild_sessions.py first")
    t1_structural()
    t2_identity()
    t3_roundtrip()
    t4_order_invariance()
    t4b_blend_betweenness()
    t5_whiskers()
    t6_regression()
    t7_euler_convention()
    print("\n" + "=" * 70)
    if NOTES:
        print("notes: " + " | ".join(NOTES))
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S):")
        for f in FAILURES:
            print("  - " + f)
        sys.exit(1)
    print("all checks passed")
