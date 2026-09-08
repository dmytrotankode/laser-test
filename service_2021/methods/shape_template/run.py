"""Метод 2 (обговорено 2026-09-08) - МАКСИМАЛЬНО просто, "подивимось який
результат дасть": жодного пошуку сусіда, жодного силуету/контуру top, жодної
CAD-моделі. Береться ГОТОВИЙ еталонний .LS для однієї з двох відомих форм
заготовки (archive/v1 або archive/v4 - самі ці .LS НЕ змінюються, форма
лінії реза не підганяється, лише переміщується) і підганяється під розмітку
лінії згину (крок 2) двома ракурсами (back+left) - ТІЛЬКИ масштаб і зсув,
БЕЗ повороту (свідоме спрощення, щоб подивитись, чи цього взагалі досить).

Доводиться на кроці 4 як завжди - цей метод лише дає СТАРТОВУ лінію, як і
Метод 1.

Контракт (той самий, що й для будь-якого методу) + один додатковий параметр:
    python run.py --variant <ім'я> --in <папка> --out <шлях до .LS> --shape <1|4>

Розмітка (крок 2) для ЦЬОГО методу ОБОВ'ЯЗКОВА (back І left) - на відміну
від Методу 1, тут нема іншого джерела інформації про позу взагалі.
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np
from scipy.optimize import least_squares

BASE = os.path.dirname(os.path.abspath(__file__))
SERVICE_ROOT = os.path.abspath(os.path.join(BASE, '..', '..'))
sys.path.insert(0, SERVICE_ROOT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--variant', required=True)
    ap.add_argument('--in', dest='in_dir', default=None)
    ap.add_argument('--out', required=True)
    ap.add_argument('--shape', required=True, choices=['1', '4'])
    ap.add_argument('--recipe', default='production_2026-08-27')
    args = ap.parse_args()

    from pipeline import generate as gen, contour_fit, camera_model as CM, geometry, line_marks

    var_marks = line_marks.load_marks().get(args.variant, {})
    used = [w for w in ('back', 'left') if w in var_marks]
    if len(used) < 2:
        print('Потрібна розмітка лінії згину з ОБОХ ракурсів (back і left) - '
              'у цього методу немає іншого джерела для пози.', file=sys.stderr)
        sys.exit(1)

    recipe = gen.load_recipe(args.recipe)
    fold_radial = recipe['constants']['fold_radial_mm']
    fold_up = recipe['constants']['fold_up_mm']
    calib_dir = os.path.join(gen.CALIB, 'cameras', recipe['camera_calibration'])
    cams = contour_fit.marker_cams(calib_dir)

    ref_variant = f'v{args.shape}'
    ref_path = os.path.join(gen.ARCHIVE, ref_variant, 'ground_truth.ls')
    if not os.path.exists(ref_path):
        print(f'Немає еталонного файлу для форми {args.shape}: {ref_path}', file=sys.stderr)
        sys.exit(1)

    prog = geometry.load(ref_path)
    from pipeline import neighbor
    standoff = neighbor.standoff(ref_variant)
    cut_full, ids_full = geometry.cut_surface(prog, standoff, full=True)
    cut_full = np.asarray(cut_full, dtype=float)
    axis_by_id = dict(zip(ids_full, geometry.tool_axes(prog, ids_full)))
    cut_by_id = dict(zip(ids_full, cut_full))
    center = cut_full.mean(0)

    # radial() - напрямок ВІД ОСІ КУПОЛА, унітарний вектор; інваріантний до
    # рівномірного масштабу й зсуву навколо центроїда (сам центроїд теж
    # зсувається разом), тому рахувати його можна один раз із ЕТАЛОННОЇ
    # форми, а не з кожної проби p4 - реальна фізична товщина
    # fold_radial_mm/fold_up_mm лишається сталою в мм незалежно від того,
    # який scale підбирає оптимізатор (бо напрямок не залежить від scale).
    rad = contour_fit.radial(cut_full)

    def mark_dist_mm(P):
        fold = P + fold_radial * rad
        fold[:, 2] += fold_up
        out = []
        for w in used:
            pc, f = cams[w]
            uv, z = CM.project(fold, pc[:3], pc[3:6], f)
            vis = CM.near_arc(uv, z)
            marks_uv = contour_fit.resample(var_marks[w])
            d1 = np.abs(CM.dist_to_polyline(marks_uv, vis))
            d2 = np.abs(CM.dist_to_polyline(vis, marks_uv))
            out.append(np.concatenate([d1, d2]) * float(np.median(z)) / f)
        return np.concatenate(out)

    def resid(p4):
        s = np.exp(p4[0])
        P = (cut_full - center) * s + center + p4[1:4]
        return mark_dist_mm(P)

    # Лише масштаб (1 число) + зсув (3 числа) - СВІДОМО без повороту (реальна
    # вимога користувача: "максимально просто, подивимось який результат
    # дасть"). Межі - як і в /fit_marks, проти виродженого розв'язку
    # (схлопнута лінія теж тривіально мінімізує симетричну відстань), тут
    # трохи ширші по зсуву - це старт "з нуля" (позиція еталона), не
    # уточнення вже майже вірної пози.
    bounds = (np.r_[-0.35, [-150.0] * 3], np.r_[0.35, [150.0] * 3])
    r = least_squares(resid, np.zeros(4), method='trf', bounds=bounds, max_nfev=800)
    s = float(np.exp(r.x[0]))
    shift = r.x[1:4]

    def point_fn(point_id, orig_xyz):
        if point_id not in cut_by_id:
            return None
        p = cut_by_id[point_id]
        moved = (p - center) * s + center + shift
        return moved + geometry.NOMINAL_STANDOFF * axis_by_id[point_id]

    from pipeline import ls_template
    out_dir = os.path.dirname(args.out) or '.'
    os.makedirs(out_dir, exist_ok=True)
    tmp_out = ls_template.write_ls(ref_path, out_dir, point_fn, f'shape{args.shape}_{args.variant}')
    if tmp_out != args.out:
        os.replace(tmp_out, args.out)

    print(f'shape={args.shape} scale={s*100:.2f}% shift={shift.tolist()} '
          f'residual_mm={float(mark_dist_mm((cut_full - center) * s + center + shift).mean()):.3f}',
          file=sys.stderr)
    print(args.out)


if __name__ == '__main__':
    main()
