"""Verify that segmentation still produces the pixel features the calibration assumes.

    python scripts/selfcheck.py            # a fast 3-variant spot check
    python scripts/selfcheck.py --full     # every variant in the library

KNN_LIBRARY stores, for each archive variant, the 8 pixel features its photos produced
when the constants were fitted. Re-segmenting those same photos must reproduce those
numbers. If it does not, something upstream of the maths has moved - a different rembg
model, a different OpenCV, a re-encoded PNG - and every pose the system outputs is
quietly wrong. Nothing else in the pipeline would notice: the arithmetic still runs.

Tolerance is deliberately tight. The whole calibrated spread of the tightest feature
(back_cx) is 4.7 px across the entire library, so a 1 px drift is already a tenth of
the working range, and the Otsu fallback moves it by 43 px.
"""
import os
import sys
import argparse
import numpy as np

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))

import cv2                                    # noqa: E402
from step03_segment_monochrome import segment_image   # noqa: E402
from step04_fit_3d_pose import KNN_LIBRARY, feat8     # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOL_PX = 0.5
NAMES = ["back_cx", "back_cy", "left_cx", "left_cy", "left_top", "top_cx", "top_cy", "top_top"]


def measure(variant):
    out = {}
    for name, is_top in (("back", False), ("left", False), ("top", True)):
        path = os.path.join(BASE, 'input', 'archive', variant, f'{name}.png')
        mask, _, _, _, backend = segment_image(path, is_top)
        M = cv2.moments(mask)
        if M["m00"] == 0:
            raise RuntimeError(f"{variant}/{name}: empty mask")
        clipped = mask.copy()
        clipped[:100, :] = 0
        out[name] = (M["m10"] / M["m00"], M["m01"] / M["m00"],
                     float(np.min(np.where(clipped > 0)[0])))
    return out, backend


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--full', action='store_true')
    a = ap.parse_args()

    variants = sorted(KNN_LIBRARY) if a.full else ["v1", "v5", "v12"]
    spread = np.ptp(np.array([feat8(e["ref_cm"]) for e in KNN_LIBRARY.values()]), axis=0)

    print(f"Проверка сегментации против калибровочных констант (допуск {TOL_PX} px)\n")
    bad = 0
    for v in variants:
        got, backend = measure(v)
        ref = feat8(KNN_LIBRARY[v]["ref_cm"])
        cur = feat8(got)
        d = cur - ref
        worst = int(np.abs(d).argmax())
        ok = np.abs(d).max() <= TOL_PX
        bad += not ok
        print(f"  {'OK  ' if ok else 'СБОЙ'} {v:4s} [{backend}] "
              f"макс. отклонение {abs(d[worst]):6.2f} px по {NAMES[worst]} "
              f"(весь калиброванный разброс этого признака {spread[worst]:.1f} px)")
        if not ok:
            for k, n in enumerate(NAMES):
                if abs(d[k]) > TOL_PX:
                    print(f"          {n:9s} ожидалось {ref[k]:9.2f}  получено {cur[k]:9.2f}"
                          f"  разница {d[k]:+7.2f} px")

    print()
    if bad:
        print(f"{bad} вариант(ов) не сошлись. Сегментация изменилась — константы "
              f"KNN_LIBRARY/W_calib больше не применимы, поза будет неверной.")
        return 1
    print("Сегментация воспроизводит калибровку. Константы применимы.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
