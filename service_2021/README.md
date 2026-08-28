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

### Marking the fold line (`pipeline/detect.py`, `mark.js`, step 3 of the wizard)

`generate()` reads photos from `archive/<variant>/` and line marks from
`lines/<variant>_{back,left}.json` — both must exist before it can run. The
marking tool itself (originally `service_3030/app.py` + `detect.py`) is now
vendored: `pipeline/detect.py` is an unchanged copy of the auto-detect
algorithm (dynamic-programming trace of the dark fold-line band, plus a
gradient-refined edge estimate — see its own docstring for why), and
`web/static/js/mark.js` is the 2D pan/zoom/click marking canvas, opened as a
full-screen overlay from wizard step 3 (`#markOverlay` in `index.html`). It
writes the exact same `lines/<variant>_<view>.json` format `line_marks.py`
already reads, so nothing downstream needed to change.

Routes (`app.py`): `GET /mark/img/<variant>/<view>.jpg` (serves the archive
photo as JPEG for the canvas), `GET /api/mark/detect`, `GET /api/mark/profile`
(brightness cross-section, for judging where the trench floor really is),
`GET|POST /api/mark/lines/<variant>/<view>`, `GET /api/mark/compare` (manual
marks vs. the auto-detector, median/p90/bias in px and mm). These are
deliberately separate from the older `/api/scene/...` routes — marking has
nothing to do with a built scene, only with `archive/`+`lines/`.

### Uploading photos (`POST /api/upload/<name>/<kind>`, done 2026-08-28)

Closes the gap above: `kind` is one of `back`/`left`/`top`/`reference`, body
is a single `multipart/form-data` file field named `file`. The original
filename is never kept — output is always `archive/<name>/{back,left,top}.png`
or `archive/<name>/ground_truth.ls` — so it doesn't matter that camera
exports arrive with arbitrary/wrong names, or that a reference `.LS` has some
unrelated name too.

Two input shapes are accepted for photos, both ending up as a plain PNG:
- A normal image (`.png`/`.jpg`/...) — decoded with `cv2.imdecode` and
  re-saved as PNG.
- A raw sensor dump named like `..._w4096_h3000_pMono8.raw` — 8-bit
  grayscale, one byte per pixel, **no header** (`numpy.frombuffer(data,
  dtype=np.uint8).reshape(h, w)`; `w`/`h` parsed from the filename via
  `_RAW_RE`, falling back to 4096×3000 if the filename doesn't match). This
  matches every `.raw` capture seen in this project so far (confirmed against
  `scratch_convert_new_variants.py`, `import_test1.py`, `capture.py` — none
  of which exposed a reusable function, so this is a fresh implementation of
  the same well-established format, not a call into existing code).

`name` is validated (`_safe_name`, `^[A-Za-z0-9_.-]{1,64}$`) before it ever
reaches a file path — needed once user-chosen names started driving file
writes, not just reads.

**Frontend: a dedicated "Новий набір" modal (`#newsetOverlay`), not inline
fields in step 1.** The first version put a single kind-picker + file-input
directly in step 1's body, defaulting to `currentTargetName()` (which falls
back to whatever scene is currently loaded, `sceneName`, when the free-text
name field is empty). That is a real bug, not just confusing UI — with an
existing scene selected and the name field empty, an upload silently landed
in *that* scene's `archive/<name>/`, overwriting its real photo (this
happened for real during testing: `archive/v21/back.png` got re-saved from a
test upload; harmless in that instance only because PNG re-encoding is
lossless and the uploaded file happened to be the same photo, dimensions and
all — a different file would have destroyed it with no backup, since
`archive/` is gitignored). The modal has its own `#ns_name` field, entirely
independent of `sceneName`/`#rawname`, and shows all of back/left/top/eталон
at once (back/left/top marked required with `*`) so there is no shared state
between "what's open in the viewer" and "what I'm uploading" for a mistake to
use. `web/static/js/mark.js`'s `#markOverlay` was already this shape (a
full-screen modal decoupled from the main sidebar) — `#newsetOverlay` follows
the same pattern rather than inventing a second one.

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
   `#rawname` to check its status. A separate "+ Новий набір" button opens
   the upload modal (`#newsetOverlay`, its own `#ns_name` field, back/left/top
   required + eталон optional shown at once) — see "Uploading photos" below
   for why this is a modal and not fields inline in step 1. A "запам'ятати
   цей набір у списку" checkbox in that modal adds the name to
   `data/pending.json` (`GET/POST /api/pending`), shown as a row of buttons
   under `#rawname` so an in-progress variant (photos uploaded, not yet
   calculated) doesn't have to be retyped from memory. A name drops out of
   that list automatically once it has a `scene.json` (i.e. it graduated to
   the real scene dropdown) — nothing has to clean the list up by hand.
