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
    # lead-in excluded: the operator places the pierce point for the burn-through, not
    # from the part geometry, and its scatter (7.3-24.1 mm off the ring, against 9.6-10.2
    # for every other step) would otherwise be the entire max-error figure.
    return lsgeom.cut_ring(lsgeom.load(
        os.path.join(BASE, 'input', 'archive', v, 'ground_truth.ls')))[0]


def export_contour(v):
    p = os.path.join(BASE, 'results', f'audit_{v}', 'current_helmet.ls')
    if not os.path.exists(p):
        return None, ["export missing"]
    prog = lsgeom.load(p)
    probs = prog.problems()
    if len(prog.order) < 90:
        probs.append(f"only {len(prog.order)} motion instructions")
    return lsgeom.cut_ring(prog)[0], probs


def gt_contour_and_axis(v):
    """GT contour points plus the nozzle axis at each of them.

    Fanuc W/P/R -> tool +Z, which points AWAY from the helmet (verified: 18.6 deg off
    the outward radial, 17 deg below horizontal, matching the programmed 15 deg cutting
    angle). A positive shift along it means the nozzle sits further from the part."""
    prog = lsgeom.load(os.path.join(BASE, 'input', 'archive', v, 'ground_truth.ls'))
    P, cont = lsgeom.cut_ring(prog)
    Z = np.array([lsgeom.rot_from_ypr(r, p, w).apply([0, 0, 1.0])
                  for w, p, r in (prog.points[i][3:] for i in cont)])
    return P, Z


def split_normal_tangential(pred, v):
    """Decompose the error into standoff (along the nozzle axis) and the rest.

    The two mean very different things on the shop floor: a standoff error changes the
    cut depth, an in-surface error moves the cut line on the part.

    The nozzle axis is taken at the MATCHED GT point, not at the same list index. The
    export is built from the nearest neighbour's template, which in general starts its
    contour at a different physical place than the variant's own recording, so pairing
    by index silently compares against an axis from elsewhere on the ring."""
    G, Z = gt_contour_and_axis(v)
    d = lsgeom.curve_distance(pred, G)

    A, B = G, np.roll(G, -1, axis=0)
    AB = B - A
    den = (AB * AB).sum(1)
    den[den == 0] = 1e-12
    AP = pred[:, None, :] - A[None, :, :]
    t = np.clip((AP * AB[None, :, :]).sum(2) / den[None, :], 0, 1)
    close = A[None, :, :] + t[:, :, None] * AB[None, :, :]
    j = np.linalg.norm(pred[:, None, :] - close, axis=2).argmin(1)
    k = np.arange(len(pred))
    vec = pred - close[k, j]
    # axis interpolated along the matched segment, same as the closest point itself
    z = Z[j] * (1 - t[k, j])[:, None] + Z[(j + 1) % len(Z)] * t[k, j][:, None]
    z /= np.linalg.norm(z, axis=1, keepdims=True)
    along = (vec * z).sum(1)
    return d, along


def fixed_baselines():
    """Every honest "do nothing" opponent: run one fixed program on every helmet.

    Which fixed program is a CHOICE, and it moves the answer a lot - on held-out the
    range is 4.36 to 7.17 mm. Reporting a single convenient one would be cherry-picking
    in whichever direction the author preferred, so the report shows the range and uses
    the hardest opponent as the headline.

    Both the candidates and the selection criteria use TRAIN only: scoring candidates
    against held-out would pick the baseline using knowledge our own model is not
    allowed to have, and a baseline tuned on the test set is not a baseline."""
    out = {}
    for c in dataset.TRAIN:
        A = gt_contour(c)
        tr = [float(lsgeom.curve_distance(A, gt_contour(v)).mean())
              for v in dataset.TRAIN if v != c]
        out[c] = dict(train_mean=float(np.mean(tr)), train_worst=float(max(tr)))
    by_worst = min(out, key=lambda c: out[c]['train_worst'])
    by_mean = min(out, key=lambda c: out[c]['train_mean'])
    return out, by_worst, by_mean


BASELINES, FIXED, FIXED_BY_MEAN = fixed_baselines()


def report():
    rows = []
    for v in dataset.ALL:
        pred, probs = export_contour(v)
        G = gt_contour(v)
        # "do nothing" = run one fixed program on every helmet. Which fixed program is
        # a choice, and picking a bad one would flatter us, so report the BEST possible
        # one: the training variant whose trajectory minimises the worst-case error
        # across all variants (computed once in best_fixed()).
        base = lsgeom.curve_distance(gt_contour(FIXED), G)
        row = dict(v=v, probs=probs, base_mean=float(base.mean()),
                   base_alt={c: float(lsgeom.curve_distance(gt_contour(c), G).mean())
                             for c in dataset.TRAIN})
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
    print("\n«без корр.» = одна фиксированная программа на все шлемы, без коррекции вообще.")
    ho = [r for r in rows if r['v'] in dataset.HELDOUT]
    spread = {c: np.mean([r['base_alt'][c] for r in ho]) for c in dataset.TRAIN}
    print(f"  В колонке — САМЫЙ СИЛЬНЫЙ такой оппонент ({FIXED}: лучший по худшему случаю")
    print(f"  на обучающих). Выбор фиксированной программы сильно двигает ответ, поэтому")
    print(f"  ниже приведён весь диапазон, а не одна удобная цифра.")
    print("«зазор» = систематическое смещение вдоль оси сопла: + значит наша траектория")
    print("  дальше от шлема, чем поставил оператор. Ось берётся в сопоставленной точке")
    print("  кривой оператора, а не по индексу списка.")

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
        print(f"ИТОГ по held-out ({', '.join(r['v'] for r in ok)}): пайплайн {m:.2f} мм")
        print(f"  против «ничего не делать», в зависимости от выбора фикс. программы:")
        print(f"    самый сильный оппонент  {FIXED:>4s}: {spread[FIXED]:5.2f} мм  -> выигрыш {spread[FIXED] / m:.2f}x")
        print(f"    лучший по ср. на TRAIN  {FIXED_BY_MEAN:>4s}: {spread[FIXED_BY_MEAN]:5.2f} мм  -> выигрыш {spread[FIXED_BY_MEAN] / m:.2f}x")
        wc = max(spread, key=spread.get)
        print(f"    худший выбор            {wc:>4s}: {spread[wc]:5.2f} мм  -> выигрыш {spread[wc] / m:.2f}x")
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
