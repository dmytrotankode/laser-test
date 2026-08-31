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

### Marking the fold line (`pipeline/detect.py`, `mark.js`, step 2 of the wizard)

`generate()` reads photos from `archive/<variant>/` and, optionally, line
marks from `lines/<variant>_{back,left}.json` — only photos are required
(see "Fold-line marking is optional" further down for why and since when).
The marking tool itself (originally `service_3030/app.py` + `detect.py`) is now
vendored: `pipeline/detect.py` is an unchanged copy of the auto-detect
algorithm (dynamic-programming trace of the dark fold-line band, plus a
gradient-refined edge estimate — see its own docstring for why), and
`web/static/js/mark.js` is the 2D pan/zoom/click marking canvas, opened as a
full-screen overlay from wizard step 2 (`#markOverlay` in `index.html`). It
writes the exact same `lines/<variant>_<view>.json` format `line_marks.py`
already reads, so nothing downstream needed to change.

Routes (`app.py`): `GET /mark/img/<variant>/<view>.jpg` (serves the archive
photo as JPEG for the canvas), `GET /api/mark/detect`, `GET /api/mark/profile`
(brightness cross-section, for judging where the trench floor really is),
`GET|POST /api/mark/lines/<variant>/<view>`, `GET /api/mark/compare` (manual
marks vs. the auto-detector, median/p90/bias in px and mm). These are
deliberately separate from the older `/api/scene/...` routes — marking has
nothing to do with a built scene, only with `archive/`+`lines/`.
**As of 2026-08-28, `mark.js` no longer calls `/api/mark/detect` or
`/api/mark/compare`** — the operator only wants their own hand-drawn line,
not the auto-detected candidates or a comparison against them (see "Marking
tool — auto-detected candidate lines removed" below). The routes and
`pipeline/detect.py` are still there, just unused by this UI now.

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
1. **Набір** — pick a built scene from the dropdown. `#rawname` used to also
   be a free-text field for checking a not-yet-built name's status; that
   visible input was removed (2026-08-28, operator didn't need it) but the
   element is kept as `type="hidden"` since `currentTargetName()` and the
   pending-name buttons below still read/write its `.value` as the wizard's
   current target. A separate "+ Новий набір" button opens
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
4. **Доведення та вивантаження** — the point/group correction UI, moved
   under this step; also holds "Ракурс" (camera/free-view selection),
   "Об'єкти" (layers) and "Опори". Auto-expanded once a scene loads. The
   correction UI itself was substantially reworked later the same day — see
   "UI simplification pass + floating axis pad" below for what changed
   (screen-relative direction buttons, the floating pad, removal of the
   selection-subset editor).

The whole UI (`index.html`, `viewer.js`'s dynamic strings, and the curve
names/scene notes `build_scene.py` generates) is in Ukrainian. Existing
scenes built before this date had their stored curve names migrated in place
(a rename-only edit of `scene.json`, touching nothing else — no
`points`/`touched` data was altered). Code comments were deliberately left as
they were (Russian/English) — this only covers what a user actually sees.

Also translated: `mark.js`'s overlay (the marking canvas) — it was
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
(`CORR_V21`/`CORR_V26`, no regression).

**Anyone adding another `new_prog_name=...`/`/PROG` writer to this service in
the future must route the name through `fanuc_safe_name()` first** — this bug
class doesn't announce itself in testing with old-style names, only fails
once someone types (or the code generates) a name with a character outside
`[A-Za-z0-9]`, and the failure shows up on the physical controller, not in
this codebase.

### Two more layers of the same incident, found by continuing to test live

The first fix alone was not enough — loading still failed, twice more, each
time on the *next* thing this bug class touches:

1. **File name didn't match `/PROG` name.** `export_final.py` wrote the
   output to `<variant>_final.LS` (e.g. `nabir-0828-001_final.LS`) while the
   sanitized `/PROG` name inside was something else entirely
   (`CORR_NABIR_0828_0`). This service's own `pipeline/ls_template.py`
   already documents the rule this violated: *"the file name and the
   in-file /PROG name MUST match (the controller refuses to load a program
   otherwise)."* Fixed by deriving the output path from the same sanitized
   `prog_name` (`f'{prog_name}.LS'`) instead of `f'{variant}_final.LS'` —
   now whatever `fanuc_safe_name()` returns is used for *both* the file name
   and the `/PROG` line, guaranteeing they match by construction.
2. **Right-truncation silently collided different variants into the same
   name.** The first version of `fanuc_safe_name` cut from the end
   (`s[:max_len]`). For `CORR_NABIR_0828_001` (19 chars, over the 17 limit)
   that produced `CORR_NABIR_0828_0` — and `nabir-0828-002` through
   `nabir-0828-099` all produce the *exact same* sanitized prefix up to that
   point, so they'd *all* truncate to that identical name. Confirmed by
   testing several side by side before shipping the fix. This is worse than
   the first bug: not a load failure, but a silent one where a completely
   different helmet's corrected program could overwrite or be confused with
   another's on the controller. Fixed by truncating from the **middle**
   instead — keep a head half and a tail half, drop only what's in between
   (`s[:head] + s[-tail:]`) — so `nabir-0828-001` → `CORR_NABI0828_001` and
   `nabir-0828-002` → `CORR_NABI0828_002`, distinguishable again. Verified
   across `001`/`002`/`010`/`099`/a different day/`v21`/`v26`/the
   already-used `nabir-0828-nieo` — no two produce the same output, and the
   short old-style names are still untouched.

All three fixes verified through the real `POST /api/scene/<name>/export`
route (not just the standalone function), and the two variants already
exported before these fixes (`nabir-0828-001`, `nabir-0828-nieo`) were
re-exported with the corrected names.

## UI simplification pass + floating axis pad (2026-08-28)

A larger round of interface cleanup, driven by real operator feedback after
the first helmet test on the robot ("довольно неплохо прошёлся лазер" — good
enough that the UI is now worth polishing, not just making functional).

**Light theme, scoped to the control sidebars only.** `#side` and `#markSide`
now use a light palette (`#f5f7fa` background, dark text) — every rule is
written as `#side .foo, #markSide .foo { ... }`, never a bare global
override, because `#side`/`#markSide` share base CSS classes (`h2`, `button`,
`label`, `.prow`, `.wmark`, ...) with `#newsetOverlay`/`#markOverlay`'s other
parts, which are **deliberately still dark** (photos/lines need dark
contrast). A blind `replace_all` on a shared color value here is genuinely
dangerous — it happened once mid-session (fixed before commit) and is why
every light-theme rule is scoped by ID prefix, never bare.
`#view`/`#markMain` (the actual 3D canvas / photo canvas) stay dark
unconditionally.

**Removed the always-visible hint text and the "Опори" checklist clutter.**
The bottom-of-canvas control hint (`#hint`) is gone — operators get trained
in person instead. "Опори" (grid/axes/photo toggles) collapsed behind a
`⚙ Опори` button (`#oporyToggle`/`#oporyPanel`, closed by default); the grid
checkbox now defaults **off** (was on); the "модель без прозорості" (`solid`)
checkbox was removed entirely as dead weight — nobody used it and it added a
`m.solid` branch to `drawMesh()` for no benefit. Axes were explicitly left
alone (still on by default) per direct instruction — don't touch that
default without being asked again.

**"Вигляд"/"Об'єкти"/"Опори" moved inside wizard step 4's `.wbody`**, so
`.wstep.open .wbody { display:block }` (already existing CSS) hides them on
steps 1–3 automatically — no new JS needed, just relocating the HTML block.
They used to sit below the wizard, always visible regardless of which step
was open, which was confusing before any scene was even calculated. Later
renamed the `<h2>Вигляд</h2>` section to **"Ракурс"** (more specific — it's
camera/angle selection, not "view" in the app-wide sense) and compacted
"Загальний вигляд" + the per-camera buttons into a single flex row (button
text shortened to just the camera name, full name kept as a `title`
tooltip). The "Загальний" button now also gets `.on` when free-view is
active — it used to only highlight the camera buttons, so returning to free
view showed *no* active button at all, which read as "nothing is selected."

**Removed the manual "type an uncalculated name" field in step 1**
(`#rawname`'s visible input + its label). `#rawname` itself is kept as a
`type="hidden"` input, because a lot of other logic (`currentTargetName()`,
the "у процесі" pending-name buttons, the new-set upload flow) reads/writes
its `.value` as the wizard's current-target state — deleting the element
outright would have broken those. Only the free-typing UI and its now-dead
debounced `oninput` handler were removed.

### Floating "axis pad" over the 3D view (`#axisPad` in index.html, `viewer.js`)

The core complaint this solves: the group-edit buttons (`пов X/Y/Z`,
`зсв X/Y/Z`) move points along **machine axes**, which don't line up with
what the operator sees on screen from a given camera view — "не можу
второпати, куди що рухати" (verbatim). Two changes together fix this:

1. **Screen-relative direction glyphs.** `camDir(vec)` projects a machine
   axis into the current camera's frame (`mulv(rodrigues(cam.rotation),
   vec)`); `shiftGlyphs(axis)` picks one of 8 arrow glyphs (`arrow8()`,
   `atan2(dy,dx)` in screen space) when the axis has enough on-screen extent
   (`hypot(dx,dy) >= 0.35`), else falls back to plain `−`/`+` (a
   depth-axis shift is genuinely almost invisible on screen — an arrow there
   would be actively misleading, not just useless). `rotGlyphs(u,v)` decides
   `↻`/`↺` for a rotation button the same way, using the same two-axis
   ordering `rotFromDeg()` actually rotates through (verified: "пов X" moves
   Y→Z, "пов Y" moves Z→X, "пов Z" moves X→Y — a screen-space cross product
   of those two projected axes gives the true visual spin direction,
   accounting for the canvas's Y-down convention). **Only active with a
   camera selected** (`camIndex >= 0`) — in free orbit the camera itself
   rotates under the mouse, so no machine axis has a fixed screen direction
   to show.
2. **A floating panel (`#axisPad`) over the canvas**, one row, sections
   separated by `.padDivider`: shift arrows → rotation icons → step size
   (0.1/1/5/10) → Зберегти/Скинути. It is a **pure proxy**, not a second
   implementation: every button in it calls `.click()` (or, for the async
   save, invokes the handler function directly via `document.getElementById
   ('gsave').onclick()` so it can `await` the network response) on the real,
   now-hidden sidebar buttons inside `#groupctl`/`#group`. **Never add logic
   directly to `buildAxisPad()`'s button handlers** — if a behavior needs to
   change, change the underlying sidebar handler in `buildGroupEditor()`,
   and the pad picks it up automatically next time it's rebuilt (called at
   the end of `buildGroupEditor()`, and also on every camera switch/reset so
   the glyphs stay in sync with the current view).
   - **Axes whose on-screen shift is near-invisible from the current camera
     are dropped from the pad entirely** (`screenPlanar(axis) < 0.35`), not
     just shown with plain `−`/`+` (that fallback is what the sidebar still
     does, since it always shows all three regardless of view) — typically
     leaves 2 of 3 shift groups + all 3 rotation groups + step + save ≈ 10
     buttons, small enough for one row.
   - **Rotation icons are a real projected ring, not a static glyph**
     (`rotIconSVG(u, v, sign)`): samples 28 points around the unit circle in
     the `(u,v)` plane, projects each through the camera, and draws the near
     half of the ring solid + the far half as a faint dashed arc (depth sign
     of each sample point) plus an arrowhead at the nearest-to-viewer point.
     This is what makes an axis that's edge-on to the camera visibly
     collapse into a thin ellipse (a "tilt", not a clean on-screen spin) —
     the geometry does that correctly on its own, it isn't special-cased.
3. **"Комплексний зсув" (the whole selection-subset system) was removed, not
   just hidden.** `group_sel`/"Уся лінія"/"Видимі тут"/Shift-click-to-narrow
   are gone from `trySelectPoint()` and the UI entirely — the group editor
   now always acts on the whole editable curve
   (`activePoints()`'s `group_sel.length` branch is permanently dead, kept
   only because ripping it out cleanly touches more call sites than leaving
   it as unreachable code costs). This was a deliberate choice, not
   laziness: with the selection UI gone, a stray Shift-click would have
   silently narrowed the scope of every future pad click with **zero visible
   feedback**, since the panel showing "vibrano N of M" was also removed —
   a footgun worse than the UI clutter it would have saved.
4. **"Зберегти"/"Скинути" now live only in the pad**, and "Зберегти" turns
   green (`.dirty` class) whenever the active curve's points differ from
   `c._saved` (`isDirty()`, compared every `draw()` call — cheap, just a
   per-point tolerance check, no allocations) — added because operators were
   forgetting to save after nudging points. "Скинути" gets a plain white
   highlight in the same state (not the same green — resetting is discarding
   work, it shouldn't look as inviting as saving). Both go dim when there's
   nothing to save. The HUD text in the corner of the 3D view no longer
   prints `погляд камерою X\nфокус N px` — the active camera is already
   shown via the highlighted button, and focal length is pure diagnostic
   noise nobody asked to see.

### Marking tool (`mark.js`) — auto-detected candidate lines removed

The auto-detector (`/api/mark/detect`: upper shadow edge / trench floor /
lower shadow edge / overflow edge) and the compare-to-auto feature
(`/api/mark/compare`) are **no longer called from the UI at all** — the
operator only wants their own hand-drawn line, doesn't want the other four
computed or shown, and doesn't want a comparison against them. Removed:
the "Знайти лінії" button, all four candidate-line checkboxes, "Порівняти з
автоматичними лініями" and its metrics table, and the color/name lookup
tables (`M_COLORS`/`M_NAMES`) that only existed to render them.
**`/api/mark/detect` and `/api/mark/compare` still exist in `app.py`** —
left in place deliberately (low-risk, might still be useful for a future
QA/calibration pass, and touching shared detection code wasn't in scope) —
but nothing in this service's UI reaches them anymore. `#markSide` also
picked up the same light-theme treatment as `#side` (see above);
`#markMain`/the photo canvas stays dark.

### Real incident: live UI testing corrupted `nabir-0828-001`'s saved points

While verifying the axis pad's "Зберегти" button (needed a real async
round-trip to check the ✓/✗ feedback and the dirty-state highlight), it was
clicked for real, more than once across several verification passes,
against the actual running dev server — not a sandbox. Each test shift +
real save left a genuine ~5mm offset in `scene.json` on disk, and it
compounded: by the time the operator noticed, all 97 points of
`nabir-0828-001`'s editable curve were marked `touched=true` with up to
17.4mm of drift, which the operator correctly noticed as "the cut line
slides further left/down every time I reopen it" (a world-space Y offset
projects as horizontal on the `back` camera and vertical on `top` — exactly
what was reported, which is what made it traceable at all instead of
looking like a random rendering glitch).

**First fix attempt was wrong**: resetting every point to `points_original`
(the pristine, uncorrected calculation) — this also erased the operator's
own *real* correction from an actual helmet test around 13:30 that day,
which is needed later for analysis. `data/scenes/*/scene.json` turns out to
be **git-tracked in this repo** (unusual for generated data, but true here),
which is what made the real fix possible: `git log --follow` on the file
showed a commit at 13:24:54 — the closest snapshot to "13:30, not later" and
the last one before this session's UI testing began — and the file was
restored from that commit instead of from `points_original`.

**Lesson for anyone testing point-editing UI here**: `touched=true` /
nonzero diff from `points_original` is not proof of test contamination —
it's just as likely to be real, wanted operator work (this repo has at
least one case, `v26`, of a scene with real accepted corrections from a
prior physical test). Before "fixing" apparent data drift, check whether the
scene file is git-tracked and cross-reference commit/mtime timestamps
against what the operator actually says they did and when — don't assume
the clean baseline is the correct one to restore. And more basically: don't
click a real save/persist button against the live dev server while
verifying UI behavior unless the save itself is under test, and if it is,
revert immediately afterward rather than leaving test data sitting in a
scene that's actually in use.

