"""Numerical parity check: does pipeline/generate.py reproduce
service_3030/export_cad_ls_contour.py's output, point for point?

Run from service_2021/ with the shared venv:

    python -m pipeline.parity_check v1 v3 v4 ...

For each variant: runs the OLD pipeline (unmodified, via subprocess) and the NEW one
(pipeline.generate), then compares cut-line points via the already-verified
../ls_points.read_ring(). Requires max per-point deviation <= 0.01mm (not exactly 0.0,
to allow for floating-point summation-order differences) - see
service_2021/README.md's parity section for why.
"""
import json
import os
import subprocess
import sys

import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
SERVICE_2021 = os.path.abspath(os.path.join(BASE, '..'))
SERVICE_3030 = os.path.abspath(os.path.join(SERVICE_2021, '..', 'service_3030'))
OLD_OUT = os.path.join(SERVICE_3030, 'out')
PYTHON = os.path.abspath(os.path.join(SERVICE_2021, '..', 'service_5056', 'venv',
                                      'Scripts', 'python.exe'))
THRESHOLD_MM = 0.01

sys.path.insert(0, SERVICE_2021)
import ls_points  # noqa: E402


def run_old(variant):
    """Run the untouched old pipeline for `variant`, return its output .LS path."""
    r = subprocess.run([PYTHON, 'export_cad_ls_contour.py', variant],
                       cwd=SERVICE_3030, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    if r.returncode != 0:
        raise RuntimeError(f'old pipeline failed for {variant}:\n{r.stdout}\n{r.stderr}')
    for line in r.stdout.splitlines():
        line = line.strip()
        if line.startswith(f'{variant}:') and line.endswith('.LS'):
            return line.split(':', 1)[1].strip()
    # fall back: newest matching file in out/
    cands = [f for f in os.listdir(OLD_OUT) if f.endswith('.LS')]
    cands.sort(key=lambda f: os.path.getmtime(os.path.join(OLD_OUT, f)), reverse=True)
    return os.path.join(OLD_OUT, cands[0])


def compare(old_path, new_path):
    old = ls_points.read_ring(old_path)
    new = ls_points.read_ring(new_path)
    old_ids = [p[0] for p in old]
    new_ids = [p[0] for p in new]
    if old_ids != new_ids:
        return dict(ok=False, reason=f'point ids differ: old={old_ids} new={new_ids}')
    old_cut = {p[0]: np.array(p[2]) for p in old}
    new_cut = {p[0]: np.array(p[2]) for p in new}
    d = np.array([np.linalg.norm(old_cut[i] - new_cut[i]) for i in old_ids])
    return dict(ok=bool(d.max() <= THRESHOLD_MM), n=len(d),
               mean_mm=float(d.mean()), max_mm=float(d.max()))


def main(variants):
    from pipeline import generate
    results = {}
    for v in variants:
        try:
            print(f'{v}: running old pipeline...', flush=True)
            old_path = run_old(v)
            print(f'{v}: running new pipeline...', flush=True)
            new_path, _ = generate.generate(v, 'production_2026-08-27')
            r = compare(old_path, new_path)
        except Exception as e:
            r = dict(ok=False, skipped=True, reason=f'{type(e).__name__}: {e}')
        results[v] = r
        status = 'OK' if r.get('ok') else 'MISMATCH'
        print(f'{v}: {status} - {r}', flush=True)

    tested = {v: r for v, r in results.items() if not r.get('skipped')}
    skipped = {v: r for v, r in results.items() if r.get('skipped')}
    out = dict(threshold_mm=THRESHOLD_MM, results=results,
              tested_ok=all(r.get('ok') for r in tested.values()) if tested else False,
              n_tested=len(tested), n_skipped=len(skipped))
    report_path = os.path.join(SERVICE_2021, 'calib', 'parity_report_2026-08-27.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)
    print(f'\nTested OK: {out["tested_ok"]} ({out["n_tested"]} tested, {out["n_skipped"]} skipped)')
    print(f'Report written to {report_path}')
    return out


if __name__ == '__main__':
    main(sys.argv[1:])
