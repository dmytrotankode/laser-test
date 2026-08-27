"""k-NN neighbor selection + per-variant standoff fitting - vendored from
service_5056/scripts/fit_model.py (program/standoff/nearest only - the ridge-regression
training code in fit_model.py is NOT on the production hot path, see
service_2021/README.md; it is not ported here).

Reads recorded programs from ../archive/<variant>/ground_truth.ls instead of
service_5056/input/archive/.
"""
import os

import numpy as np

from . import features
from . import geometry

BASE = os.path.dirname(os.path.abspath(__file__))
ARCHIVE = os.path.abspath(os.path.join(BASE, '..', 'archive'))

ANCHOR = "v1"          # defines where "standoff = nominal" sits; only relative values matter
_PROG, _STANDOFF = {}, {}


def program(v):
    if v not in _PROG:
        _PROG[v] = geometry.load(os.path.join(ARCHIVE, v, 'ground_truth.ls'))
    return _PROG[v]


def _anchor_surface():
    return geometry.cut_surface(program(ANCHOR), geometry.NOMINAL_STANDOFF)[0]


def standoff(v):
    """Standoff of a recorded program, fitted from shape agreement with the anchor."""
    if v not in _STANDOFF:
        _STANDOFF[v] = (geometry.NOMINAL_STANDOFF if v == ANCHOR
                        else geometry.fit_standoff(program(v), _anchor_surface())[0])
    return _STANDOFF[v]


def own_ring(v, extra=0.0):
    """A recorded variant's own cut ring (for parity/report comparisons only), shifted
    an extra `extra` mm along the tool axis."""
    prog = program(v)
    P, ids = geometry.cut_ring(prog)
    axes = geometry.tool_axes(prog, ids)
    return np.asarray(P, float) - (standoff(v) + extra) * np.asarray(axes, float)


def nearest(v, pool, F, kind):
    """The neighbor variant `v` is templated from, by the same rule the deployed
    pipeline uses: distance in the feature space, normalized by the pool's own spread."""
    lib = np.array([features.vec(F[u], kind) for u in pool])
    scale = lib.std(0)
    scale[scale < 1e-9] = 1.0
    cur = features.vec(F[v], kind)
    d = {u: float(np.linalg.norm((cur - features.vec(F[u], kind)) / scale)) for u in pool}
    return min(d, key=d.get)
