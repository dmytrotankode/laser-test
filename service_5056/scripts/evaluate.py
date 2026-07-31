"""Honest accuracy report for the whole pipeline.

Replaces eval_all_variants.py, which measured point-to-point distance by P-index (a
metric that inflates the error 1.4x-9x because a point sliding ALONG the cut path is
harmless) on a trajectory step05 no longer even exports.

Three rules baked in, because their absence is what made the old numbers misleading:

1. Every table carries the DO-NOTHING baseline. "3.9 mm" means nothing until you know
   that not correcting at all costs 8.0 mm on the same variant.
2. Training variants are reported as SELF-MATCH, not as accuracy. k-NN picks the
   variant itself at distance ~0.005 and replays its own recorded file, so "0.00 mm"
   is a tautology. It is printed, but never averaged into a headline figure.
3. Held-out variants are the only real accuracy numbers and are labelled as such.

    python scripts/evaluate.py                 # report from existing results/audit_*
    python scripts/evaluate.py --rebuild       # re-run the pipeline first (slow)
"""
import os
import sys
import json
import argparse
import subprocess
import numpy as np

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import lsgeom          # noqa: E402
import dataset         # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def gt_contour(v):
    return lsgeom.load(os.path.join(BASE, 'input', 'archive', v, 'ground_truth.ls')).contour_xyz()[0]


def export_contour(v):
    p = os.path.join(BASE, 'results', f'audit_{v}', 'current_helmet.ls')
    if not os.path.exists(p):
        return None, ["export missing"]
    prog = lsgeom.load(p)
    probs = prog.problems()
    if len(prog.order) < 90:
        probs.append(f"only {len(prog.order)} motion instructions")
    return prog.contour_xyz()[0], probs


def tool_axis(v):
    prog = lsgeom.load(os.path.join(BASE, 'input', 'archive', v, 'ground_truth.ls'))
    _, cont, _ = prog.split_path()
    wpr = np.array([prog.points[i][3:] for i in cont])
    # Fanuc W/P/R -> tool +Z, which points AWAY from the helmet (verified: 18.6 deg
    # off the outward radial, 17 deg below horizontal, matching the programmed 15 deg
    # cutting angle). A positive shift along it means a larger standoff.
    return np.array([lsgeom.rot_from_ypr(r, p, w).apply([0, 0, 1.0])
                     for w, p, r in wpr])


def split_normal_tangential(pred, v):
    """Decompose the error into standoff (along the nozzle axis) and the rest.

    The two mean very different things on the shop floor: a standoff error changes the
    cut depth/kerf, an in-surface error moves the cut line on the part."""
    G = gt_contour(v)
    z = tool_axis(v)
    n = min(len(pred), len(z))
    d = lsgeom.curve_distance(pred, G)
    # signed component along the tool axis, via the nearest point on the GT curve
    A, B = G, np.roll(G, -1, axis=0)
    AB = B - A
    den = (AB * AB).sum(1)
    den[den == 0] = 1e-12
    AP = pred[:, None, :] - A[None, :, :]
    t = np.clip((AP * AB[None, :, :]).sum(2) / den[None, :], 0, 1)
    close = A[None, :, :] + t[:, :, None] * AB[None, :, :]
    j = np.linalg.norm(pred[:, None, :] - close, axis=2).argmin(1)
    vec = pred - close[np.arange(len(pred)), j]
    along = (vec[:n] * z[:n]).sum(1)
    return d, along


def report():
    rows = []
    for v in dataset.ALL:
        pred, probs = export_contour(v)
        G = gt_contour(v)
        base = lsgeom.curve_distance(gt_contour('v1'), G)     # do nothing: v1's file as-is
        row = dict(v=v, probs=probs, base_mean=float(base.mean()))
        if pred is not None and not probs:
            d, along = split_normal_tangential(pred, v)
            row.update(mean=float(d.mean()), p90=float(np.percentile(d, 90)),
                       max=float(d.max()), standoff=float(along.mean()),
                       standoff_sd=float(along.std()))
            s4p = os.path.join(BASE, 'results', f'audit_{v}', 'step04_result.json')
            if os.path.exists(s4p):
                s4 = json.load(open(s4p, encoding='utf-8'))
                row['nb'] = "+".join(s4['selected_neighbors'])
                row['dist'] = s4['nearest_distance']
                row['oor'] = s4['out_of_range']
        rows.append(row)

    def block(title, names, note=""):
        print(f"\n{title}")
        if note:
            print(f"  {note}")
        print(f"  {'вар':5s}{'соседи k-NN':>14s}{'дист':>7s}{'вне':>5s}"
              f"{'без корр.':>11s}{'пайплайн':>10s}{'p90':>8s}{'макс':>8s}"
              f"{'зазор':>8s}")
        for r in (x for x in rows if x['v'] in names):
            if r['probs']:
                print(f"  {r['v']:5s}  СЛОМАН: {'; '.join(r['probs'])}")
                continue
            print(f"  {r['v']:5s}{r.get('nb', '?'):>14s}{r.get('dist', 0):7.2f}"
                  f"{('да' if r.get('oor') else 'нет'):>5s}"
                  f"{r['base_mean']:11.2f}{r['mean']:10.2f}{r['p90']:8.2f}{r['max']:8.2f}"
                  f"{r['standoff']:+8.2f}")

    print("=" * 88)
    print("ТОЧНОСТЬ ПАЙПЛАЙНА  (метрика: точка -> кривая записи оператора, мм)")
    print("=" * 88)

    block("ОБУЧАЮЩИЕ — это САМОСОВПАДЕНИЕ, а не точность",
          dataset.TRAIN,
          "k-NN находит сам себя (дистанция ~0.005) и отдаёт его же файл. 0.00 здесь\n"
          "  означает только что экспорт не портит данные, и в средние не идёт.")

    block("HELD-OUT — единственные настоящие цифры точности",
          dataset.HELDOUT)

    block("PENDING — исправные, но с константой зазора (ждут ответа на Q1)",
          dataset.PENDING,
          "их ошибка почти целиком объясняется одной константой смещения вдоль сопла,\n"
          "  которую жёсткая модель выразить не может — см. PLAN.md раздел 4.")

    ok = [r for r in rows if r['v'] in dataset.HELDOUT and not r['probs']]
    if ok:
        print("\n" + "-" * 88)
        b = np.mean([r['base_mean'] for r in ok])
        m = np.mean([r['mean'] for r in ok])
        print(f"ИТОГ по held-out ({', '.join(r['v'] for r in ok)}): "
              f"без коррекции {b:.2f} мм -> пайплайн {m:.2f} мм "
              f"({b / m:.2f}x лучше)" if m > 0 else "")
        print("-" * 88)

    broken = [r['v'] for r in rows if r['probs']]
    if broken:
        print(f"\nВНИМАНИЕ: нерабочие экспорты: {broken}")
        return 1
    return 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--rebuild', action='store_true',
                    help="перегенерировать results/audit_* (медленно, rembg на 48 фото)")
    a = ap.parse_args()
    if a.rebuild:
        subprocess.run([sys.executable, os.path.join(BASE, 'tests', 'rebuild_sessions.py')],
                       cwd=BASE, check=True)
    sys.exit(report())
