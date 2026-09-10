"""Метод 3 (обговорено 2026-09-10) - аналог Методу 2 (той самий принцип
"взяти готовий еталонний .LS і жорстко підігнати під розмітку лінії
згину"), але з ДВОМА відмінностями за прямою вимогою користувача:

  1. Еталон ОДИН, фіксований - TOR_XL_1009.LS (лежить поруч у цій же
     папці). Це "чистий" .LS прямо з програми, без ручної підстройки
     оператором (на відміну від archive/vN/ground_truth.ls, куди могли
     потрапити операторські правки) - тому жодного вибору форми (--shape)
     тут нема, тільки один еталон.
  2. Жодного згладжування і жодного офсету лінії згину (fold_radial/
     fold_up) - той самий урок, що й у Методі 2 (methods/shape_template/
     run.py, дивись його докстрінг): згладжування без розбору тупить
     реальну кривизну (вуха), а офсет лінії згину робить результат
     систематично іншим за те, що дає "Підігнати за розміткою". Тут з
     самого початку без обох - чистий жорсткий 7-параметричний фіт (той
     самий принцип, що й у /fit_marks), більше нічого.

Контракт (той самий, що й для будь-якого методу):
    python run.py --variant <ім'я> --in <папка> --out <шлях до .LS>

Розмітка (крок 2) для ЦЬОГО методу ОБОВ'ЯЗКОВА (back І left) - як і в
Методі 2, тут нема іншого джерела інформації про позу взагалі.

Standoff еталона підбирається так само, як і для будь-якого архівного
варіанта (geometry.fit_standoff проти того самого анкера v1, що й
pipeline/neighbor.py) - TOR_XL_1009.LS просто не зареєстрований в
archive/, тому викликаємо fit_standoff напряму, а не через
neighbor.standoff(name).
"""
import argparse
import os
import sys

import cv2
import numpy as np
from scipy.optimize import least_squares

BASE = os.path.dirname(os.path.abspath(__file__))
SERVICE_ROOT = os.path.abspath(os.path.join(BASE, '..', '..'))
sys.path.insert(0, SERVICE_ROOT)

REF_PATH = os.path.join(BASE, 'TOR_XL_1009.LS')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--variant', required=True)
    ap.add_argument('--in', dest='in_dir', default=None)
    ap.add_argument('--out', required=True)
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

    if not os.path.exists(REF_PATH):
        print(f'Еталонний файл не знайдено: {REF_PATH}', file=sys.stderr)
        sys.exit(1)

    recipe = gen.load_recipe(args.recipe)
    calib_dir = os.path.join(gen.CALIB, 'cameras', recipe['camera_calibration'])
    cams = contour_fit.marker_cams(calib_dir)

    prog = geometry.load(REF_PATH)
    standoff, _ = geometry.fit_standoff(prog, neighbor._anchor_surface())
    cut_full, ids_full = geometry.cut_surface(prog, standoff, full=True)
    cut_full = np.asarray(cut_full, dtype=float)
    axis_by_id = dict(zip(ids_full, geometry.tool_axes(prog, ids_full)))
    center = cut_full.mean(0)

    # Фітуємо ЛИШЕ по "справжньому" ободу (без точки підводу/пірсингу) - той
    # самий cut_ring(), яким усюди в проєкті вже фільтрується ця точка перед
    # порівнянням форм.
    cut_ring, _ = geometry.cut_surface(prog, standoff, full=False)
    cut_ring = np.asarray(cut_ring, dtype=float)

    # Без офсету лінії згину, без згладжування - пряма лінія реза проти
    # розмітки, той самий член невязки, що й у /fit_marks.
    def mark_dist_mm(P):
        out = []
        for w in used:
            pc, f = cams[w]
            uv, z = CM.project(P, pc[:3], pc[3:6], f)
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
        return mark_dist_mm(P)

    # Ті самі межі, що й у Методі 2 та /fit_marks - проти виродженого
    # розв'язку (лінія, що схлопується в точку, теж мінімізує симетричну
    # відстань).
    bounds = (np.r_[[-0.6] * 3, [-150.0] * 3, -0.35], np.r_[[0.6] * 3, [150.0] * 3, 0.35])
    r = least_squares(resid, np.zeros(7), method='trf', bounds=bounds, max_nfev=1500)
    R = cv2.Rodrigues(r.x[:3])[0]
    s = float(np.exp(r.x[6]))
    shift = r.x[3:6]

    def transform(X):
        return (X - center) @ R.T * s + center + shift

    # cut_by_id з ПОВНОГО (full=True) набору - у вивід потрібна й точка
    # підводу/пірсингу. Жодного "прилипання" до CAD-сітки - лише жорсткий
    # поворот+зсув+масштаб, той самий для КОЖНОЇ точки (той самий урок з
    # Методу 2 - on_cad рухав кожну точку кільця на 7-16мм, не лише пірсинг).
    cut_by_id_full = dict(zip(ids_full, cut_full))

    def point_fn(point_id, orig_xyz):
        if point_id not in cut_by_id_full:
            return None
        return transform(cut_by_id_full[point_id]) + geometry.NOMINAL_STANDOFF * axis_by_id[point_id]

    out_dir = os.path.dirname(args.out) or '.'
    os.makedirs(out_dir, exist_ok=True)
    tmp_out = ls_template.write_ls(REF_PATH, out_dir, point_fn, f'method3_{args.variant}')
    if tmp_out != args.out:
        os.replace(tmp_out, args.out)

    final_residual = float(mark_dist_mm(transform(cut_ring)).mean())
    print(f'rot(deg)={np.degrees(r.x[:3]).tolist()} scale={s*100:.2f}% '
          f'shift={shift.tolist()} residual_mm={final_residual:.3f}', file=sys.stderr)
    print(args.out)


if __name__ == '__main__':
    main()
