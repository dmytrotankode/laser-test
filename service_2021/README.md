# service_2021 — operator correction tool

Web tool for a human operator to correct a computed helmet cut-line trajectory
by hand before it goes to the robot, and export the corrected `.LS`.

## Why this exists

The upstream pipeline (`service_3030`, `service_5056`) computes a cut line
from camera photos of a helmet, but that computation is not perfect on
helmet forms it wasn't tuned on (measured 21–83% of points within 2mm across
different forms — see git log of this repo for the numbers). A real historical
correction (V6→V6_2, 05.08) showed only ~26% of what the operator changed is
explained by a rigid whole-line shift; the rest is local, per-point. So this
service exists to let a human do that local correction efficiently, and to
record which points were actually touched (for possible future learning from
corrections — see "Future ideas" below).

## Hard architectural rule: fully self-contained

**This service must never import code from `service_3030` or `service_5056`.**
Those services get refactored/renamed independently and have broken files
this service depended on before (that's why this rule exists — not
theoretical). It has its own minimal parsers instead:

- `ls_points.py` — parses `.LS` text directly (regex), no dependency on
  `lsgeom.py`/`export_ls.py` from other services. Verified once against
  `lsgeom.cut_surface()` — exact 0.0mm match across 97 points.
- Camera format: a `.npy` of exactly 7 floats
  `[rvec(3), position(3), focal_px]`, loaded with plain `numpy.load`.

Any file this service reads from another service (a `.LS`, a `.npy`, a photo)
is copied into `data/scenes/<variant>/` at build time — after that, this
service never touches the original again.

**As of 2026-08-27 this rule also covers the computation itself.** The
generation pipeline that used to live in `service_3030`/`service_5056`
(camera-fit optimizer, k-NN neighbor selection, segmentation) has been
vendored into `pipeline/`, with its own copies of the input data in
`calib/`/`archive/`/`lines/`. `service_3030`, `service_5056`, `service_2020`,
and `laserdot_2` are **frozen, not deleted** — their code and history stay on
disk/in git for reference, but nothing here imports or runs them anymore, and
they should not be developed further. See "The computation pipeline" below.

## The computation pipeline (`pipeline/`, `calib/`, `archive/`, `lines/`)

This is a vendored, verified port of `service_3030/export_cad_ls_contour.py`
(the best-known method as of the port date) — same algorithm, same numbers,
just no longer importing another service's code. **Numerically verified**:
`calib/parity_report_2026-08-27.json` compares this pipeline's output against
the untouched old one for every archive variant that has a recorded program —
21 of 22 matched to exactly 0.0mm (the 22nd, `v2`, has no manual line marks in
either pipeline and was never a valid target — not a bug). Re-run the check
with `python -m pipeline.parity_check <variants...>` from `service_2021/` if
you ever touch a file in `pipeline/`.

```
pipeline/
├── geometry.py        ICP, cut_surface, fit_standoff, tool_axes — the
│                       optimizer/training math (from lsgeom.py). Deliberately
│                       SEPARATE from ../ls_points.py: that one is the
│                       viewer's naive/robust parser for ANY .LS (including
│                       operator-corrected ones this pipeline never produced);
│                       this one does ICP shape-alignment and traversal-order
│                       parsing that the viewer has no reason to need. Both
│                       independently implement the same W/R-swapped tool-axis
│                       convention — that duplication is intentional, not an
│                       oversight (see ls_points.py's own docstring).
├── ls_template.py     Regex substitution of X/Y/Z into a neighbor's .LS text;
│                       computes the Fanuc-safe program name ONCE and uses it
│                       for both the file name and the in-file /PROG field
│                       (they must match or the controller refuses to load it).
├── mesh_rim.py         Loads the reference STL, extracts its bottom rim (a
│                       real geometric edge-angle feature) and its full unique
│                       vertex set (used for a silhouette bounding-box check).
├── camera_model.py     Pinhole projection, near-side arc selection, and the
│                       signed point-to-polyline distance for line-mark
│                       residuals. Pure math, no I/O.
├── segmentation.py     rembg-based silhouette segmentation. Isolated on
│                       purpose — it's the most fragile external dependency
│                       (model download, onnxruntime), so "did segmentation
│                       change" is always a one-file diff against this module.
├── features.py         Pixel features (centroid + radial silhouette profile)
│                       per variant, cached to calib/_features_cache.json.
├── line_marks.py        Reads manual fold-line marks from ../lines/*.json.
├── contour_fit.py       THE ALGORITHM: builds the residual function for
│                       scipy.optimize.least_squares (line-mark distance +
│                       silhouette bounding-box + top-view contour distance).
│                       FOLD_RADIAL/FOLD_UP are passed in from the recipe, not
│                       hardcoded, so a recipe can pin a different measured
│                       offset for comparison without editing this file.
├── neighbor.py          k-NN neighbor selection + per-variant standoff
│                       fitting. Does NOT include the ridge-regression model
│                       (fit_model.py's W_calib) — verified by reading
│                       export_cad_ls_contour.py that the production method
│                       never uses it at all; only `standoff`/`nearest` are
│                       on the hot path.
├── cad_placement.py     Loads a frozen CAD-to-machine registration from
│                       calib/cad_placement/<name>/ (replaces a live read of
│                       service_2020's scene.json), via the existing
│                       scene.placement_matrix() already in ../scene.py.
├── generate.py           THE ENTRY POINT: generate(variant, recipe_name) ->
│                       (path, report). Everything else in pipeline/ is a
│                       building block this one assembles.
└── parity_check.py      Runs both pipelines on the same inputs and diffs the
                        result via ../ls_points.read_ring() — see above.
```

