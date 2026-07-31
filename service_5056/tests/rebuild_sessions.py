"""Rebuild results/audit_<v>/ for all 16 archive variants (step03 -> step04 -> step05).

Slow (rembg segmentation on 3 x 12 MP images per variant). test_export.py only needs
step03/step04 to exist; it re-runs step05 itself, so this is a one-off.
"""
import os
import sys
import json
import shutil
import subprocess

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REF_STEP02 = os.path.join(BASE, 'results', 'run_20260726_202818', 'step02_result.json')
VARIANTS = [f"v{i}" for i in range(1, 17)]

if __name__ == '__main__':
    only = sys.argv[1:] or VARIANTS
    for v in only:
        s = f"audit_{v}"
        d = os.path.join(BASE, 'results', s)
        os.makedirs(d, exist_ok=True)
        shutil.copy(REF_STEP02, d)
        json.dump({"variant": v}, open(os.path.join(d, 'config.json'), 'w', encoding='utf-8'))
        for step in ('step03_segment_monochrome', 'step04_fit_3d_pose', 'step05_visualize_export'):
            r = subprocess.run([sys.executable, os.path.join(BASE, 'scripts', f'{step}.py'),
                                '--session', s], cwd=BASE, capture_output=True, text=True)
            if r.returncode != 0:
                print(f"{v}: {step} FAILED\n{r.stdout}\n{r.stderr}")
                break
        else:
            print(f"{v}: ok")
