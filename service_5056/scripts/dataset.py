"""Single source of truth for the train / held-out split.

Any script that FITS anything (regression weights, k-NN library, thresholds,
hyperparameters) must import TRAIN from here and call guard_training() with whatever
it is about to touch. Held-out variants have leaked into hyperparameter selection once
already - round 3 of W_calib picked its weighting by looking at v6/v13 error - so the
split is enforced in code rather than left to comments.

Evaluation may read HELDOUT. Fitting may not.
"""

ALL = [f"v{i}" for i in range(1, 17)]

# Fitting set. One physical master helmet in 14 different placements on the stand.
TRAIN = ["v1", "v2", "v3", "v4", "v5",
         "v7", "v8", "v9", "v10", "v11", "v12",
         "v14", "v15", "v16"]

# Never used for fitting, under any circumstance, including hyperparameter choice.
# Kept as the customer's independent check: v6 comes from the old capture batch,
# v13 from the new one, so between them they cover both.
HELDOUT = ["v6", "v13"]

# Empty since 04.08. v14-v16 were parked because their recorded trajectories carry a
# constant offset along the nozzle axis (v14 ~3.5 mm, v15/v16 ~6.3 mm) that no rigid
# pose model can express, and it was unclear whether that was a real standoff change
# or a re-taught UTOOL.
#
# Both readings turned out not to matter. The customer confirmed the tool was never
# re-taught, and - more importantly - that the standoff is slack rather than a setpoint:
# 10 / 8 / 5 mm make no visible difference to the cut. Since the beam runs along the
# tool axis, sliding the nozzle along it does not move the cut point at all, so the
# offset never affected the product. Working in cut-line coordinates removes it
# outright: with the standoff fitted per variant, v14-v16 match the rest of the archive
# to 0.52-0.59 mm, i.e. as well as any training variant. See PLAN.md sections 2 and 4.
PENDING = []

assert set(TRAIN) | set(HELDOUT) | set(PENDING) == set(ALL)
assert not (set(TRAIN) & set(HELDOUT))


def guard_training(names):
    """Raise if a fitting routine is about to consume a held-out variant."""
    leaked = sorted(set(names) & set(HELDOUT))
    if leaked:
        raise RuntimeError(
            f"held-out variant(s) {leaked} used for fitting. They exist to give an "
            f"honest error estimate; touching them here - even to pick a "
            f"hyperparameter - destroys that. See scripts/dataset.py.")
    return list(names)