## Confirmation before re-running "Розрахувати" on a corrected scene (2026-08-29)

`/api/generate/<name>` fully rebuilds `scene.json` (same as `build_scene.py`
— see its own docstring warning above), silently discarding any saved
per-point corrections. Direct follow-up from the same-day incident above:
`dogenerate`'s click handler now checks whether the currently-loaded scene
(only when `sceneName === currentTargetName()`) has any `touched` points on
its editable curve, and if so shows a plain `confirm()` — **Ukrainian text
only**, matching the rest of the UI — naming exactly how many points are at
risk, before doing anything. Cancelling makes zero network requests
(verified by stubbing `window.confirm` to return `false` and checking
`read_network_requests`), so it's safe to test this path without touching a
real scene.

## Fold-line marking is optional (2026-08-29)

Production reality forced this: with ~300 helmets/day, spending ~3 minutes
per helmet on manual fold-line marking *on top of* per-point correction
afterward is too slow. No checkbox/config flag was needed to make marking
optional — the fold-line mark distance was always just one of three terms
`contour_fit.py::resid_of` combines (the silhouette bounding-box check and
the top-view contour distance are the other two, and they're computed from
photos alone, not from marks), so the fix was making that one term tolerate
being absent instead of requiring it.

`resid_of()` now does `marks.get(variant, {})` and skips a view's mark term
entirely with a plain `if w not in var_marks: continue` (previously
`marks[variant][w]` — an unconditional `KeyError` if the variant had no
marks at all, or a *silent wrong-view* bug if `line_marks.load_marks()` had
dropped one view for having under 3 points, since Python doesn't error on
dict access it never reaches only when *neither* view is present — worth
knowing this half-broken partial case existed before, not just the
no-marks-at-all one). This also transparently supports **partial** marking
(only `back` or only `left`) — nobody asked for that specifically, but it
falls out of the same fix for free and there was no reason to special-case
it away.

