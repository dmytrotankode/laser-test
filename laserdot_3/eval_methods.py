"""Порівняння методів розрахунку на наборах, де відомий правильний .LS (14.10).

Збирає папку --in ТАК САМО, як сервіс (app.py:_stage_method_input: фото, камери
рецепта набору, розмітка), запускає методи як окремі процеси і міряє відстань
кожної точки результату до ЛІНІЇ правильного кільця (archive/<набір>/ground_truth.ls).

    python eval_methods.py                      # набори за замовчуванням
    python eval_methods.py nabir-1005-001 v21   # вибрані
"""
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from scipy.spatial import cKDTree

BASE = os.path.dirname(os.path.abspath(__file__))
S21 = os.path.abspath(os.path.join(BASE, '..', 'service_2021'))
sys.path.insert(0, S21)
import ls_points  # noqa: E402
from pipeline import generate as gen  # noqa: E402

PY = sys.executable
RUNS = [('Метод 3', 'methods/method3/run.py', []),
        ('М4 (зараз)', 'methods/method4/run.py', []),
        ('М4 згин +2.3', 'methods/method4/run.py', ['--fold', '2.3']),
        ('М4 згин +1.5', 'methods/method4/run.py', ['--fold', '1.5'])]
DEFAULT_SETS = ['nabir-1005-001', 'nabir-1005-002', 'v21', 'v22', 'v23', 'v24', 'v25']


def stage(variant):
    recipe = gen.recipe_for(variant)
    calib_dir = os.path.join(gen.CALIB, 'cameras', recipe['camera_calibration'])
    d = tempfile.mkdtemp(prefix=f'eval_{variant}_')
    for v in ('back', 'left', 'top'):
        for src, dst in ((os.path.join(gen.ARCHIVE, variant, f'{v}.png'), f'{v}.png'),
                         (os.path.join(calib_dir, f'cam_{v}.npy'), f'cam_{v}.npy')):
            if os.path.exists(src):
                shutil.copyfile(src, os.path.join(d, dst))
    for v in ('back', 'left'):
        src = os.path.join(S21, 'lines', f'{variant}_{v}.json')
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(d, f'marks_{v}.json'))
    return d


def dense(R, n=3000):
    Q = np.r_[R, R[:1]]
    dd = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
    t = np.linspace(0, dd[-1], n, endpoint=False)
    return np.c_[[np.interp(t, dd, Q[:, i]) for i in range(3)]].T


def ring(p):
    return np.array([q[2] for q in ls_points.read_ring(p)])


if __name__ == '__main__':
    sets = sys.argv[1:] or DEFAULT_SETS
    out_dir = tempfile.mkdtemp(prefix='eval_out_')
    summary = {name: [] for name, _, _ in RUNS}
    for v in sets:
        truth = ring(os.path.join(gen.ARCHIVE, v, 'ground_truth.ls'))
        tree = cKDTree(dense(truth))
        in_dir = stage(v)
        rname = gen.recipe_name_for(v)
        print(f'=== {v} ({rname})')
        for name, entry, extra in RUNS:
            out = os.path.join(out_dir, f'{v}_{name.replace(" ", "_")}.LS')
            r = subprocess.run([PY, os.path.join(S21, entry), '--variant', v, '--in', in_dir, '--out', out,
                                '--recipe', rname] + extra, capture_output=True, text=True,
                               encoding='utf-8', errors='replace', env=dict(os.environ, PYTHONIOENCODING='utf-8'))
            if r.returncode != 0 or not os.path.exists(out):
                print(f'  {name:20s} ПОМИЛКА: {(r.stderr or r.stdout)[-300:]}')
                continue
            d = tree.query(ring(out))[0]
            summary[name].append(d)
            print(f'  {name:20s} середня {d.mean():.2f}, 90% {np.percentile(d, 90):.2f}, макс {d.max():.2f}, '
                  f'<1мм {np.mean(d < 1) * 100:3.0f}%, <2мм {np.mean(d < 2) * 100:3.0f}%')
        shutil.rmtree(in_dir, ignore_errors=True)
    print('=== РАЗОМ (середнє по наборах)')
    for name, ds in summary.items():
        if ds:
            print(f'  {name:20s} середня {np.mean([d.mean() for d in ds]):.2f}, '
                  f'найгірша точка (середнє по наборах) {np.mean([d.max() for d in ds]):.2f}, '
                  f'<2мм {np.mean([np.mean(d < 2) for d in ds]) * 100:.0f}%')
