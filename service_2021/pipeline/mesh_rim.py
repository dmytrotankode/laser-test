"""Load the reference STL and extract its bottom rim - vendored from
service_3030/exp_cad_fit.py (load_stl) and service_3030/export_scene.py (mesh_rim).

The rim is used by contour_fit.py as the rigid shape that gets posed against the photos;
it never changes per variant, only the STL file itself would.
"""
import struct
from collections import defaultdict

import numpy as np


def load_stl(path):
    b = open(path, 'rb').read()
    n = struct.unpack('<I', b[80:84])[0]
    tri = np.empty((n, 3, 3), np.float32)
    for i in range(n):
        tri[i] = np.frombuffer(b, np.float32, 9, 84 + i * 50 + 12).reshape(3, 3)
    return tri.astype(float)


def unique_vertices(path):
    """Every distinct vertex of the STL, for the silhouette bounding-box residual in
    contour_fit.py - not the rim, the whole mesh surface."""
    return np.unique(load_stl(path).reshape(-1, 3), axis=0)


def mesh_rim(stl_path, angle_deg=45):
    """The model's bottom edge - a real geometric feature, not sampled.

    The edge is a sharp fold in the surface: take edges whose two adjacent faces'
    normals diverge by more than `angle_deg` and collect them into connected loops.
    There are exactly two such loops at the bottom (inner and outer edge of the ~8mm
    wall); the outer one is where the cut lands.
    """
    tri = load_stl(stl_path)
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9

    own = defaultdict(list)
    for i, t in enumerate(np.round(tri, 3)):
        for a, b in ((0, 1), (1, 2), (2, 0)):
            own[tuple(sorted((tuple(t[a]), tuple(t[b]))))].append(i)
    lim = np.cos(np.radians(angle_deg))
    adj = defaultdict(set)
    for e, f in own.items():
        if len(f) == 2 and float(nrm[f[0]] @ nrm[f[1]]) < lim:
            adj[e[0]].add(e[1])
            adj[e[1]].add(e[0])

    seen, loops = set(), []
    for v in adj:
        if v in seen:
            continue
        stack, comp = [v], set()
        while stack:
            u = stack.pop()
            if u in comp:
                continue
            comp.add(u)
            seen.add(u)
            stack.extend(adj[u] - comp)
        if len(comp) > 50 and all(len(adj[u]) == 2 for u in comp):
            loops.append(comp)
    if not loops:
        raise ValueError('no closed fold-edge loops found')

    def radius(c):
        P = np.array(list(c))
        return np.hypot(P[:, 0] - P[:, 0].mean(), P[:, 1] - P[:, 1].mean()).max()
    low = min(np.array(list(c))[:, 2].mean() for c in loops)
    bottom = [c for c in loops if np.array(list(c))[:, 2].mean() < low + 30]
    comp = max(bottom, key=radius)

    start = next(iter(comp))
    order, prev, cur = [start], None, start
    while True:
        nxt = [u for u in adj[cur] if u != prev]
        if not nxt or nxt[0] == start:
            break
        prev, cur = cur, nxt[0]
        order.append(cur)
    return np.array(order, float)
