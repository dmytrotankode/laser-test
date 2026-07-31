"""Single source of truth for the train / held-out split.

Any script that FITS anything (regression weights, k-NN library, thresholds,
hyperparameters) must import TRAIN from here and call guard_training() with whatever
it is about to touch. Held-out variants have leaked into hyperparameter selection once
already - round 3 of W_calib picked its weighting by looking at v6/v13 error - so the
split is enforced in code rather than left to comments.

Evaluation may read HELDOUT. Fitting may not.
"""

ALL = [f"v{i}" for i in range(1, 17)]

# Fitting set. One physical master helmet in 11 different placements on the stand.
TRAIN = ["v1", "v2", "v3", "v4", "v5",
         "v7", "v8", "v9", "v10", "v11", "v12"]

# Never used for fitting, under any circumstance, including hyperparameter choice.
# Kept as the customer's independent check: v6 comes from the old capture batch,
# v13 from the new one, so between them they cover both.
HELDOUT = ["v6", "v13"]

# Usable data, currently parked. Their recorded trajectories carry a constant offset
# along the nozzle axis (v14 ~3.7 mm, v15/v16 ~6.4 mm) that no rigid pose model can
# express. Whether that offset is a real standoff change or a re-taught UTOOL decides
# how to handle it, and that is question Q1 to the customer - see PLAN.md section 4.
# They were previously discarded as "unreliable data", which was wrong.
PENDING = ["v14", "v15", "v16"]

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