2. **Розмітка лінії згину** — ✓/✗ for `lines/<name>_{back,left}.json`, plus
   "Відкрити розмітку" which opens the vendored marking overlay (`mark.js`,
   see the pipeline section above) for the chosen view.
3. **Вхідні дані** — ✓/✗ checklist for `archive/<name>/{back,left,top}.png`;
   "Розрахувати" calls `POST /api/generate/<name>` (disabled until photos AND
   marks both exist) and reloads the resulting scene. **Deliberately placed
   after marking, not before** — the button does nothing useful until marks
   exist, so putting "check inputs" ahead of "the one input that's usually
   still missing" just meant clicking a dead button first. Note that the
   internal element ids (`w2mark` for this step's status, `w3mark` for
   marking's) still don't match the visual step numbers — only the `<div>`
   order, `data-step` values, and header text were swapped; every id-based
   JS reference (`#dogenerate`, `#markstatus`, `#inputcheck`, ...) is
   untouched, so don't "fix" the ids to match without re-checking every call
   site that assumes the old mapping.
4. **Доведення та вивантаження** — the original point/group correction UI,
   unchanged, just moved under this step. Auto-expanded once a scene loads.

The whole UI (`index.html`, `viewer.js`'s dynamic strings, and the curve
names/scene notes `build_scene.py` generates) is in Ukrainian. Existing
scenes built before this date had their stored curve names migrated in place
(a rename-only edit of `scene.json`, touching nothing else — no
`points`/`touched` data was altered). Code comments were deliberately left as
they were (Russian/English) — this only covers what a user actually sees.

Also translated: `mark.js`'s overlay (step 3's marking canvas) — it was
already Ukrainian in `service_3030`'s original, ported as-is. `pipeline/`'s
own Python docstrings/comments and the print statements in `app.py`/
`build_scene.py`/etc. stay in Russian, same reasoning as above.

## Four bugs found and fixed in one review pass (2026-08-28)

Found by actually clicking through the app, not by inspection — three of the
four only show up when two pieces of state (the loaded scene vs. the wizard's
current target; two async handlers racing) interact, which is exactly the
kind of thing that looks fine in isolation.

1. **Stale scene data when the wizard target isn't calculated yet.** Creating
   a new set (or typing an unbuilt name) left the *previous* scene's curves,
   camera buttons, and layer list on screen — easy to mistake for "the new
   set's computed line" when it was really just leftovers. Fixed with
   `clearViewer(name)` in `viewer.js`: nulls `scene`/`sceneName`, empties
   `#cams`/`#layers`, hides the point/group/placement panels, and puts an
   explicit "«name» ще не порахований" message in the HUD instead of leaving
   old text or old geometry on screen. `refreshWizard()` now calls this (or
   `loadScene()`, if the target *is* calculated and just wasn't the one
   loaded — e.g. typed by hand instead of picked from the dropdown) whenever
   `sceneName !== currentTargetName()`.