### Versioned calibrations/models + the recipe file

`calib/` holds versioned artifacts, never overwritten in place — a new
calibration run, a new neighbor-library selection, or a new CAD registration
each gets its own dated/named subfolder next to the old one, with a
`meta.json` recording what it is and where it came from:

```
calib/
├── cameras/<name>/{cam_back,cam_left,cam_top}.npy + meta.json
├── cad_placement/<name>/placement.json + meta.json
├── libraries/<name>/variants.json + meta.json   (k-NN neighbor pool)
├── ridge_models/                                 (optional, not on the hot path)
└── recipes/<name>.json
```

A **recipe** ties one of each together for a single generation run, plus the
physical constants, so the whole configuration that produced a given `.LS` is
one small, readable file:

```json
{
  "name": "production_2026-08-27",
  "camera_calibration": "marker_2026-08-21",
  "cad_placement": "v1_2026-08-27",
  "neighbor_library": "all_variants_2026-08",
  "constants": {"fold_radial_mm": -2.17, "fold_up_mm": 0.68, "nominal_standoff_mm": 10.0},
  "feature_kind": "prof"
}
```

**To test a new camera calibration or a restricted training library against
the current one**: drop the new calibration `.npy`s (or a new
`libraries/<name>/variants.json`) in their own named folder, copy
`recipes/production_2026-08-27.json` to a new name pointing at it, and run
`generate()` once per recipe for the same variant. Attach one result as a
reference on the other via the *existing* `attach_reference.py` — the
viewer's `эталон` comparison in `viewer.js::refStats()` doesn't care what
produced either curve, so the HUD's mean/max/%-in-tolerance numbers just work
as an A/B comparison with no new UI code.

### Known gap: brand-new, never-photographed helmets

`generate()` reads photos from `archive/<variant>/` and line marks from
`lines/<variant>_{back,left}.json` — both must already exist. There is
currently no vendored way to mark a NEW helmet's fold line (that tool,
`service_3030/app.py`, has not been ported — see "Future ideas"), so a
genuinely new variant still needs that old tool, and its photos still need to
be placed into `archive/<variant>/` by hand. This is a known, deliberate gap,
not an oversight.

## Key domain facts (don't relearn these)

- **`.LS` stores the NOZZLE path, not the cut line.** Cut line =
  `nozzle − 10.0mm (NOMINAL_STANDOFF) × tool_axis`, and `tool_axis` varies
  per point (~55–76° from vertical), so it's not a constant offset.
- **W/R are swapped** in the Fanuc convention used here:
  `tool_axis(w,p,r) = Rotation.from_euler('ZYX', [r,p,w]).apply([0,0,1])`
  — note `r` goes in the yaw slot and `w` in the roll slot. This looks like a
  bug if you don't know it's deliberate; it's verified against `lsgeom`.
- **First/last points in a `.LS` are usually lead-in/retract**, not part of
  the ring — `ls_points.read_ring()` drops them via nearest-neighbor-distance
  outlier filtering (>3× median).
- **A camera only sees ~half the ring** (near side of the dome); the far side
  is not self-occluded in code, it's classified by projected depth vs.
  median (`nearSideMask` in `viewer.js`). Points on the far side are dimmed
  and unselectable in that camera view — correcting them needs a different
  camera or the free-orbit view.
- **"Touched" ≠ "verified correct".** An operator only touches points that
  look bad enough to bother with. Untouched points are silently unverified,
  not confirmed good. Any future learning from corrections must filter to
  touched points only — this was a real, costly mistake to get wrong once.
- **Reference (`эталон`) curves are computed with the exact same formula as
  our curve** (same `ls_points.read_ring`, same standoff subtraction) — they
  are NOT derived from our camera calibration in any way. A reference line
  sitting well on the true fold line says the *reference program* (a human's
  prior correction) is good; it says nothing about our calibration by itself.
  Our calibration/algorithm quality is judged by comparing OUR curve against
  the reference, not by how good the reference looks alone.

## Data flow / one-way rule

`scene.json` is the only thing this service reads and writes at runtime.
Building one is a separate, explicit step — never triggered by opening the
page for an existing scene (that would erase corrections).

```
raw files (.LS, .npy, photos)  →  build_scene.py / discover.py  →  scene.json
                                                                       ↓
                                                              app.py (Flask)
                                                                       ↓
                                                         viewer.js (browser)
```

