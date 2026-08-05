"""Refit the pose model, selecting everything by cross-validation on TRAIN only.

Two things are done differently from the shipped W_calib.

1. TRAINED ON PAIRS. The model is USED on differences - the current photo's features
   minus the chosen neighbour's, giving a pose delta relative to that neighbour - but it
   was FITTED on 11 absolute samples measured from one anchor. Training on all ordered
   pairs of training variants matches the deployment condition and turns 11 samples into
   110. The pairs are not independent, so cross-validation holds out a VARIANT and every
   pair that mentions it, never a single pair.

2. LABELS FROM CURVE ICP. The old labels came from index-wise Kabsch between .LS files,
   which is meaningless across the two archive batches (their point numbering differs by
   a full contour step) and was the source of the phantom ~11.5 deg yaw. Labels here come
   from correspondence-free ICP between the recorded contours, and use the single
   yaw/pitch/roll convention from lsgeom.

Hyperparameters (feature set, ridge lambda, pivot) are chosen by leave-one-variant-out
inside TRAIN. Held-out variants are scored once, at the end, by evaluate.py - they are
never read here; dataset.guard_training() enforces that.

    python scripts/fit_model.py              # compare candidates, print the table
    python scripts/fit_model.py --emit       # also write the winning constants
"""
import os
import sys
import json
import argparse
import numpy as np

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import lsgeom      # noqa: E402
import dataset     # noqa: E402
import features    # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------- geometry
ANCHOR = "v1"          # defines where "standoff = nominal" sits; only relative values matter
_PROG, _STANDOFF, _CUT = {}, {}, {}


def program(v):
    if v not in _PROG:
        _PROG[v] = lsgeom.load(os.path.join(BASE, 'input', 'archive', v,
                                            'ground_truth.ls'))
    return _PROG[v]


def _anchor_surface():
    return lsgeom.cut_surface(program(ANCHOR), lsgeom.NOMINAL_STANDOFF)[0]


def standoff(v):
    """Standoff of a recorded program, fitted from shape agreement with the anchor."""
    if v not in _STANDOFF:
        _STANDOFF[v] = (lsgeom.NOMINAL_STANDOFF if v == ANCHOR
                        else lsgeom.fit_standoff(program(v), _anchor_surface())[0])
    return _STANDOFF[v]


def contour(v):
    """The CUT LINE, not the nozzle path.

    Everything downstream - labels, cross-validation error, the do-nothing control -
    works on where the beam lands. The standoff is stripped because it is slack that
    does not move the cut (lsgeom, "standoff and the cut line"), and leaving it in
    would make the labels for v14-v16 express a 3.5-6.3 mm offset as a bogus pose."""
    if v not in _CUT:
        _CUT[v] = lsgeom.cut_surface(program(v), standoff(v))[0]
    return _CUT[v]


icp = lsgeom.icp

_T = {}


def transform_from_ref(v, ref):
    """Rigid transform taking the reference contour onto variant v's contour (cached).

    Pairwise poses are then compositions of these, not fresh ICP runs: the transform
    a -> b is T_b . T_a^-1 exactly, so 11 ICP fits cover all 110 ordered pairs."""
    if v not in _T:
        _T[v] = icp(contour(ref), contour(v))
    return _T[v]


def pose_between(a, b, pivot, ref):
    """6-DOF pose of variant b relative to variant a, expressed about `pivot`."""
    Ra, ta = transform_from_ref(a, ref)
    Rb, tb = transform_from_ref(b, ref)
    # x_b = Rb Rа^-1 (x_a - ta) + tb
    Rm = Rb @ Ra.T
    t = tb - Rm @ ta
    yaw, pitch, roll = lsgeom.ypr_from_rot(Rm)
    shift = Rm @ pivot + t - pivot
    return np.array([shift[0], shift[1], shift[2], roll, pitch, yaw])


def apply_pose(pts, p, pivot):
    return lsgeom.rot_from_ypr(p[5], p[4], p[3]).apply(pts - pivot) + pivot + p[:3]


# ---------------------------------------------------------------- model
def ridge(X, Y, lam):
    A = X.T @ X + lam * np.eye(X.shape[1])
    return np.linalg.solve(A, X.T @ Y)