2. **A "рахую…" loading overlay was missing entirely** — clicking
   "Розрахувати" gave no feedback beyond a small text line for what can be a
   multi-minute wait (cold standoff-fit cache across the whole neighbor
   library, see the parity section above for why). Added `#calcOverlay`
   (centered over the 3D view, spinner + cycling stage text). The stages are
   honest about being approximate — there is no real progress channel from
   `pipeline/generate.py`, just one blocking POST — so the code comment and
   this note both say so; don't let the UI imply more precision than exists.
3. **Two real race conditions, both caught by actually clicking fast, not by
   reading the code:**
   - Selecting an existing scene from the dropdown while `#rawname` still
     held leftover text from a moment ago: `currentTargetName()` prefers
     `#rawname` over `sceneName`, so `refreshWizard()` (fired by the same
     `onchange`) would target the *stale typed name*, decide the target
     didn't match, and undo the very selection that was just made. Fixed by
     clearing `#rawname` in the `onchange` handler before doing anything else.
   - Even after that fix, `sel.onchange` ran `loadScene()` and
     `refreshWizard()` **concurrently** (fire-and-forget, not awaited in
     sequence). If `refreshWizard()` read `sceneName` before `loadScene()`
     had gotten far enough to update it, it would see the *old* name, think
     the target had drifted, and call `loadScene()` a second time for the
     *previous* selection — reverting the switch after the fact. Reproduced
     by scripting two quick dropdown changes back-to-back; fixed by awaiting
     `loadScene()` before calling `refreshWizard()`, so the latter never runs
     against a `sceneName` that's mid-update.
4. **The marking overlay (`#markOverlay`) was fully broken**: the photo
   looked tinted/covered, and clicking never placed a point. Root cause was a
   single missing CSS rule — the page-wide `canvas { width:100%; height:100%
   }` (written for the main 3D canvas, `#c`) also applied to `#markprof` (the
   small 220×110 brightness-profile canvas in the corner), since its own CSS
   block never overrode width/height. It rendered at full `#markMain` size
   (measured: 960×720, laid directly on top of `#markcv`) with its
   `rgba(15,23,42,.92)` background — that's the "photo looks blue" symptom —
   and, being later in the DOM, silently absorbed every click meant for the
   drawing canvas underneath, which is why drawing "didn't work" at all. Fixed
   by giving `#markprof` explicit `width:220px; height:110px` in its own CSS
   rule. Verified both the fixed layout (`getBoundingClientRect()` before/after)
   and that a synthetic click now actually appends to `M.manual`.

## Six more fixes/features, same session (2026-08-28)

1. **Step order swapped** — see the numbered wizard list above; marking now
   comes before "Вхідні дані" since the latter's button is dead until marks
   exist.
2. **Confirmed (not changed): the marking overlay loads full-resolution
   photos.** `/mark/img/<variant>/<view>.jpg` serves the original archive PNG
   re-encoded as JPEG, dimensions untouched — verified `M.img.naturalWidth ===
   4096`. Zooming in the marking canvas reveals real detail, not an upscaled
   thumbnail; this was already true before today, just re-verified since it
   was asked about directly.
3. **Sequential, checked naming for new sets.** `genName()` no longer
   generates a random client-side suffix — it calls `GET /api/suggest_name`,
   which scans `archive/` for `nabir-<today's MMDD>-NNN` and returns the next
   free `NNN` (zero-padded, resets daily). Typing a custom name (e.g. `v26`)
   into `#ns_name` now triggers a debounced `GET /api/name_taken/<name>`
   check (`_name_status()` in `app.py`): a name with an existing `scene.json`
   is **hard-blocked**, both in the modal (upload button refuses, clear
   message) and — the real safety net — in `POST /api/upload/...` itself
   (returns 409 even if the client-side check is bypassed entirely, e.g. a
   raw `fetch` from the console). A name with *some* files but no
   `scene.json` yet (an in-progress upload from earlier) only warns, since
   coming back to add a missing photo to your own unfinished set is a normal
   workflow, not the dangerous case.
