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

# Delivered 10.08, photographed 07-08.08. Six different physical helmets off moulds 1
# and 4 - the first sets in the project that are NOT the master helmet, and the first
# whose results nobody has looked at. That makes them the only genuinely blind estimate
# available: v6 and v13 are mechanically clean but their numbers have been read many
# times, so they no longer measure anything independent.
#
# Deliberately NOT part of ALL. ALL means "the archive the model was built on", and
# tests/test_standoff.py carries a per-variant table over it. These are inputs the
# pipeline is run against, not archive members - but they must never be fitted on,
# hence guard_training() covers them too.
BLIND = ["v20", "v21", "v22", "v23", "v24", "v25"]

# Of those six, the three that may be folded into the library ON PURPOSE, to test whether
# widening the pose coverage helps. The split is formal - every second set in capture
# order - and was fixed BEFORE any result was looked at, so that it could not be chosen
# to flatter the outcome; both moulds land on both sides (mould 4 is v22 and v23).
#
# Folding them in costs their blindness, which is why it is opt-in: fit_model only
# accepts them with --augment, and the result goes to a SEPARATE model file so the
# shipped one is never silently replaced. v21/v23/v25 stay out of fitting entirely.
#
# Measured (PLAN section 4d): on v21/v23/v25 the error drops 4.29 -> 2.67 mm, while
# leave-one-out inside the original 14 barely moves (1.23 -> 1.26).
AUGMENT = ["v20", "v22", "v24"]

assert set(AUGMENT) <= set(BLIND)

assert set(TRAIN) | set(HELDOUT) | set(PENDING) == set(ALL)
assert not (set(TRAIN) & set(HELDOUT))
assert not (set(BLIND) & set(ALL))


def guard_training(names, allow=()):
    """Raise if a fitting routine is about to consume a held-out or blind variant.

    `allow` is the deliberate exception - currently only AUGMENT, and only when the
    caller asked for it explicitly on the command line. Everything else still raises.
    """
    leaked = sorted((set(names) & (set(HELDOUT) | set(BLIND))) - set(allow))
    if leaked:
        raise RuntimeError(
            f"held-out variant(s) {leaked} used for fitting. They exist to give an "
            f"honest error estimate; touching them here - even to pick a "
            f"hyperparameter - destroys that. See scripts/dataset.py.")
    return list(names)
