"""Frozen CAD-to-machine registration - replaces service_3030/exp_all_methods.py's
cad_start(), which read a live service_2020 scene.json. Reuses the existing
scene.placement_matrix() from service_2021's own scene.py (already identical math to
service_2020's copy) instead of duplicating it.

This is a fixed, one-time-calibrated starting pose for the optimizer, not recomputed
per variant - see ../calib/cad_placement/<name>/meta.json for provenance.
"""
import json
import os
import sys

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(BASE, '..')))
import scene as S  # noqa: E402

CALIB = os.path.abspath(os.path.join(BASE, '..', 'calib', 'cad_placement'))


def load(name):
    """(R0, t0) from calib/cad_placement/<name>/placement.json."""
    with open(os.path.join(CALIB, name, 'placement.json'), encoding='utf-8') as f:
        pl = json.load(f)
    T = np.array(S.placement_matrix(pl['rot_deg'], pl['translate'], pl['scale']))
    return T[:3, :3], T[:3, 3]
