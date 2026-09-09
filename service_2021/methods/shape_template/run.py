"""Метод 2 (обговорено 2026-09-08, доопрацьовано 2026-09-08 і 2026-09-09 за
реальним тестуванням) - береться ГОТОВИЙ еталонний .LS для однієї з двох
відомих форм заготовки (яка саме archive/vN відповідає якій формі -
calib/shape_templates.json, НЕ f'v{shape}' - форма "4" це archive/v22 чи
v23, а не v4) і підганяється під розмітку лінії згину (крок 2) двома
ракурсами (back+left).

Контракт (той самий, що й для будь-якого методу) + один додатковий параметр:
    python run.py --variant <ім'я> --in <папка> --out <шлях до .LS> --shape <1|4>

Розмітка (крок 2) для ЦЬОГО методу ОБОВ'ЯЗКОВА (back І left) - на відміну
від Методу 1, тут нема іншого джерела інформації про позу взагалі.

Історія цього файлу (щоб не наступити на ті самі граблі):
  - Перша версія рахувала лише масштаб+зсув, БЕЗ повороту - "максимально
    просто, подивимось". Реальний тест показав це недостатнім: невязка до
    розмітки з поворотом падає в 2-4 рази (перевірено на реальних даних:
    1.4мм->0.6мм, 2.9мм->0.6мм) - тому тепер повний 7-параметричний фіт
    (поворот+зсув+масштаб), той самий принцип, що й у /fit_marks.
  - Перша версія напряму переносила точки еталонного .LS (з їхньою "як
    записано" формою) - точка №2 (пірсинг/підвід, не частина ободу шлема,
    див. коментар у geometry.py про "old batch" P[2] і cut_ring()) через
    це стирчала гострим зламом. Спроба №1 - окремий відступ від сусіда,
    спроба №2 - "прилипання" (on_cad) кожної точки до найближчої точки
    ПІДІГНАНОГО CAD-обода (як робить Метод 1) - ОБИДВІ прибрані.
  - on_cad ВИЯВИВСЯ ГІРШИМ БАГОМ, НІЖ ГОРА (реальний звіт 2026-09-09,
    nabir-0909-002: "знаходить далеко від лінії згину, Підігнати за
    розміткою сильно змінює"). Перевірено числами: on_cad прилипляє НЕ
    ЛИШЕ пірсинг, а КОЖНУ точку кільця до найближчої вершини CAD-сітки -
    на цьому наборі це зсувало точки в середньому на 7.5-8.9мм (максимум
    12-16мм) від щойно підігнаної під розмітку позиції, бо архівний
    "справжній" обід і теоретична CAD-сітка НЕ співпадають ідеально самі
    по собі, незалежно від пози. Власний друкований "residual_mm" це
    маскував - він рахувався по cut_ring ДО on_cad, тобто завжди показував
    гарну цифру (0.4-0.6мм) незалежно від того, що реально писалось у файл.
  - Тепер - БЕЗ жодного прилипання: усі точки (включно з пірсингом) просто
    жорстко трансформуються (поворот+зсув+масштаб) з їхньої позиції в
    еталоні. "Гора" від пірсингу від цього повертається (це РЕАЛЬНА,
    завжди присутня в самому еталонному файлі особливість, ~9-17мм залежно
    від варіанта, не наша обробка - користувач сам перевірив це відкривши
    v1/v8 напряму) - але кільце тепер дійсно там, де показала розмітка.
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

    from pipeline import (generate as gen, contour_fit, camera_model as CM, geometry,
                           line_marks, neighbor, ls_template)

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

    # НЕ f'v{shape}' - реальна плутанина: "форма 4" це archive/v22 (чи v23),
    # а не archive/v4 (v4 - насправді форма 1, як і майже все інше в
    # архіві). Мапа - calib/shape_templates.json.
    shape_map_path = os.path.join(SERVICE_ROOT, 'calib', 'shape_templates.json')
    with open(shape_map_path, encoding='utf-8') as f:
        shape_map = json.load(f)
    ref_variant = shape_map.get(args.shape)
    if not ref_variant:
        print(f'Немає еталона для форми {args.shape} у {shape_map_path}', file=sys.stderr)
        sys.exit(1)
    ref_path = os.path.join(gen.ARCHIVE, ref_variant, 'ground_truth.ls')
    if not os.path.exists(ref_path):
        print(f'Еталонний файл для форми {args.shape} ({ref_variant}) не знайдено: {ref_path}', file=sys.stderr)
        sys.exit(1)

    prog = geometry.load(ref_path)
    standoff = neighbor.standoff(ref_variant)
    cut_full, ids_full = geometry.cut_surface(prog, standoff, full=True)
    cut_full = np.asarray(cut_full, dtype=float)
    axis_by_id = dict(zip(ids_full, geometry.tool_axes(prog, ids_full)))
    center = cut_full.mean(0)

    # Фітуємо ЛИШЕ по "справжньому" ободу (без точки підводу/пірсингу) - той
    # самий cut_ring(), яким усюди в проєкті вже фільтрується ця точка перед
    # порівнянням форм (див. geometry.cut_ring docstring). Інакше єдина ця
    # точка, що явно НЕ на гладкій лінії, тягне підгонку вбік.
    cut_ring, _ = geometry.cut_surface(prog, standoff, full=False)
    cut_ring = np.asarray(cut_ring, dtype=float)

    def mark_dist_mm(P, rad_local):
        fold = P + fold_radial * rad_local
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

    def resid(p7):
        R = cv2.Rodrigues(p7[:3])[0]
        s = np.exp(p7[6])
        P = (cut_ring - center) @ R.T * s + center + p7[3:6]
        return mark_dist_mm(P, contour_fit.radial(P))

    # Поворот (±35°) + зсув (±150мм, це старт "з нуля", не уточнення вже
    # майже вірної пози) + масштаб (74-135%) - ті самі межі й той самий
    # захист від виродженого розв'язку, що й у /fit_marks та /auto_pose.
    bounds = (np.r_[[-0.6] * 3, [-150.0] * 3, -0.35], np.r_[[0.6] * 3, [150.0] * 3, 0.35])
    r = least_squares(resid, np.zeros(7), method='trf', bounds=bounds, max_nfev=1500)
    R = cv2.Rodrigues(r.x[:3])[0]
    s = float(np.exp(r.x[6]))
    shift = r.x[3:6]

    def transform(X):
        return (X - center) @ R.T * s + center + shift

    # cut_by_id з ПОВНОГО (full=True) набору - у вивід потрібна й точка
    # підводу/пірсингу (не лише "гладкий" обід, який ми зафітили вище).
    cut_by_id_full = dict(zip(ids_full, cut_full))

    # Жодного "прилипання" до CAD-сітки (on_cad) - лише жорсткий поворот+
    # зсув+масштаб, той самий для КОЖНОЇ точки. Саме on_cad і був реальним
    # багом (див. докстрінг): він рухав кожну точку кільця, не лише пірсинг.
    def point_fn(point_id, orig_xyz):
        if point_id not in cut_by_id_full:
            return None
        return transform(cut_by_id_full[point_id]) + geometry.NOMINAL_STANDOFF * axis_by_id[point_id]

    out_dir = os.path.dirname(args.out) or '.'
    os.makedirs(out_dir, exist_ok=True)
    tmp_out = ls_template.write_ls(ref_path, out_dir, point_fn, f'shape{args.shape}_{args.variant}')
    if tmp_out != args.out:
        os.replace(tmp_out, args.out)

    final_residual = float(mark_dist_mm(transform(cut_ring), contour_fit.radial(transform(cut_ring))).mean())
    print(f'shape={args.shape} rot(deg)={np.degrees(r.x[:3]).tolist()} scale={s*100:.2f}% '
          f'shift={shift.tolist()} residual_mm={final_residual:.3f}', file=sys.stderr)
    print(args.out)


if __name__ == '__main__':
    main()
