"""Generate a cut-line .LS for a variant, from a named recipe - the single entry point
callers should use. Ported from service_3030/export_cad_ls_contour.py's export()/main(),
same algorithm, reading only from this service's own calib/archive/lines/ directories
via the recipe (see calib/recipes/<name>.json and service_2021/README.md).

    from pipeline.generate import generate
    path, report = generate('v21', 'production_2026-08-27')
"""
import json
import os

import cv2
import numpy as np
from scipy.optimize import least_squares

from . import cad_placement
from . import contour_fit
from . import geometry
from . import line_marks
from . import ls_template
from . import mesh_rim
from . import neighbor
from . import features as features_mod

BASE = os.path.dirname(os.path.abspath(__file__))
SERVICE_ROOT = os.path.abspath(os.path.join(BASE, '..'))
CALIB = os.path.join(SERVICE_ROOT, 'calib')
ARCHIVE = os.path.join(SERVICE_ROOT, 'archive')
MODEL_3D = os.path.join(SERVICE_ROOT, 'data', 'model_3d', 'helmet_ref.stl')
OUT = os.path.join(SERVICE_ROOT, 'data', 'generated')


def load_recipe(name):
    with open(os.path.join(CALIB, 'recipes', f'{name}.json'), encoding='utf-8') as f:
        return json.load(f)


def load_library(name):
    with open(os.path.join(CALIB, 'libraries', name, 'variants.json'), encoding='utf-8') as f:
        return json.load(f)


def has_ground_truth(variant):
    return os.path.exists(os.path.join(ARCHIVE, variant, 'ground_truth.ls'))


def generate(variant, recipe_name):
    """Returns (path_to_LS, report_dict). report_dict is comparison stats against the
    recorded program, only present when the variant has a ground_truth.ls (a genuinely
    new, never-cut helmet has nothing to compare against - that's expected, not an error).
    """
    recipe = load_recipe(recipe_name)
    lib = load_library(recipe['neighbor_library'])
    fold_radial = recipe['constants']['fold_radial_mm']
    fold_up = recipe['constants']['fold_up_mm']
    feature_kind = recipe['feature_kind']
    # nominal_standoff_mm is recorded for documentation/traceability, but the export
    # path always uses geometry.NOMINAL_STANDOFF (matching the ported original exactly,
    # which hardcoded it too) - assert instead of silently diverging if a recipe ever
    # names a different value.
    assert recipe['constants']['nominal_standoff_mm'] == geometry.NOMINAL_STANDOFF, (
        "recipe's nominal_standoff_mm differs from geometry.NOMINAL_STANDOFF - "
        "the export path does not actually use the recipe value yet, see generate.py")

    calib_dir = os.path.join(CALIB, 'cameras', recipe['camera_calibration'])
    cams = contour_fit.marker_cams(calib_dir)
    R0, t0 = cad_placement.load(recipe['cad_placement'])
    rim = mesh_rim.mesh_rim(MODEL_3D)
    verts = mesh_rim.unique_vertices(MODEL_3D)
    marks = line_marks.load_marks()

    neighbor_pool = [u for u in lib['neighbor_pool'] if u != variant]
    feature_pool = list(lib['feature_pool'])
    for v in feature_pool:
        neighbor.standoff(v)
    if has_ground_truth(variant):
        neighbor.standoff(variant)
    F_all = features_mod.load(feature_pool + [v for v in [variant] if v not in feature_pool])

    r = least_squares(
        contour_fit.resid_of(ARCHIVE, variant, rim, verts, marks, cams, R0, t0,
                             fold_radial, fold_up),
        np.r_[np.zeros(6), 12.0], method='lm', max_nfev=900)
    R = cv2.Rodrigues(r.x[:3])[0] @ R0
    P = rim @ R.T + t0 + r.x[3:6]

    nb = neighbor.nearest(variant, neighbor_pool, F_all, feature_kind)
    src = os.path.join(ARCHIVE, nb, 'ground_truth.ls')
    tmpl = geometry.load(src)
    st = neighbor.standoff(nb)
    cut_full, ids_full = geometry.cut_surface(tmpl, st, full=True)
    axis_by_id = dict(zip(ids_full, geometry.tool_axes(tmpl, ids_full)))
    cut_by_id = dict(zip(ids_full, np.asarray(cut_full, float)))

    def on_cad(pt):
        return P[int(np.argmin(np.linalg.norm(P - pt, axis=1)))]

    def point_fn(point_id, orig_xyz):
        if point_id not in cut_by_id:
            return None
        return on_cad(cut_by_id[point_id]) + geometry.NOMINAL_STANDOFF * axis_by_id[point_id]

    # Program names are Fanuc-limited to 17 chars (geometry.program_name truncates), so
    # the recipe name is NOT guaranteed to survive in the file/program name - only use
    # it for a same-recipe rerun sanity check, not to distinguish recipes by filename.
    # `report`/callers should track which recipe produced which path themselves.
    out_path = ls_template.write_ls(src, OUT, point_fn, f'cadc_{variant}')

    report = None
    if has_ground_truth(variant):
        back = geometry.load(out_path)
        got, _ = geometry.cut_surface(back, geometry.NOMINAL_STANDOFF)
        own = neighbor.own_ring(variant, 0.0)
        nb_as_is = neighbor.own_ring(nb, 0.0)
        d = geometry.curve_distance(got, own)
        dz = geometry.curve_distance(nb_as_is, own)
        report = dict(
            recipe=recipe_name, neighbor=nb, skirt_mm=float(r.x[6]),
            mean_mm=float(d.mean()), max_mm=float(d.max()),
            within_2mm_pct=float(100 * np.mean(d <= 2)),
            neighbor_as_is_mean_mm=float(dz.mean()), neighbor_as_is_max_mm=float(dz.max()))
    return out_path, report
