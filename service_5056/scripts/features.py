"""Pixel features of the three camera views, with an on-disk cache.

Two sets are produced for every archive variant:

  "f8"    the 8 scalars the shipped model uses: per view, the mask centroid (cx, cy)
          plus, for two of the views, the topmost dome row. Cheap, but thin: three of
          the eight are quantised to ~9-10 px steps by the stand-stripping loop, which
          leaves them with 3-5 distinct levels across all 16 samples.

  "prof"  the same two centroid numbers per view plus a 48-bin radial profile of the
          silhouette, sampled at fixed angles around the mask centroid. Same photos,
          same segmentation - it just stops throwing away the outline.

Cached in results/_features.json keyed by variant, because segmentation costs ~1.6 s
per image and the cache is only invalidated when the photos change.
"""
import os
import json
import numpy as np
import cv2

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CACHE = os.path.join(BASE, 'results', '_features.json')
N_BINS = 48
VIEWS = (("back", False), ("left", False), ("top", True))


def _measure(variant):
    from step03_segment_monochrome import segment_image
    f8, prof = [], []
    for name, is_top in VIEWS:
        path = os.path.join(BASE, 'input', 'archive', variant, f'{name}.png')
        mask, _, _, _, _ = segment_image(path, is_top)
        M = cv2.moments(mask)
        cx, cy = M["m10"] / M["m00"], M["m01"] / M["m00"]
        clipped = mask.copy()
        clipped[:100, :] = 0
        top_y = float(np.min(np.where(clipped > 0)[0]))
        f8.append((cx, cy, top_y))

        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        c = max(cnts, key=cv2.contourArea)[:, 0, :].astype(float)
        ang = np.arctan2(c[:, 1] - cy, c[:, 0] - cx)
        rad = np.hypot(c[:, 0] - cx, c[:, 1] - cy)
        o = np.argsort(ang)
        grid = np.linspace(-np.pi, np.pi, N_BINS, endpoint=False)
        prof.append([cx, cy] + list(np.interp(grid, ang[o], rad[o], period=2 * np.pi)))
    return {"f8": f8, "prof": prof}


def load(variants, rebuild=False):
    """{variant: {"f8": [...], "prof": [...]}} for the requested variants."""
    cache = {}
    if os.path.exists(CACHE) and not rebuild:
        with open(CACHE, encoding='utf-8') as f:
            cache = json.load(f)
    missing = [v for v in variants if v not in cache]
    for v in missing:
        print(f"  segmenting {v} ...", flush=True)
        cache[v] = _measure(v)
    if missing:
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        with open(CACHE, 'w', encoding='utf-8') as f:
            json.dump(cache, f)
    return {v: cache[v] for v in variants}


def vec(entry, kind):
    """Flatten one variant's features into a plain vector."""
    if kind == "f8":
        b, l, t = entry["f8"]
        return np.array([b[0], b[1], l[0], l[1], l[2], t[0], t[1], t[2]], dtype=float)
    if kind == "prof":
        return np.array([x for row in entry["prof"] for x in row], dtype=float)
    raise ValueError(kind)