4. **Hand-drawn marks now show as a layer in the main 3D viewer**, not just
   inside the marking overlay. `markLines.{back,left}` are fetched (`GET
   /api/mark/lines/<name>/<view>`) when a scene loads, and drawn in `draw()`
   using the *same* `pr.fit` affine transform the background photo itself
   uses (they're pixel coordinates on that specific photo, not 3D points —
   drawing them via the normal `pr.p()` world-to-screen projection would be
   meaningless). Gated strictly on `scene.cameras[camIndex].name` matching
   the view the marks belong to, so back-view marks never appear while
   looking from `left` or in free orbit — not a toggle a user has to manage,
   just a structural consequence of them being image-space data.
5. **Brightness/contrast sliders for the camera-view photo** (`#photoAdjust`,
   shown only while `camIndex >= 0`), applied via `ctx.filter =
   'brightness(N%) contrast(N%)'` right before `drawImage` and reset to
   `'none'` immediately after (a lingering `ctx.filter` would otherwise leak
   into every other draw call this frame). Explicitly session-only state —
   nothing here is written to `scene.json`, `localStorage`, or anywhere else;
   "Скинути" and the general "Загальний вигляд" button both reset it to
   100/100, and it starts neutral on every page load.
6. **Color collision between item 4's new mark-line layer and the existing
   "touched" point marker** — both were `#ef4444`, so a touched point sitting
   near the hand-drawn line was indistinguishable from it once both were
   visible at the same time (a combination that only became possible once
   item 4 existed). Resolved by giving each its own color rather than
   picking one arbitrarily to keep: touched points moved to `#dc2626` (a
   calmer, slightly darker red, also just a touch smaller) since that
   convention already existed project-wide and had prior expectations built
   up around it; the brand-new mark-line layer took the color change instead
   (`#f472b6`, pink) since nothing yet depended on it being red specifically
   — it was three lines of code old at the time. `mark.js`'s own overlay
   canvas keeps its original red for "your line" — that one never showed
   touched points alongside it, so there was never a collision there to fix.

## CRITICAL, found live: exported `.LS` could fail to load on the real robot

`export_final.py` built the corrected program's name as
`f'CORR_{variant.upper()}'` and passed it straight into
`ls_points.write_points()`, which inserted it into `/PROG` **with no
validation at all**. This happened to work for every name that existed
before this session (`v21`, `v26`, ...) purely because none of them
contained anything but letters and digits. The `nabir-MMDD-NNN` naming
introduced this same session broke it immediately: `CORR_NABIR-0828-001`
has hyphens, which the Fanuc controller rejects outright. Caught live — the
user tried to load `nabir-0828-001`'s exported program on the actual robot
controller and got `ASBN-002/008/009/050: Invalid name in /PROG section`.
The user noted this exact class of naming problem "has been a recurring
issue," which is why the fix below is a general sanitizer, not a special
case for the hyphen.

Fixed with `ls_points.fanuc_safe_name(raw, max_len=17)`: strips anything
that isn't a letter or digit to `_`, uppercases, strips leading/trailing
`_`, truncates to 17 chars (the same empirically-proven limit already used
by `pipeline/geometry.py::program_name` — longest name ever run in
production is `TORXL_NEW_PROG2_5`, 17 chars). `export_final.py` now calls
`ls_points.fanuc_safe_name(f'CORR_{variant}')` instead of building the name
inline. Verified: `v21`/`v26` produce byte-identical names to before
(`CORR_V21`/`CORR_V26`, no regression); `nabir-0828-001` now produces
`CORR_NABIR_0828_0` (valid, no hyphens, ≤17 chars). Two already-exported
files on disk from before this fix (`nabir-0828-001_final.LS`,
`nabir-0828-nieo_final.LS`) had the bad `/PROG` line and were regenerated.

**Anyone adding another `new_prog_name=...`/`/PROG` writer to this service in
the future must route the name through `fanuc_safe_name()` first** — this bug
class doesn't announce itself in testing with old-style names, only fails
once someone types (or the code generates) a name with a character outside
`[A-Za-z0-9]`, and the failure shows up on the physical controller, not in
this codebase.
