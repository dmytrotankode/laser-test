#!/bin/bash
# Runs pose_fit_3d.py against all 5 archive/v1-v5 real photo sets and prints
# the point-by-point mean error against each set's production-recorded .ls,
# for comparison against the heuristic pipeline's numbers in VALIDATION_LOG.md.
#
# input/photos_current/*.png are git-tracked, so this script overwrites them
# per test set and restores the committed version via `git checkout` at the
# end - no manual backup/restore step needed. Assumes you have NOT staged any
# real edits to those three files before running (check `git status` first).
#
# Usage: bash scripts/batch_test_pose_fit_3d.sh [output_file]
# Takes ~15-20 min total (multi-start Powell x5 sets). Run in background.
set -e
cd "$(dirname "$0")/.."

SESSION=run_20260723_122941
ARCHIVE="../archive"
OUT="${1:-/tmp/batch3d_results.txt}"

declare -A REF_FILES=(
  [v1]="TORXL_NEW_PROG2.LS"
  [v2]="TORXL_NEW_PROG2_2.LS"
  [v3]="TORXL_NEW_PROG2_3.LS"
  [v4]="TORXL_NEW_PROG2_4.LS"
  [v5]="TORXL_NEW_PROG2_5.LS"
)

echo "=== BATCH 3D POSE FIT TEST - ALL 5 ARCHIVE SETS ===" > "$OUT"

for v in v1 v2 v3 v4 v5; do
  echo "" >> "$OUT"
  echo "=== $v ===" >> "$OUT"
  echo "--- $v: swapping photos ---"

  conv_dir="$ARCHIVE/$v/converted"
  frame1=$(ls "$conv_dir" | grep '^frame1_' | grep -v thumb)
  frame2=$(ls "$conv_dir" | grep '^frame2_' | grep -v thumb)
  frame3=$(ls "$conv_dir" | grep '^frame3_' | grep -v thumb)
  cp "$conv_dir/$frame1" input/photos_current/back.png
  cp "$conv_dir/$frame2" input/photos_current/left.png
  cp "$conv_dir/$frame3" input/photos_current/top.png

  echo "--- $v: running step05 (segmentation) ---"
  ./venv/Scripts/python.exe scripts/step05_segment_current.py --session "$SESSION" >> "$OUT" 2>&1

  echo "--- $v: running pose_fit_3d (this takes a few minutes) ---"
  ./venv/Scripts/python.exe scripts/pose_fit_3d.py --session "$SESSION" >> "$OUT" 2>&1

  echo "--- $v: comparing to production reference ---"
  ./venv/Scripts/python.exe -c "
import json, re
import numpy as np
from scipy.spatial.transform import Rotation

with open('results/$SESSION/pose_fit_3d_result.json') as f:
    fit = json.load(f)
pivot = np.array(fit['pivot'])
R = Rotation.from_euler('xyz', fit['delta_rotation_deg_xyz'], degrees=True).as_matrix()
T = np.array(fit['delta_translation_mm'])

def load_ls_points(path):
    pts=[]
    pat=re.compile(r'P\[(\d+)\]\{[^}]*X\s*=\s*([-\d.]+)[^}]*Y\s*=\s*([-\d.]+)[^}]*Z\s*=\s*([-\d.]+)', re.IGNORECASE|re.DOTALL)
    txt=open(path, errors='replace').read()
    for m in pat.finditer(txt):
        pts.append((int(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))))
    return pts

orig = load_ls_points('input/ls_file/TORXL_NEW_PROG.LS')
o = np.array([[p[1],p[2],p[3]] for p in orig])
mask = np.ones(len(o), dtype=bool); mask[[0,97]] = False
generated = pivot + (R @ (o - pivot).T).T + T

ref = load_ls_points('$ARCHIVE/$v/${REF_FILES[$v]}')
r = np.array([[p[1],p[2],p[3]] for p in ref])[:98]

d = np.linalg.norm(generated[mask] - r[mask], axis=1)
print('POINT_BY_POINT $v: mean=%.2f median=%.2f max=%.2f min=%.2f' % (d.mean(), np.median(d), d.max(), d.min()))
" >> "$OUT" 2>&1

done

echo "" >> "$OUT"
echo "=== ALL DONE ===" >> "$OUT"

git checkout -- input/photos_current/back.png input/photos_current/left.png input/photos_current/top.png
echo "Photos restored (git checkout)." >> "$OUT"
