"""Manual fold-line marks -> per-variant arrays - vendored from
service_3030/line_features.py's load_marks(), reading from ../lines/ instead of
service_3030/data/lines/.

Cameras are fixed, so the line is kept directly in frame pixels (no normalization) -
mapping it onto the silhouette would remove exactly the signal this is for: where the
line sits relative to the dome.
"""
import glob
import json
import os

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
LINES = os.path.abspath(os.path.join(BASE, '..', 'lines'))


def _mark_name(stem):
    """'shop_05.08_left' -> ('shop_05.08', 'left'). Variant names may contain '_'."""
    variant, view = stem.rsplit('_', 1)
    return variant, view


def load_marks():
    """{variant: {view: Nx2 array}} from ../lines/*.json."""
    out = {}
    for f in sorted(glob.glob(os.path.join(LINES, '*.json'))):
        pts = json.load(open(f, encoding='utf-8')).get('points', [])
        if len(pts) < 3:
            continue
        variant, view = _mark_name(os.path.basename(f)[:-5])
        p = np.array(sorted(pts, key=lambda q: q[0]), float)
        out.setdefault(variant, {})[view] = p
    return out