def fit_pairs(names, F, kind, lam, POSE):
    """Least squares from feature DIFFERENCE to pose DIFFERENCE over all ordered pairs."""
    X, Y = [], []
    for a in names:
        for b in names:
            if a == b:
                continue
            X.append(features.vec(F[b], kind) - features.vec(F[a], kind))
            Y.append(POSE[(a, b)])
    X, Y = np.array(X), np.array(Y)
    sx = X.std(0)
    sx[sx < 1e-9] = 1.0
    return ridge(X / sx, Y, lam), sx


def predict(W, sx, F, kind, ref, cur):
    d = features.vec(F[cur], kind) - features.vec(F[ref], kind)
    return (d / sx) @ W


def nearest(v, pool, F, kind):
    """The neighbour DEPLOYMENT would pick, by the same rule step04 uses.

    step04 measures distance in the model's own feature space, divided by knn_scale
    (the per-feature spread across the library). Cross-validation used to rank by raw,
    unnormalised f8 distance instead - a different rule, so the "nearest" it scored was
    not always the one that ships. On v13 the two disagree (v9 against v5), which is
    enough to move the reported error. The scale is rebuilt from the fold's own training
    variants; taking it from the full library would leak the held-out one."""
    lib = np.array([features.vec(F[u], kind) for u in pool])
    scale = lib.std(0)
    scale[scale < 1e-9] = 1.0
    cur = features.vec(F[v], kind)
    d = {u: float(np.linalg.norm((cur - features.vec(F[u], kind)) / scale)) for u in pool}
    return min(d, key=d.get)


