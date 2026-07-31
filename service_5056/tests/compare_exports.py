"""Compare two exported .LS programs geometrically.

    python tests/compare_exports.py OLD.ls NEW.ls [--gt v6]

A plain text diff of two .LS files shows a change on every coordinate line and tells
you nothing about whether it matters. This reports how far the cutting path actually
moved, and - if a ground-truth variant is named - whether it moved towards or away
from the operator's recorded trajectory.
"""
import os
import sys
import argparse
import numpy as np

if hasattr(sys.stdout, "reconfigure"):        # Windows console defaults to cp1252
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import lsgeom  # noqa: E402


def describe(tag, prog):
    app, cont, ret = prog.split_path()
    probs = prog.problems()
    print(f"{tag}: {len(prog.points)} точек, {len(prog.order)} команд движения, "
          f"контур {len(cont)}, подвод {app} отвод {ret}"
          + (f"  ПРОБЛЕМЫ: {probs}" if probs else ""))
    return np.array([prog.points[i][:3] for i in cont]), cont


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--gt", help="вариант архива для сравнения с записью оператора, напр. v6")
    a = ap.parse_args()

    po, pn = lsgeom.load(a.old), lsgeom.load(a.new)
    print()
    A, ca = describe("СТАРЫЙ", po)
    B, cb = describe("НОВЫЙ ", pn)
    print()

    d = lsgeom.curve_distance(B, A)
    print(f"Насколько сместилась траектория (точка нового -> кривая старого):")
    print(f"  среднее {d.mean():6.3f}   медиана {np.median(d):6.3f}   "
          f"90% {np.percentile(d, 90):6.3f}   макс {d.max():6.3f} мм")

    common = sorted(set(po.points) & set(pn.points))
    per = {i: float(np.linalg.norm(po.xyz(i) - pn.xyz(i))) for i in common}
    frozen = [i for i in common if per[i] < 1e-9]
    print(f"  точек без изменений: {len(frozen)} {frozen if len(frozen) < 8 else ''}")
    worst = sorted(per, key=per.get, reverse=True)[:5]
    print("  наибольшее смещение по точкам: "
          + ", ".join(f"P[{i}] {per[i]:.2f}мм" for i in worst))

    if a.gt:
        gt_path = os.path.join(BASE, 'input', 'archive', a.gt, 'ground_truth.ls')
        G, _ = lsgeom.load(gt_path).contour_xyz()
        eo = lsgeom.curve_distance(A, G)
        en = lsgeom.curve_distance(B, G)
        print()
        print(f"Ошибка до записи оператора ({a.gt}):")
        print(f"  СТАРЫЙ  среднее {eo.mean():6.3f}  макс {eo.max():6.3f} мм")
        print(f"  НОВЫЙ   среднее {en.mean():6.3f}  макс {en.max():6.3f} мм")
        delta = en.mean() - eo.mean()
        verdict = "лучше" if delta < -0.05 else ("хуже" if delta > 0.05 else "без изменений")
        print(f"  итог: {verdict} ({delta:+.3f} мм по среднему)")
    print()


if __name__ == "__main__":
    main()