`viewer.js`'s "Розрахувати" button now only requires photos
(`genBtn.disabled = !allPhotos`, was `!(allPhotos && allMarks)`); step 2's
status stopped rendering missing marks as an error (no more red `✗`/`bad`
class) — it's a neutral "необов'язково" note now, since it genuinely isn't
required.

**The accuracy tradeoff is real and was measured, not assumed**: re-running
`generate('v1', ...)` on the same variant with its marks physically moved
out of `lines/` gave `mean_mm≈6.6, within_2mm_pct≈7.3` vs. `mean_mm≈2.7,
within_2mm_pct≈39.6` with marks present. Skipping marking is a legitimate
choice for throughput, not a free accuracy lunch — the expectation is that
the now-faster per-point correction step (see the floating axis pad above)
absorbs the gap, and every correction made this way is itself training
signal for a future without either step (see "Roadmap" below).

## Roadmap: feeding operator corrections back into the neighbor library

Not yet implemented — captured here so the idea doesn't get lost. Every
`touched=true` point already recorded on a corrected `.LS` is exactly the
supervised signal a future improvement needs, and the natural place to feed
it back in is `pipeline/neighbor.py`'s k-NN library
(`calib/libraries/<name>/variants.json`), not a new ML model: once an
operator has fully corrected a variant, add its resulting `.LS` to the
neighbor pool as a new "known-good" reference. The next helmet with a
similar silhouette then picks up an already-corrected shape via nearest-
neighbor instead of the uncorrected baseline, with no new inference code —
the existing `neighbor.nearest()` mechanism does the work as-is. Over
enough corrected helmets (the operator's own estimate: "через 100 шлемов"),
this should shrink both how much marking helps and how much per-point
correction is needed, converging toward needing neither for well-represented
helmet shapes. Two things this needs before it's real, not sketched:
- A decision on *when* a corrected variant is "good enough" to add (all
  points touched? below some residual threshold vs. a later independent
  check? operator says so explicitly?) — adding a badly-corrected variant
  would poison the neighbor pool for everything similar to it afterward.
- Versioning discipline for `calib/libraries/` (a new named library
  snapshot when the pool changes, per the existing convention in "Versioned
  calibrations/models" above) so a regression can be traced to *which*
  addition caused it, not just "the library" in the abstract.

## Curve-gap warning (2026-08-29)

Direct follow-up to the optional-marking accuracy tradeoff: without marks in
a poorly-visible region (the ear-fold area is the recurring real example),
`generate()`'s per-point rim-snap (`on_cad()` in `pipeline/generate.py`) can
cluster several of the neighbor's points onto nearly the same spot and leave
one large gap elsewhere on the ring — measured live at up to 59mm vs. a
~9mm median spacing on an affected variant. That is a real shape defect, not
a cosmetic accuracy dip: the final `.LS` would drive the robot in a straight
chord across that gap instead of following the true fold there.

`viewer.js::checkCurveGaps()` (called from `loadScene()`) flags this: it
measures every consecutive-point segment length around the editable curve
(respecting `c.closed`), and any segment over `max(3×median, 15mm)` is
listed in `#curveWarn` — point ids and the jump length, plain text. **This
is detection only, not a fix** — there's no tool yet that can usefully
close a gap like this through the UI (the group panel only does rigid
whole-line transforms; the point panel edits one point at a time, and
manually rebuilding 15-20 points to approximate the missing arc defeats the
whole point of skipping marking for speed). Deliberately **not** rendered as
a color highlight on the 3D points — red is already "touched," reusing it
for "suspicious" would make both meanings ambiguous at a glance (direct
user feedback). The practical fix, once a jump is flagged, is targeted
marking of just that view/region and re-running "Розрахувати" — not manual
point surgery.

## Semi-automatic marking: an auto-detected draft instead of a blank canvas (2026-08-29)

Manual marking from scratch (8–12 clicks per view) is real operator time
production can't always spare, but skipping it can produce the curve-gap
defect above. Middle path: `pipeline/detect.py` (vendored, unchanged;
dynamic-programming trace of the dark fold-shadow band, four candidate
lines per call) was already sitting unused after its old 4-candidate
comparison UI got removed — it's now repurposed as a starting draft the
operator adjusts rather than draws from nothing.

**Validated against real data before building anything**, per the "don't
trust a clean baseline blindly" lesson higher up in this file: ran
`detect.py` against all 48 photos in this project that already have a real
manual mark (26 variants × back/left) and compared its `edge_lo` candidate
(the one an earlier 5-photo calibration, referenced in `detect.py`'s own
docstring, found closest to how the customer actually marks) against each
manual line, using the same segment-distance math as `service_3030/bench.py`.
Results:
- `edge_lo` is still the best candidate at this larger scale too (median
  disagreement across all 48 photos: 0.54mm; `upper`/`center`/`lower` are
  all worse). The 5-photo calibration held up.
- Where `detect.py`'s own confidence flag (`ok`, contrast-based) is high,
  agreement with the real manual mark is typically sub-1-2mm. Where `ok`
  drops, disagreement genuinely spikes too (one photo: 6–20% confidence and
  up to ~200px error in the low-confidence third, then 90–100% confidence
  and 2–4px error everywhere else) — the confidence signal is not noise,
  it's usable to tell the operator where to actually look.
- No evidence, on any of the 48 photos, of the detector locking onto
  something other than the fold shadow (no localized-but-confident spike
  pattern anywhere). One photo (`v21_back`) disagreed with its manual mark
  by a large, *smooth* amount across nearly the whole width at 95–100%
  confidence — a pattern more consistent with that particular manual
  reference being off than with the detector tracking the wrong thing, but
  wasn't independently re-verified against the photo by eye.

**First implementation used `detect.py`'s live output directly as the
draft — superseded same day.** It worked, but visually "rывками" (jagged) —
real operator feedback after actually looking at it. `detect.py`'s
per-column trace follows genuine pixel-level noise (JPEG artifacts, minor
contrast fluctuation), which is exactly what you'd expect from a live pixel
detector and exactly why it looks rough even where its own numbers (above)
say it's accurate. The fix wasn't to smooth the trace further — it was to
stop drafting from photo pixels at all.

### The draft is now a projected CAD template, not a pixel trace (`/api/mark/template`)

The insight: `pipeline/generate.py` already treats the fold line as *a
known, fixed 3D shape* (the CAD rim, `mesh_rim.mesh_rim()`, offset by the
measured `FOLD_RADIAL`/`FOLD_UP` constants) that only needs *placing*, not
re-discovering, per photo — that's the entire premise behind `on_cad()`'s
per-point snap in the real calculation. So the draft line should be exactly
that: the same rim geometry, offset the same way, projected through the
same calibrated camera — perfectly smooth by construction, because it never
touches a single photo pixel. `GET /api/mark/template?view=back|left`
(`app.py`) does this: `mesh_rim` + `contour_fit.radial()` for the
fold-offset direction, `camera_model.project()` through
`calib/cameras/<recipe>/cam_<view>.npy`, `camera_model.near_arc()` to keep
only the camera-facing half of the closed rim loop (order-preserving, so
the result is already a clean polyline, no sorting needed). **Identical for
every variant under the same view** — the model and camera don't depend on
the photo — so it's computed once per process and cached
(`_TEMPLATE_LINE_CACHE`, keyed by view only).

**Which pose to project at was tested cheaply before deciding, not
assumed.** The obvious-sounding option — run the same marks-free pose fit
`generate()` already does when marks are absent (silhouette + top-contour
only) and project at *that* pose — was measured against real manual marks
on 3 variants (6 view-samples) before writing any UI code: the nominal,
*unfitted* pose (straight from `calib/cad_placement`, zero adjustment) beat
the "quick-fit" pose in 5 of 6 samples, sometimes drastically (v9: nominal
4.5mm vs. fitted 38.5mm). Without a fold-line constraint, the silhouette/
contour-only optimizer can drift the pose *away* from the true fold while
still satisfying its own (weaker, less specific) terms — worth remembering
as a caveat about `generate()`'s own no-marks path too, not just about this
draft feature; not chased further here since it's a separate question from
what to draft with. So the template is projected at the **nominal pose,
with no fit at all** — cheaper (zero extra compute, vs. several seconds of
segmentation for a pose fit) and more accurate in this test, a rare
free lunch. Checked properly with `near_arc` applied (an earlier pass of
this same test forgot that step and mixed in far-side/behind-camera points,
producing misleadingly bad numbers): against real marks, nominal-pose
`edge_lo`-equivalent projection lands at 2.0mm/1.4mm (v1 back/left), 3.8mm/
2.1mm (v9) — genuinely close — and 10.7mm/9.7mm on `v21_back`, the same
outlier flagged in the `detect.py` validation above.

**Implementation** (`mark.js`): unchanged interaction from the first
version — `openMarkOverlay()` fetches the draft only when the variant has
no saved manual mark yet (`M.manual.length === 0`, so a real marking is
never silently touched), draws it as a plain solid yellow polyline (no
confidence concept anymore — the shape doesn't depend on the photo, so
there's nothing to be "unsure" about), and `autoTransformed()`/`M.autoAdj`
apply a rigid shift+rotate around its centroid, same pattern as
`buildGroupEditor()`'s controls in the 3D viewer (just 2D photo pixels
instead of mm) — deliberately **rigid-only**, not a per-point bend, to keep
the interaction to a handful of clicks. "Застосувати як лінію"
(`applyAutoAsManual()`) downsamples the transformed draft to ~40 points
into the normal `M.manual` array, after which existing click-to-add/remove
editing works on it unchanged — additive, not a separate code path.
Saving still goes through `/api/mark/lines/<variant>/<view>`;
`contour_fit.py` cannot tell where a mark came from either way.

Not yet done: comparing actual operator time (template+adjust vs.
draw-from-scratch), and whether rigid-only adjustment is expressive enough
in practice or a later version needs a small number of independently-
draggable anchor points for cases where the disagreement isn't a simple
shift/rotation.
