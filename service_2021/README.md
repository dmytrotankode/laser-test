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
marker-based one: `service_3030/data/cam_{back,left,top}_marker.npy`.

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

## Future ideas (not started — recorded per user request, 2026-08-27)

Idea for a bigger UI redesign: turn the sidebar into a collapsible step
wizard (Figma-panel style, only one step expanded at a time):
1. Pick variant (or start a new "current" in-progress one).
2. Check inputs present (photos, cameras) — show "waiting for X" if not.
3. (Conditional) draw the cut-line marking on new photos, similar to
   `service_3030/app.py`'s line-marking tool — only needed if that step
   hasn't been done yet for this variant.
4. Correct + export (what this service does today), with a short,
   unique-but-not-long name for the exported file.

Open question raised by the user: when step 3 (line drawing) is active, the
main view may end up looking almost identical to the final correction step
(same photos, same-ish overlay) — worth checking during design whether steps
3 and 4 should actually be one screen with a mode switch rather than two
separate wizard steps.

This would likely mean either duplicating `service_3030`'s marking-tool logic
into this service (to keep the self-containment rule above), or accepting a
one-directional read-only dependency on it — decide deliberately before
starting, don't default into breaking self-containment.