- `build_scene.py <variant> --ls ... --cam-* ... --photo-* ... [--reference ...]`
  — full (re)build from explicit paths. **Overwrites `scene.json` completely**,
  including any saved corrections. Use only for a variant that hasn't been
  corrected yet, or when you intend to discard corrections.
- `discover.py` — scans `incoming/<variant>/` for fixed filenames
  (`trajectory.LS`, `reference.LS` optional, `cam_back/left/top.npy`,
  `back/left/top.{jpg,png}`) and calls `build_scene.build()`, but **only for
  variants that don't have a `scene.json` yet** — never re-touches an
  existing scene. Runs automatically on every `/api/scenes` call (see
  `app.py`), so dropping a folder into `incoming/` and refreshing the page is
  enough.
- `attach_reference.py <variant> <path.LS>` — adds/replaces just the two
  reference curves on an **already-built** scene, without touching the
  editable curve or its `touched` history. Use this to add a reference after
  the fact, or after a `build_scene.py` rebuild accidentally dropped it (this
  has happened — a rebuild without `--reference` silently removes a
  previously-attached reference; if a variant should have one, re-run this
  after any full rebuild).
- `export_final.py` (also callable via `POST /api/scene/<name>/export`) —
  regenerates the final `.LS` from current (possibly corrected) points using
  `ls_points.write_points`.

## Nozzle path is computed live, not stored

The cut-line curve stores per-point `axes` (tool axis) alongside the points.
`viewer.js` computes the displayed nozzle path on the fly as
`point + 10mm * axis` every `draw()` call. It used to be a separately-stored
static curve, computed once at build time — that went stale (wrong) the
moment the operator edited a point, since the stored nozzle curve didn't
move with it. Don't reintroduce a stored nozzle curve for the editable line.
(Reference curves' nozzle path IS static — that's someone else's finished
program, nobody edits it, so staleness isn't a concern there.)

## Scenes directory layout

`data/scenes/<variant>/`:
- `scene.json` — read/written by `app.py`, source of truth for the UI.
- `template.ls` — copy of the original `.LS`, used as the text template
  `export_final.py` substitutes corrected coordinates into.
- `back.jpg` / `left.jpg` / `top.jpg` — background photos per camera view.
- `<variant>_final.LS` — appears after the operator exports (may not exist
  yet for an untouched scene).
- `reference_*.LS` (naming not fixed) — a reference `.LS` if one was
  attached, kept for traceability of what was compared against.

## Adding a new variant

Two ways:
1. Drop `incoming/<name>/` with the fixed filenames above and reload the
   page (or run `python discover.py`) — simplest, no arguments.
2. Call `build_scene.py` directly when your source files don't match the
   fixed `incoming/` naming.

Camera calibration currently used for production variants (v21–v26) is the
marker-based one, now at `calib/cameras/marker_2026-08-21/`.

## Group (bulk) edit math, if touching `buildGroupEditor()` in viewer.js

Rotation and translation totals are **additive** (each click's delta is
independent of the running total, so `target - totals[i]` is the right delta
to apply for a typed value). Scale is **multiplicative** (100% baseline,
each click/typed target needs `target / totals.scale` as the relative factor
applied to the *current* points, not the original ones) — don't copy the
rotate/translate delta pattern for scale, it'll double up incorrectly.
`buildGroupEditor()` must be called after `gundo` and `gsave` (not just
`draw()`) or the displayed totals go stale relative to the actual points —
this was a real bug once.

## UI: step wizard + Ukrainian (done 2026-08-28)

The sidebar is a collapsible step wizard (`.wiz`/`.wstep`/`.whead`/`.wbody` in
`index.html`, `wizExpand()`/`refreshWizard()` in `viewer.js`) — only one step
open at a time:
1. **Набір** — pick a built scene, or type a not-yet-built variant name into
   `#rawname` to check/generate it (reads `/api/pipeline/status/<name>`).
2. **Вхідні дані** — ✓/✗ checklist for `archive/<name>/{back,left,top}.png`;
   "Розрахувати" calls `POST /api/generate/<name>` (disabled until photos AND
   marks both exist) and reloads the resulting scene.
3. **Розмітка лінії згину** — ✓/✗ for `lines/<name>_{back,left}.json`. Honest
   about the known gap (see above): if marks are missing, says so and points
   at the old `service_3030/app.py` tool rather than pretending to offer one.
4. **Доведення та вивантаження** — the original point/group correction UI,
   unchanged, just moved under this step. Auto-expanded once a scene loads.

The whole UI (`index.html`, `viewer.js`'s dynamic strings, and the curve
names/scene notes `build_scene.py` generates) is in Ukrainian. Existing
scenes built before this date had their stored curve names migrated in place
(a rename-only edit of `scene.json`, touching nothing else — no
`points`/`touched` data was altered). Code comments were deliberately left as
they were (Russian/English) — this only covers what a user actually sees.

Open item, still not done: the marking tool itself (`service_3030/app.py`)
is not vendored, so step 3 can only report status, not let an operator draw a
new line here. Vendoring it would mean either duplicating its logic into this
service (keeping the self-containment rule above) or accepting a
one-directional read-only dependency — decide deliberately before starting.
