# Service 3030 — the fold line, and what it is good for

Started as a tool for the customer to mark the pressing boundary by hand. It
became the place where the geometry of the cell is measured.

**It only reads `service_5056`.** No file there has ever been modified by this
service. Experiments import 5056's own modules so that every number is produced
by 5056's own protocol and is directly comparable to its published figures.

```
start.bat                  # marking UI, port 3030
```

## What was established here

1. **The fold line is the cut line**, offset ~2–3 mm up along the tool axis.
   The existence of a constant offset is solid; the exact value trades off
   against camera pose and should not be used standalone.
2. **Cameras can be calibrated without a board.** The robot already recorded
   hundreds of exact 3D points: the `.LS` programs. Combined with the laser-dot
   observations from `PLAN.md` §4e they give both cameras in machine
   coordinates. Prediction of unseen data: 0.7–0.8 mm.
3. **Helmet pose can be recovered from two photographs**, no library involved in
   the correction. On foreign helmets: points within the 2 mm tolerance went
   17 % → 57 %, worst deviation 9.4 → 4.5 mm.
4. **The ceiling is camera accuracy, not the idea.** A perfect rigid pose would
   give 84–96 % in tolerance. What remains beyond that is shape difference
   between helmet instances, which no rigid motion can fix.

## Measured and rejected — do not redo

* the fold line as extra features in 5056's regression — LOO 1.34 → 1.23 mm, and
  a permutation control shows the gain is real but tiny; it duplicates what the
  silhouette already knows (roll/pitch) and does not cover the weak axes;
* **minimax / robust losses** for pose fitting — minimax is better on the master
  helmet (78 % vs 64 %) and catastrophic on foreign ones (15 %); `soft_l1` is
  worse everywhere. Plain least squares is the only choice without a collapse;
* **lowering the segmentation cutoff** in 5056 step 3 — no gain at any level, and
  a fixed image row moves blind sets *further* from the library, not closer. The
  documented "skirt length" explanation of `out_of_range` does not reproduce;
* **dropping the ear** from the markup — worse everywhere. The ear carries 24 %
  of the left-view points and a disproportionate share of the information.

## Beware: the sample is skewed

16 sets are the same master helmet, 5 are other instances. **Any aggregate must
be split master / foreign** — an aggregate hid a total collapse on foreign
helmets twice already (see the minimax note above).

## Files

| | |
|---|---|
| `app.py`, `web/` | marking UI |
| `detect.py` | automatic line finder; `edge_lo` is the candidate that matches the hand |
| `bench.py` | detector vs hand markup, distance to the polyline, **not** vertical at fixed x |
| `shots.py` | where the photographs live (shared with `app.py`) |
| `line_features.py` | markup → numbers comparable across shots |
| `exp_camera_fit.py` | camera from recorded programs; focal must be pinned or it degenerates |
| `exp_camera_joint.py` | camera from programs **and** laser dots, with the test battery |
| `exp_pose_from_line.py` | pose from two photographs, scored by 5056's own metric |
| `export_ls.py`, `export_all.py` | write `.LS` for that pose, into `out/` |
| `exp_*.py` (others) | the rejected experiments above, kept so they are not repeated |
| `export_scene.py` | hand the geometry to service 2020 |
| `data/cam_back.npy`, `cam_left.npy` | the calibrated cameras: `[rvec(3), position(3), fold offset]` |
| `data/lines/*.json` | the hand markup |

## Test discipline

* fitting uses `dataset.TRAIN` only, through `dataset.guard_training`;
* `v6`, `v13` are held out; `v20`, `v21`, `v24`, `v25` are blind and their
  results have now been read, so they are partly spent;
* **`v22`, `v23` have never been looked at** — the last untouched check. Their
  markup is the one the customer is unsure about.

## What would move the needle next

20–30 marker points per camera with pendant coordinates **and orientation**
(`W/P/R`), in `UFRAME 2` / `UTOOL 2`. The distance to the part need not be known
— only that the nozzle points at the dot — but keep it small, since an aiming
error scales with distance. Approach ~5 dots twice with clearly different
orientations: that measures the `UTOOL` defect (0.4–0.6 mm per degree, §4e)
directly.