def loo_error(names, F, kind, lam, POSE, pivot):
    """Leave-one-VARIANT-out. Every pair mentioning the held-out variant is removed.

    Holding out a single pair would leak: 10 other pairs still mention both of its
    endpoints, so the model would have seen that variant's geometry."""
    per = {}
    for v in names:
        tr = [u for u in names if u != v]
        W, sx = fit_pairs(tr, F, kind, lam, POSE)
        Gv = contour(v)
        errs = []
        for ref in tr:
            p = predict(W, sx, F, kind, ref, v)
            errs.append(lsgeom.curve_distance(apply_pose(contour(ref), p, pivot), Gv).mean())
        # deployment picks the nearest neighbour, so score the nearest, not the average
        nb = nearest(v, tr, F, kind)
        per[v] = dict(nearest=float(errs[tr.index(nb)]),
                      mean_over_refs=float(np.mean(errs)),
                      best=float(np.min(errs)))
    return per


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--emit', action='store_true')
    a = ap.parse_args()

    names = dataset.guard_training(dataset.TRAIN)
    print(f"Обучающая выборка: {len(names)} вариантов -> {len(names) * (len(names) - 1)} пар")
    print(f"Held-out ({', '.join(dataset.HELDOUT)}) здесь не читается вообще.\n")

    F = features.load(names)

    pivots = {
        "старая (зашитая в step02)": np.array([1170.98, 785.15, -191.86]),
        "центроид контура": contour(names[0]).mean(0),
    }
    ref = names[0]
    print(f"Подгонка ICP каждого варианта к эталону ({len(names)} прогонов "
          f"на все {len(names) * (len(names) - 1)} пар)...")
    print(f"Отступ, подобранный по каждому варианту (мм): "
          + ", ".join(f"{v} {standoff(v):.2f}" for v in names))
    for v in names:
        transform_from_ref(v, ref)
    POSE = {}
    for label, piv in pivots.items():
        POSE[label] = {(x, y): pose_between(x, y, piv, ref)
                       for x in names for y in names if x != y}

    print(f"{'признаки':10s}{'точка поворота':28s}{'lambda':>9s}"
          f"{'LOO ближ.':>11s}{'LOO худш.':>11s}")
    results = []
    for kind in ("f8", "prof"):
        for label, piv in pivots.items():
            for lam in (0.1, 1, 10, 100, 1000):
                per = loo_error(names, F, kind, lam, POSE[label], piv)
                m = float(np.mean([r['nearest'] for r in per.values()]))
                w = float(np.max([r['nearest'] for r in per.values()]))
                results.append((m, w, kind, label, lam, piv))
                print(f"{kind:10s}{label:28s}{lam:9g}{m:11.2f}{w:11.2f}")

    # Pre-declared selection rule, so the choice is not made by eye: take the best LOO
    # mean, then among everything within 1% of it prefer the LARGEST lambda. Ties here
    # are genuine (prof is flat over four orders of magnitude), and the more regularised
    # model is the safer one to ship.
    best = min(r[0] for r in results)
    close = [r for r in results if r[0] <= best * 1.01]
    # The label is a deterministic final tie-break, nothing more. The two pivots score
    # identically to the last digit, so without it max() would return whichever the loop
    # happened to visit first and the shipped pivot would flip between runs for no
    # reason. Ordering ascending keeps the long-standing choice; a pivot change is not
    # free (it moves every exported point) and nothing here argues for one.
    m, w, kind, label, lam, piv = max(close, key=lambda r: (r[4], [-ord(c) for c in r[3]]))
    print(f"\nЛучшее по LOO: признаки={kind}, точка поворота={label}, lambda={lam} "
          f"-> {m:.2f} мм в среднем, {w:.2f} мм в худшем случае")

    # internal control inside the same protocol: what if we predicted nothing at all
    zero = []
    for v in names:
        tr = [u for u in names if u != v]
        nb = nearest(v, tr, F, kind)
        zero.append(float(lsgeom.curve_distance(contour(nb), contour(v)).mean()))
    print(f"Контроль «ничего не делать» (траектория ближайшего соседа как есть): "
          f"{np.mean(zero):.2f} мм в среднем, {np.max(zero):.2f} мм в худшем — "
          f"выигрыш модели {np.mean(zero) / m:.2f}x")

    if a.emit:
        W, sx = fit_pairs(names, F, kind, lam, POSE[label])
        # k-NN distance scale and the out-of-range threshold, both in the feature space
        # the model actually uses. The shipped threshold (6.43) was computed for the old
        # f8 space and never fired on the real out-of-library poses: v6 sat at 2.47 and
        # v13 at 4.35, both well under it.
        V = {v: features.vec(F[v], kind) for v in names}
        knn_scale = np.array([features.vec(F[v], kind) for v in names]).std(0)
        knn_scale[knn_scale < 1e-9] = 1.0
        gaps = []
        for v in names:
            gaps.append(min(float(np.linalg.norm((V[v] - V[u]) / knn_scale))
                            for u in names if u != v))
        # Threshold = the largest nearest-neighbour gap inside the library, with NO
        # safety multiplier. Beyond it, the new photo is further from every calibrated
        # pose than any calibrated pose is from its own neighbour - that is the
        # definition of extrapolating, and it is exactly the regime where the error
        # stops being explained by the standoff and starts being real.
        # The shipped threshold multiplied this gap by 1.5 "for safety", which inverted
        # its purpose: it never fired on the one variant that genuinely was outside.
        threshold = float(max(gaps))
        print(f"Порог out_of_range = наибольший разрыв до соседа внутри библиотеки: "
              f"{threshold:.2f} (без множителя — см. комментарий)")

        anchor = names[0]
        out = dict(feature_kind=kind, lam=lam, pivot=[float(x) for x in piv],
                   scale=[float(x) for x in sx], W=[[float(x) for x in row] for row in W],
                   train=names, loo_nearest_mean=m, loo_nearest_worst=w,
                   loo_do_nothing_mean=float(np.mean(zero)),
                   knn_scale=[float(x) for x in knn_scale],
                   out_of_range_threshold=threshold,
                   anchor=anchor,
                   # Poses live in CUT-LINE space now, so step05 must strip the
                   # neighbour's standoff before applying them and re-apply the nominal
                   # one afterwards. Recorded per variant so the export never has to
                   # re-fit it, and so a drift in these numbers is visible in git.
                   coordinates="cut_line",
                   nominal_standoff=lsgeom.NOMINAL_STANDOFF,
                   standoff={v: float(standoff(v)) for v in names},
                   library={v: dict(feat=[float(x) for x in V[v]],
                                    pose_vs_anchor=[float(x) for x in POSE[label][(anchor, v)]]
                                    if v != anchor else [0.0] * 6)
                            for v in names})
        p = os.path.join(BASE, 'input', 'model_pose.json')
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=2)
        print(f"Записано в {p}")


if __name__ == '__main__':
    main()
