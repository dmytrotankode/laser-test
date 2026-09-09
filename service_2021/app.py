"""Сервис 2021: доводка траектории реза руками + сам расчёт (pipeline/).

Раньше сервис только читал и правил файл сцены, а расчёт .LS жил в 3030/5056.
С 27.08 расчёт перенесён внутрь (pipeline/, calib/, archive/, lines/) - см.
pipeline/generate.py и README.md, раздел про численную проверку (parity_report).
Старые сервисы не удалены и не тронуты, просто больше не используются здесь.

Отличие от 2020: там правится ПОЛОЖЕНИЕ МОДЕЛИ целиком (6 чисел на весь меш).
Здесь - ОТДЕЛЬНЫЕ ТОЧКИ кривой, по одной, так же как оператор в цеху правит
программу через пульт - точка за точкой, не общим сдвигом. Проверено на
реальной правке (V6->V6_2, 05.08): жёсткое движение объясняет только 26% того,
что оператор поменял, остальное - локальные правки отдельных точек.

Каждая точка помнит: исходное (расчётное) положение и тронута ли она. Это
важно для дообучения потом - учиться можно только на тронутых точках, нетронутая
не значит "проверено верно", значит "не показалось достаточно плохой, чтобы
возиться" (см. HANDOFF/переписку 26.08 про V6_2).

    start.bat        или        python app.py     (порт 2021)
"""
import os
import re
import sys
import io
import json
import datetime
import subprocess
import shutil

import cv2
import numpy as np
from flask import Flask, jsonify, render_template, send_from_directory, abort, request, send_file

import scene
import discover
import export_final
import build_scene

BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder='web/templates', static_folder='web/static')

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


@app.after_request
def no_cache(resp):
    if resp.mimetype in ('application/javascript', 'text/css', 'text/html'):
        resp.headers['Cache-Control'] = 'no-store'
    return resp


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/scenes')
def scenes():
    try:
        discover.scan_and_build()
    except Exception as e:
        print(f'discover: пропущено из-за ошибки - {type(e).__name__}: {e}')
    if not os.path.isdir(scene.SCENES):
        return jsonify([])
    out = []
    for d in sorted(os.listdir(scene.SCENES)):
        p = os.path.join(scene.SCENES, d, 'scene.json')
        if os.path.exists(p):
            with open(p, encoding='utf-8') as f:
                doc = json.load(f)
            editable = [c['name'] for c in doc.get('curves', []) if c.get('editable')]
            touched = sum(1 for c in doc.get('curves', []) if c.get('editable')
                         for t in c.get('touched', []) if t)
            out.append(dict(name=d, note=doc.get('note', ''),
                            editable_curves=editable, touched=touched))
    return jsonify(out)


@app.route('/api/pipeline/status/<name>')
def pipeline_status(name):
    """Для кроків 2-3 мастер-панелі: що вже є для цього варіанта на диску, а
    чого бракує - фото/камери/розмітка (вхід pipeline/generate.py) та чи вже
    порахована лінія реза (є scene.json). Нічого не рахує, тільки перевіряє
    наявність файлів."""
    name = _safe_name(name)
    from pipeline import generate as gen
    photo_dir = os.path.join(gen.ARCHIVE, name)
    photos = {v: os.path.exists(os.path.join(photo_dir, f'{v}.png'))
             for v in ('back', 'left', 'top')}
    marks = {v: os.path.exists(os.path.join(BASE, 'lines', f'{name}_{v}.json'))
            for v in ('back', 'left')}
    calculated = os.path.exists(os.path.join(scene.SCENES, name, 'scene.json'))
    return jsonify(photos=photos, marks=marks, calculated=calculated)


# ---------------------------------------------------------------- розмітка лінії згину
# Вендорено з service_3030/app.py - той самий детектор (pipeline/detect.py, копія
# без змін), той самий формат data/lines/<variant>_<view>.json, який уже читає
# pipeline/line_marks.py. Малює й керує канвою web/static/js/mark.js, окремо
# від 3D-в'ювера (виклик з кроку 3 майстер-панелі, оверлей поверх усього вікна).

_mark_img_cache = {}
MM_PER_PX = {'back': 0.09, 'left': 0.082, 'top': 0.12}


def _mark_image_path(variant, view):
    from pipeline import generate as gen
    return os.path.join(gen.ARCHIVE, variant, f'{view}.png')


def _mark_load(variant, view):
    key = (variant, view)
    if key not in _mark_img_cache:
        p = _mark_image_path(variant, view)
        if not os.path.exists(p):
            return None
        _mark_img_cache.clear()          # знімки великі, тримаємо один
        _mark_img_cache[key] = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
    return _mark_img_cache[key]


@app.route('/mark/img/<variant>/<view>.jpg')
def mark_image(variant, view):
    img = _mark_load(variant, view)
    if img is None:
        abort(404)
    ok, buf = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return send_file(io.BytesIO(buf.tobytes()), mimetype='image/jpeg')


@app.route('/api/mark/detect')
def mark_detect():
    from pipeline import detect
    variant, view = request.args.get('variant'), request.args.get('view')
    img = _mark_load(variant, view)
    if img is None:
        return jsonify(error='немає такого знімку'), 404
    kw = {}
    for k in detect.DEFAULTS:
        v = request.args.get(k)
        if v not in (None, ''):
            kw[k] = float(v) if k in ('band_lo', 'band_hi', 'edge') else int(float(v))
    res = detect.find_lines(img, **kw)
    if res is None:
        return jsonify(error='деталь на знімку не знайдена'), 400
    res['mm_per_px'] = MM_PER_PX.get(view, 0.09)
    return jsonify(res)


@app.route('/api/mark/lines/<variant>/<view>', methods=['GET', 'POST'])
def mark_lines(variant, view):
    from pipeline import line_marks
    p = os.path.join(line_marks.LINES, f'{variant}_{view}.json')
    if request.method == 'POST':
        data = request.get_json(force=True) or {}
        # totals - зсув/поворот/масштаб, яким чернетку довели до вигляду, що
        # оператор зберіг (не сама розмітка - вона в points) - записуємо
        # ОКРЕМО від points, щоб надалі пропонувати кращий СТАРТ (не з нуля),
        # див. _record_mark_totals/  /api/mark/avg_totals.
        totals = data.pop('totals', None)
        data['variant'], data['view'] = variant, view
        os.makedirs(line_marks.LINES, exist_ok=True)
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        if totals:
            _record_mark_totals(view, totals)
        return jsonify(status='saved')
    if not os.path.exists(p):
        return jsonify(points=[])
    with open(p, encoding='utf-8') as f:
        return jsonify(json.load(f))


MARK_TOTALS_PATH = os.path.join(BASE, 'data', 'mark_totals.json')


def _load_mark_totals():
    if not os.path.exists(MARK_TOTALS_PATH):
        return {}
    with open(MARK_TOTALS_PATH, encoding='utf-8') as f:
        return json.load(f)


def _record_mark_totals(view, totals):
    """Накопичує totals (зсув/поворот/масштаб чернетки) з КОЖНОЇ збереженої
    розмітки - ОКРЕМИЙ файл, не прив'язаний до чекбоксу "запам'ятати цей
    набір" (той керує списком "в процесі" на кроці 1, оператор часто його не
    ставить, а дані для усереднення потрібні незалежно від цього). Просте
    арифметичне середнє - для НЕВЕЛИКИХ поправочних кутів (реально - одиниці/
    десятки градусів, не будь-яке обертання) цього достатньо, кватерніонне
    усереднення тут зайве."""
    if view not in ('back', 'left'):
        return
    data = _load_mark_totals()
    data.setdefault(view, []).append(totals)
    data[view] = data[view][-200:]
    os.makedirs(os.path.dirname(MARK_TOTALS_PATH), exist_ok=True)
    with open(MARK_TOTALS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)


@app.route('/api/mark/avg_totals')
def mark_avg_totals():
    """Середні зсув/поворот/масштаб з попередніх розміток цього ракурсу - як
    СТАРТОВА поза для нової розмітки замість номінальних нулів (реальний
    запит: розмітка займає хвилини, а фізична установка з разу в раз схожа,
    тож хороший старт має суттєво скоротити ручне підганяння)."""
    view = request.args.get('view')
    data = _load_mark_totals().get(view, [])
    if not data:
        return jsonify(rot=[0.0, 0.0, 0.0], t=[0.0, 0.0, 0.0], scale=100.0, n=0)
    n = len(data)
    rot = [sum(d['rot'][i] for d in data) / n for i in range(3)]
    t = [sum(d['t'][i] for d in data) / n for i in range(3)]
    scale = sum(d['scale'] for d in data) / n
    return jsonify(rot=rot, t=t, scale=scale, n=n)


@app.route('/api/mark/compare')
def mark_compare():
    """Розбіжність автоматичних ліній із ручною розміткою, px і мм."""
    from pipeline import detect, line_marks
    import numpy as np
    variant, view = request.args.get('variant'), request.args.get('view')
    p = os.path.join(line_marks.LINES, f'{variant}_{view}.json')
    if not os.path.exists(p):
        return jsonify(error='еталон не розмічено')
    with open(p, encoding='utf-8') as f:
        pts = json.load(f).get('points', [])
    if len(pts) < 2:
        return jsonify(error='в еталоні менше двох точок')
    img = _mark_load(variant, view)
    kw = {}
    for k in detect.DEFAULTS:
        v = request.args.get(k)
        if v not in (None, ''):
            kw[k] = float(v) if k in ('band_lo', 'band_hi', 'edge') else int(float(v))
    res = detect.find_lines(img, **kw)
    if res is None:
        return jsonify(error='деталь на знімку не знайдена')

    pts = sorted(pts, key=lambda q: q[0])
    px = np.array([q[0] for q in pts], float)
    py = np.array([q[1] for q in pts], float)
    xs = np.array(res['x'], float)
    ok = np.array(res['ok'], bool)
    inside = (xs >= px.min()) & (xs <= px.max()) & ok
    mm = MM_PER_PX.get(view, 0.09)
    out = {}
    for name in ('upper', 'center', 'lower', 'edge_lo'):
        y = np.array(res[name], float)
        d = y[inside] - np.interp(xs[inside], px, py)
        if len(d) == 0:
            continue
        out[name] = dict(n=int(len(d)),
                         median=float(np.median(np.abs(d))),
                         p90=float(np.percentile(np.abs(d), 90)),
                         max=float(np.abs(d).max()),
                         bias=float(np.median(d)),
                         median_mm=float(np.median(np.abs(d)) * mm),
                         p90_mm=float(np.percentile(np.abs(d), 90) * mm))
    return jsonify(metrics=out, covered=int(inside.sum()),
                   total=int(ok.sum()), mm_per_px=mm)


_TEMPLATE_LINE_CACHE = {}
_MARK_CAMERAS_CACHE = None


@app.route('/api/mark/cameras')
def mark_cameras():
    """Rotation/position/фокус камер back/left - НЕ з завантаженої сцени
    основного в'ювера (scene.cameras), а напряму з калібрування рецепту.

    Панель розмітки (buildMarkPad у mark.js) використовує це, щоб малювати
    3D-піктограми повороту/зсуву незалежно від того, чи взагалі є в'ювер уже
    щось завантажений - для щойно завантаженого (ще не порахованого через
    /api/generate) набору scene.json просто не існує, а /api/scene/<name>
    (і отже scene.cameras) поверне 404. Калібрування камер - властивість
    самого стенду, однакова для всіх варіантів цього рецепту, тому її можна
    віддавати без прив'язки до конкретної сцени.
    """
    global _MARK_CAMERAS_CACHE
    if _MARK_CAMERAS_CACHE is None:
        from pipeline import generate as gen, contour_fit
        recipe = gen.load_recipe('production_2026-08-27')
        calib_dir = os.path.join(gen.CALIB, 'cameras', recipe['camera_calibration'])
        cams = contour_fit.marker_cams(calib_dir)
        _MARK_CAMERAS_CACHE = {
            v: dict(rotation=pc[:3].tolist(), position=pc[3:6].tolist(), focal_px=float(f))
            for v, (pc, f) in cams.items()
        }
    return jsonify(_MARK_CAMERAS_CACHE)


@app.route('/api/mark/template')
def mark_template():
    """Гладкий контур обода CAD-моделі (без жодної підгонки - номінальна поза
    calib/cad_placement), спроєктований у вигляд камери - шаблон для розмітки
    замість шумної піксельної трасування detect.py.

    Однаковий для БУДЬ-ЯКОГО варіанта під цим ракурсом (та сама модель, та
    сама камера, номінальна поза не залежить від фото) - тому кешується один
    раз на процес за view, не за (variant, view). Перевірено наживо
    (2026-08-29): підгонка позиції лише по силуету/контуру (без розмітки)
    часто дає ГІРШИЙ старт, ніж просто номінальна поза без будь-якої
    підгонки (на трьох реальних варіантах - гірше в 5 випадках з 6, іноді в
    рази) - тому тут навмисно НЕМАЄ least_squares, лише пряма проекція.
    """
    view = request.args.get('view')
    if view not in ('back', 'left'):
        return jsonify(error="view має бути 'back' або 'left'"), 400
    # Зсув/поворот/масштаб КОНТУРУ навколо його ж центроїда, ДО проекції в
    # камеру - той самий принцип (і та сама формула повороту Rz*Ry*Rx з
    # градусів), що й панель "лінія різу" в основному 3D-перегляді
    # (viewer.js::rotFromDeg) - навмисно не окремий, вигаданий тут набір
    # ступенів свободи. Totals (не дельти) - клієнт шле накопичену суму,
    # тому кожен запит рахується наново від номінальної пози, без стану на
    # сервері. Кешується лише "все нулі/100%" (найчастіший випадок).
    def arg(name, default=0.0):
        return float(request.args.get(name, default) or default)
    rx, ry, rz = arg('rx'), arg('ry'), arg('rz')
    dx, dy, dz = arg('dx'), arg('dy'), arg('dz')
    scale = arg('scale', 100.0)
    identity = not (rx or ry or rz or dx or dy or dz) and scale == 100.0
    if identity and view in _TEMPLATE_LINE_CACHE:
        return jsonify(_TEMPLATE_LINE_CACHE[view])
    from pipeline import generate as gen, contour_fit, mesh_rim, cad_placement, camera_model as CM
    recipe = gen.load_recipe('production_2026-08-27')
    calib_dir = os.path.join(gen.CALIB, 'cameras', recipe['camera_calibration'])
    cams = contour_fit.marker_cams(calib_dir)
    R0, t0 = cad_placement.load(recipe['cad_placement'])
    rim = mesh_rim.mesh_rim(gen.MODEL_3D)
    off = recipe['constants']['fold_radial_mm'] * contour_fit.radial(rim)
    off[:, 2] += recipe['constants']['fold_up_mm']
    fold_world = (rim + off) @ R0.T + t0
    if not identity:
        rxr, ryr, rzr = np.radians([rx, ry, rz])
        cx, sx = np.cos(rxr), np.sin(rxr)
        cy, sy = np.cos(ryr), np.sin(ryr)
        cz, sz = np.cos(rzr), np.sin(rzr)
        R = np.array([
            [cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx],
            [sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx],
            [-sy,     cy * sx,                cy * cx],
        ])
        center = fold_world.mean(0)
        fold_world = (fold_world - center) @ R.T * (scale / 100.0) + center + [dx, dy, dz]
    pc, f = cams[view]
    uv, z = CM.project(fold_world, pc[:3], pc[3:6], f)
    vis = CM.near_arc(uv, z)
    # Ті самі індекси, що обрав near_arc (сама функція повертає лише вибрані
    # uv, без індексів) - продубльовано тут (НЕ змінюючи camera_model.py),
    # щоб віддати ще й відповідні 3D-точки поточного (можливо, повернутого/
    # зсунутого) контуру: потрібні лише для тестового PnP-режиму розмітки
    # (клік по кількох точках на фото), самого near_arc не стосується.
    idx = np.asarray(_near_arc_idx(z))
    keep = _trim_kinks(vis)
    vis, idx = vis[keep], idx[keep]
    result = dict(x=vis[:, 0].tolist(), y=vis[:, 1].tolist(),
                  pts3d=fold_world[idx].tolist())
    if identity:
        _TEMPLATE_LINE_CACHE[view] = result
    return jsonify(result)


def _near_arc_idx(z):
    """Ті самі індекси, які camera_model.near_arc() обирає з z - продубльовано
    (а не змінено camera_model.py), бо near_arc там навмисно віддає лише
    вибрані точки, без індексів, а тут вони потрібні окремо для pts3d."""
    m = z < np.median(z)
    n = len(m)
    best = cur = start = bs = 0
    for i in range(2 * n):
        if m[i % n]:
            if cur == 0:
                start = i
            cur += 1
            if cur > best:
                best, bs = cur, start
        else:
            cur = 0
    return [(bs + i) % n for i in range(min(best, n))]


def _trim_kinks(P, angle_thresh=45.0, guard=30):
    """Обрізає гострі "вусики" на кінцях near_arc-вибірки - ЛИШЕ для цього
    допоміжного шаблону розмітки, camera_model.near_arc() не чіпає.

    near_arc ріже видиму дугу по МЕДІАННІЙ ГЛИБИНІ, а не за формою контуру -
    час від часу кілька точок одразу за межею справжнього видимого краю ще
    проходять поріг і дають різкий одиничний злам ("усики, що йдуть різко
    вгору" - реальний звіт користувача, ракурс back). Перевірено на
    реальних даних: медіанний кут повороту вздовж усієї 128-точкової кривої
    ~1°, а на зламі - 88-97°, ІЗОЛЬОВАНО (сусідні кути повертаються до норми
    за 1-2 точки) - фізичний згин так не заломлюється, до країв справжньої
    видимої дуги кут наростає плавно. Тому шукає перший ізольований різкий
    злам (>45°) в межах перших/останніх `guard` точок і обрізає до нього
    включно; якщо зламу нема - нічого не чіпає (більшість випадків).
    """
    n = len(P)
    if n < 2 * guard + 10:
        return np.arange(n)

    def turn_angle(i):
        a, b = P[i] - P[i - 1], P[i + 1] - P[i]
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na < 1e-9 or nb < 1e-9:
            return 0.0
        return np.degrees(np.arccos(np.clip(np.dot(a, b) / (na * nb), -1, 1)))

    start = 0
    for i in range(1, guard + 1):
        if turn_angle(i) > angle_thresh:
            start = i
    end = n - 1
    for i in range(n - 2, n - guard - 2, -1):
        if turn_angle(i) > angle_thresh:
            end = i
    return np.arange(start, end + 1)


@app.route('/api/mark/solve_pnp', methods=['POST'])
def mark_solve_pnp():
    """ТЕСТОВИЙ, додатковий спосіб позиціювати чернетку: замість ручного
    зсуву/повороту/масштабу панеллю - оператор клацає 4-6 впізнаваних точок
    на фото (їм заздалегідь відомі відповідні 3D-точки на ободі), а поза
    рахується напряму через PnP (Perspective-n-Point, класична задача:
    відомі 3D-точки об'єкта + їхні 2D-пікселі + відома камера -> поза
    об'єкта). Не чіпає існуючий шлях (/api/mark/template з totals) - геть
    окрема кнопка в mark.js, для порівняння, чи це реально швидше.

    На відміну від totals-шляху, тут НЕ обмежено рухом навколо центроїда
    номінального контуру - PnP дає повну довільну позу (rvec/tvec), тому
    список кореспонденцій має містити РІЗНОМАНІТНІ (не майже колінеарні)
    точки, інакше розв'язок буде нестійким - це відповідальність клієнта
    (обирає точки вздовж дуги, не купкою в одному місці).
    """
    d = request.get_json(force=True) or {}
    view = d.get('view')
    corr = d.get('correspondences') or []
    if view not in ('back', 'left'):
        return jsonify(error="view має бути 'back' або 'left'"), 400
    if len(corr) < 6:
        # cv2.solvePnP (DLT, дефолтний метод) сам вимагає >=6 точок для
        # непланарних об'єктних точок - перевірено емпірично (з 5-ма падає
        # з "count >= 6"), тому тут те саме число, а не "класичні" 4.
        return jsonify(error='потрібно мінімум 6 точок'), 400
    obj = np.array([c['obj'] for c in corr], dtype=float)
    img = np.array([c['img'] for c in corr], dtype=float)
    from pipeline import generate as gen, contour_fit, mesh_rim, cad_placement, camera_model as CM, geometry
    recipe = gen.load_recipe('production_2026-08-27')
    calib_dir = os.path.join(gen.CALIB, 'cameras', recipe['camera_calibration'])
    cams = contour_fit.marker_cams(calib_dir)
    pc, f = cams[view]
    K = np.array([[f, 0.0, CM.IMG_W / 2], [0.0, f, CM.IMG_H / 2], [0.0, 0.0, 1.0]])
    # Початкове наближення - НОМІНАЛЬНА поза камери (rvec/tvec, за яких obj-точки
    # й так лежать там, де їх намальовано у шаблоні), а не "з нуля" (за
    # замовчуванням solvePnP рахує лінійним DLT без жодного зв'язку з тим, де
    # ми ЗНАЄМО, що деталь приблизно є - звідси і скарга "вилітає по масштабу/
    # нахилу/зсуву": DLT на шумних ручних кліках може знайти математично
    # коректний, але фізично абсурдний розв'язок). useExtrinsicGuess вмикає
    # ітеративне уточнення (Левенберг-Марквардт) ВІД цього старту, а не пошук
    # заново - тому результат лишається в розумних межах від номіналу.
    # np.array(...), НЕ np.asarray(...) - cv2.solvePnP з useExtrinsicGuess=True
    # пише уточнений результат НАЗАД у передані rvec0/tvec0 (перевірено
    # емпірично); np.asarray на вже-ndarray не копіює, тож rvec0 був би
    # ТИМ САМИМ шматком пам'яті, що й pc (зріз cams[view]) - виклик solvePnP
    # тихо псував би калібрування камери для решти цього запиту (саме це й
    # спричиняло "рахує якось дивно, вилітає": Rc нижче використовувала вже
    # зіпсовані дані). np.array() завжди копіює.
    rvec0 = np.array(pc[:3], dtype=float).reshape(3, 1)
    Rc0 = cv2.Rodrigues(rvec0)[0]
    tvec0 = (-Rc0 @ np.array(pc[3:6], dtype=float)).reshape(3, 1)
    ok, rvec, tvec = cv2.solvePnP(obj, img, K, None, rvec0, tvec0,
                                  useExtrinsicGuess=True, flags=cv2.SOLVEPNP_ITERATIVE)
    if not ok:
        return jsonify(error="не вдалося розв'язати позу за цими точками"), 400
    rim = mesh_rim.mesh_rim(gen.MODEL_3D)
    R0, t0 = cad_placement.load(recipe['cad_placement'])
    off = recipe['constants']['fold_radial_mm'] * contour_fit.radial(rim)
    off[:, 2] += recipe['constants']['fold_up_mm']
    fold_world = (rim + off) @ R0.T + t0
    Rm = cv2.Rodrigues(rvec)[0]
    tv = tvec.reshape(3)
    Xc = fold_world @ Rm.T + tv
    z = np.maximum(Xc[:, 2], 1e-6)
    uv = np.c_[f * Xc[:, 0] / z + CM.IMG_W / 2, f * Xc[:, 1] / z + CM.IMG_H / 2]
    vis = CM.near_arc(uv, Xc[:, 2])
    # Той самий розв'язок, але переведений у зсув/поворот/масштаб НАВКОЛО
    # ЦЕНТРОЇДА fold_world - той самий формат, що приймає /api/mark/template
    # (totals) - щоб панель зсуву/повороту/масштабу могла продовжити рух
    # ЗВІДСИ, а не почати знову з нуля (інакше перший же клік по панелі тягнув
    # totals=0 і чернетка "стрибала" назад до нуля - реальний звіт користувача).
    # R_total - те саме обертання, але БЕЗ camera-екстринсиків (Rc, C):
    # Rc @ R_total = Rm  =>  R_total = Rc^-1 @ Rm = Rc.T @ Rm (Rc - ортогональна).
    center = fold_world.mean(0)
    Rc = cv2.Rodrigues(np.asarray(pc[:3], dtype=float))[0]
    C = np.asarray(pc[3:6], dtype=float)
    R_total = Rc.T @ Rm
    yaw, pitch, roll = geometry.ypr_from_rot(R_total)
    shift = Rc.T @ (Rm @ center + tv - Rc @ center + Rc @ C)
    totals = dict(rot=[roll, pitch, yaw], t=shift.tolist(), scale=100.0)
    return jsonify(x=vis[:, 0].tolist(), y=vis[:, 1].tolist(), totals=totals)


@app.route('/api/scene/<name>/curve/<int:cidx>/auto_pose', methods=['POST'])
def auto_pose(name, cidx):
    """ЕКСПЕРИМЕНТАЛЬНО (варіант 3 з обговорення 2026-09-07, "авто-доведення"),
    ПЕРЕРОБЛЕНО 2026-09-07 за реальним зауваженням користувача - раніше клік
    означав "оця КОНКРЕТНА (наперед обрана за індексом) точка насправді тут",
    а оператору важко точно знати, яка саме з ~90 майже однакових точок
    мається на увазі ("точно узнать где должна стоять именно эта точка,
    сложно"). Тепер клік означає простіше - "лінія повинна проходити ТУТ",
    без прив'язки до конкретного індексу: та сама ідея, що вже добре працює
    в /fit_marks (відстань до НАЙБЛИЖЧОЇ точки лінії, не до заданої), лише
    джерело - кілька кліків оператора замість уже намальованої розмітки.

    Одна жорстка поза (поворот+зсув+масштаб), що мінімізує сумарну відстань
    від кожного кліку до найближчої (near_arc-видимої) точки лінії з ТОГО Ж
    ракурсу - scipy.least_squares, той самий принцип, що contour_fit.resid_of
    і /fit_marks, тільки в один бік (клік->лінія, не навпаки): кліків мало
    (не суцільна розмітка), тому карати лінію за те, що вона десь ДАЛЕКО від
    жодного кліку, немає сенсу - кліки відзначають лише окремі місця, не
    вимагають покриття всієї дуги.

    Навмисно ІЗОЛЬОВАНО від pipeline/contour_fit.py: не змінює оптимізатор
    підгонки, не викликається з generate(), нічого не пише на диск сама.
    Повертає totals (rot/t/scale) у ТОМУ САМОМУ форматі, що й /fit_marks -
    клієнт застосовує їх тим самим поворотом/зсувом навколо центроїда, що й
    ручні кнопки групової панелі, тому "Скасувати"/"Зберегти" продовжують
    працювати без жодних змін.
    """
    d = request.get_json(force=True) or {}
    corr = d.get('corr') or []
    by_view = {'back': [], 'left': []}
    for item in corr:
        if item.get('view') not in ('back', 'left'):
            return jsonify(error='некоректні дані кліку'), 400
        by_view[item['view']].append(item['img'])
    # Як і /fit_marks - розмітка/кліки лише З ОДНОГО ракурсу не визначають
    # позу однозначно (один 2D-контур - недостатньо обмежень).
    if len(by_view['back']) < 2 or len(by_view['left']) < 2:
        return jsonify(error='потрібно мінімум 2 кліки на КОЖНОМУ ракурсі (back і left)'), 400

    p = os.path.join(scene.SCENES, name, 'scene.json')
    if not os.path.exists(p):
        abort(404)
    with open(p, encoding='utf-8') as f:
        doc = json.load(f)
    if not (0 <= cidx < len(doc['curves'])):
        abort(404)
    c = doc['curves'][cidx]
    P0 = np.array(c['points'], dtype=float)

    from scipy.optimize import least_squares
    from pipeline import generate as gen, contour_fit, camera_model as CM, geometry
    recipe = gen.load_recipe('production_2026-08-27')
    calib_dir = os.path.join(gen.CALIB, 'cameras', recipe['camera_calibration'])
    cams = contour_fit.marker_cams(calib_dir)
    center = P0.mean(0)
    clicks = {w: np.array(by_view[w], dtype=float) for w in ('back', 'left')}

    def click_dist_mm(P):
        out = []
        for w in ('back', 'left'):
            pc, f = cams[w]
            uv, z = CM.project(P, pc[:3], pc[3:6], f)
            vis = CM.near_arc(uv, z)
            d = np.abs(CM.dist_to_polyline(clicks[w], vis))
            out.append(d * float(np.median(z)) / f)
        return np.concatenate(out)

    def resid(p7):
        R = cv2.Rodrigues(p7[:3])[0]
        s = np.exp(p7[6])
        P = (P0 - center) @ R.T * s + center + p7[3:6]
        return click_dist_mm(P)

    before_mm = float(click_dist_mm(P0).mean())
    # Ті самі межі, що й /fit_marks - проти виродженого розв'язку (лінія, що
    # "схлопнулась" у точку десь біля кліків, теж тривіально мінімізує цю
    # відстань, як і симетричну в /fit_marks - перевірено на реальних даних).
    bounds = (np.r_[[-0.6]*3, [-100.0]*3, -0.3], np.r_[[0.6]*3, [100.0]*3, 0.3])
    r = least_squares(resid, np.r_[np.zeros(6), 0.0], method='trf', bounds=bounds, max_nfev=800)
    R = cv2.Rodrigues(r.x[:3])[0]
    s = float(np.exp(r.x[6]))
    P1 = (P0 - center) @ R.T * s + center + r.x[3:6]
    after_mm = float(click_dist_mm(P1).mean())

    yaw, pitch, roll = geometry.ypr_from_rot(R)
    totals = dict(rot=[roll, pitch, yaw], t=r.x[3:6].tolist(), scale=s * 100.0)
    return jsonify(totals=totals, before_mm=before_mm, after_mm=after_mm, n=len(corr))


@app.route('/api/scene/<name>/curve/<int:cidx>/fit_marks', methods=['POST'])
def fit_marks(name, cidx):
    """ОДНА кнопка, БЕЗ кліків (обговорено 2026-09-07) - підганяє ПОТОЧНУ лінію
    (з ручними правками, вже застосованим auto_pose - байдуже) під уже
    збережену ручну розмітку лінії згину (крок 2/3), схожим членом невязки,
    що й у generate() (contour_fit.resid_of, mark-term - E.dist_to_polyline
    проти near_arc-видимих точок), лише тут - на живих точках сцени, а не на
    CAD-ободі, і без решти членів (силует/контур top).

    ВІДМІННІСТЬ від resid_of: там відстань лише В ОДИН бік (розмітка->лінія) -
    карає, якщо лінія НЕ ДОХОДИТЬ до розмітки, але не бачить, якщо лінія
    ВИЛІЗЛА за розмітку (тим точкам розмітки й так є до чого прилипнути
    ближче до середини). Тут - СИМЕТРИЧНО в обидва боки (див. mark_dist_mm),
    саме тому, що масштаб/краї - єдине, що тут підганяється (без силуету/
    контуру top, які в generate() частково компенсують цю асиметрію) -
    реальний звіт: "масштаб трохи не витримується", саме на краях
    (лоб/потилиця/вуха).

    Незалежно від /auto_pose (окрема кнопка, окрема функція застосування на
    клієнті) - навмисно, щоб ідеї можна було прибирати чи лишати кожну
    окремо, як і просив користувач. Так само не чіпає pipeline/contour_fit.py
    і generate(), нічого не пише на диск сама.
    """
    p = os.path.join(scene.SCENES, name, 'scene.json')
    if not os.path.exists(p):
        abort(404)
    with open(p, encoding='utf-8') as f:
        doc = json.load(f)
    if not (0 <= cidx < len(doc['curves'])):
        abort(404)
    c = doc['curves'][cidx]
    P0 = np.array(c['points'], dtype=float)

    from scipy.optimize import least_squares
    from pipeline import generate as gen, contour_fit, camera_model as CM, geometry, line_marks
    var_marks = line_marks.load_marks().get(name, {})
    used = [w for w in ('back', 'left') if w in var_marks]
    # Розмітка лише З ОДНОГО боку не визначає 7-параметричну позу однозначно
    # (один 2D-контур відповідає багатьом 3D позам) - без другого виду
    # оптимізатор просто тікає кудись у межі обмежень (перевірено на
    # реальних даних: back-only дав поворот -57°, зсув до упору в 100мм,
    # "покращення" суто числове, без фізичного сенсу). Тому - обидва або
    # відмова, а не спроба на одному.
    if len(used) < 2:
        return jsonify(error='потрібна розмітка з ОБОХ ракурсів (back і left) - '
                              'з одного 2D-контур не визначає позу однозначно'), 400

    recipe = gen.load_recipe('production_2026-08-27')
    calib_dir = os.path.join(gen.CALIB, 'cameras', recipe['camera_calibration'])
    cams = contour_fit.marker_cams(calib_dir)
    center = P0.mean(0)

    def mark_dist_mm(P):
        # Симетрично в ОБИДВА боки (розмітка->лінія і лінія->розмітка), не лише
        # в один, як contour_fit.resid_of. Один напрямок карає НЕДОхід лінії до
        # кінця розмітки (там розмітці нема до чого прилипнути), але зовсім не
        # бачить, якщо лінія навпаки ВИЛІЗЛА за розмітку (розмітці й так є до
        # чого прилипнути ближче до середини) - реальний звіт користувача:
        # масштаб "трохи не витримується", саме на краях (лоб/потилиця/вуха).
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
        P = (P0 - center) @ R.T * s + center + p7[3:6]
        return mark_dist_mm(P)

    before_mm = float(mark_dist_mm(P0).mean())
    # Межі (метод 'trf', не 'lm' - 'lm' bounds не підтримує) - без них
    # симетрична (в обидва боки) відстань вище має вироджений розв'язок:
    # СХЛОПНУТИ лінію майже в точку десь на розмітці робить обидва напрямки
    # відстані малими одночасно (перевірено на реальних даних - виходило
    # scale=0.08%, зсув 2650мм - лінія фізично зникала). ±35° / ±100мм /
    # 74-135% з запасом покривають будь-яку реальну "доводочну" правку,
    # не залишаючи вироджений розв'язок математично доступним.
    bounds = (np.r_[[-0.6]*3, [-100.0]*3, -0.3], np.r_[[0.6]*3, [100.0]*3, 0.3])
    r = least_squares(resid, np.r_[np.zeros(6), 0.0], method='trf', bounds=bounds, max_nfev=800)
    R = cv2.Rodrigues(r.x[:3])[0]
    s = float(np.exp(r.x[6]))
    P1 = (P0 - center) @ R.T * s + center + r.x[3:6]
    after_mm = float(mark_dist_mm(P1).mean())

    yaw, pitch, roll = geometry.ypr_from_rot(R)
    totals = dict(rot=[roll, pitch, yaw], t=r.x[3:6].tolist(), scale=s * 100.0)
    return jsonify(totals=totals, before_mm=before_mm, after_mm=after_mm, used=used)


_TEMPLATE_LINE_3D_CACHE = {}


@app.route('/api/mark/template3d')
def mark_template_3d():
    """Той самий контур лінії згину (rim + fold_radial/fold_up, номінальна поза),
    але ПОВНИЙ ЗАМКНЕНИЙ і в світових координатах верстата - без проекції в
    конкретну камеру і без near_arc-відсікання видимої дуги. Аналог "лінії
    різу" для головного 3D-перегляду (viewer.js): один спільний контур, який
    можна посунути/повернути ОДИН РАЗ і бачити однаково під будь-яким ракурсом
    і у вільному огляді - на відміну від /api/mark/template, прив'язаного до
    пікселів одного конкретного фото.
    """
    if 'points' in _TEMPLATE_LINE_3D_CACHE:
        return jsonify(_TEMPLATE_LINE_3D_CACHE['points'])
    from pipeline import generate as gen, contour_fit, mesh_rim, cad_placement
    recipe = gen.load_recipe('production_2026-08-27')
    R0, t0 = cad_placement.load(recipe['cad_placement'])
    rim = mesh_rim.mesh_rim(gen.MODEL_3D)
    off = recipe['constants']['fold_radial_mm'] * contour_fit.radial(rim)
    off[:, 2] += recipe['constants']['fold_up_mm']
    fold_world = (rim + off) @ R0.T + t0
    result = dict(points=fold_world.tolist())
    _TEMPLATE_LINE_3D_CACHE['points'] = result
    return jsonify(result)


@app.route('/api/scene/<name>')
def one(name):
    p = os.path.join(scene.SCENES, name, 'scene.json')
    if not os.path.exists(p):
        abort(404)
    with open(p, encoding='utf-8') as f:
        return jsonify(json.load(f))


@app.route('/api/scene/<name>/mesh/<int:idx>/placement', methods=['POST'])
def set_placement(name, idx):
    """Как в 2020 - положение модели, если она есть в сцене, для ориентира."""
    p = os.path.join(scene.SCENES, name, 'scene.json')
    if not os.path.exists(p):
        abort(404)
    with open(p, encoding='utf-8') as f:
        doc = json.load(f)
    if idx >= len(doc.get('meshes', [])):
        abort(404)
    d = request.get_json(force=True) or {}
    place = dict(rot_deg=[float(x) for x in d.get('rot_deg', [0, 0, 0])],
                 translate=[float(x) for x in d.get('translate', [0, 0, 0])],
                 scale=float(d.get('scale', 1.0)))
    doc['meshes'][idx]['placement'] = place
    doc['meshes'][idx]['transform'] = scene.placement_matrix(**place)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False)
    return jsonify(status='saved', placement=place)


@app.route('/api/scene/<name>/curve/<int:cidx>/point/<int:pidx>', methods=['POST'])
def set_point(name, cidx, pidx):
    """Поправить одну точку редактируемой кривой. Помечает её тронутой."""
    p = os.path.join(scene.SCENES, name, 'scene.json')
    if not os.path.exists(p):
        abort(404)
    with open(p, encoding='utf-8') as f:
        doc = json.load(f)
    curves = doc.get('curves', [])
    if cidx >= len(curves) or not curves[cidx].get('editable'):
        abort(404)
    c = curves[cidx]
    if pidx >= len(c['points']):
        abort(404)
    d = request.get_json(force=True) or {}
    xyz = [float(x) for x in d.get('xyz', c['points'][pidx])]
    c['points'][pidx] = xyz
    c.setdefault('touched', [False] * len(c['points']))
    c['touched'][pidx] = True
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False)
    return jsonify(status='saved', point=xyz)


@app.route('/api/scene/<name>/curve/<int:cidx>/points', methods=['POST'])
def set_points_bulk(name, cidx):
    """Сдвинуть НЕСКОЛЬКО точек разом - групповой сдвиг, не по одной.

    body: {"points": [{"pidx": int, "xyz": [x,y,z]}, ...]}
    Каждая перечисленная точка помечается тронутой, остальные не трогаются.
    """
    p = os.path.join(scene.SCENES, name, 'scene.json')
    if not os.path.exists(p):
        abort(404)
    with open(p, encoding='utf-8') as f:
        doc = json.load(f)
    curves = doc.get('curves', [])
    if cidx >= len(curves) or not curves[cidx].get('editable'):
        abort(404)
    c = curves[cidx]
    c.setdefault('touched', [False] * len(c['points']))
    d = request.get_json(force=True) or {}
    saved = []
    for item in d.get('points', []):
        pidx = int(item['pidx'])
        if pidx >= len(c['points']):
            continue
        xyz = [float(x) for x in item['xyz']]
        c['points'][pidx] = xyz
        c['touched'][pidx] = True
        saved.append(pidx)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False)
    return jsonify(status='saved', count=len(saved))


@app.route('/api/scene/<name>/curve/<int:cidx>/point/<int:pidx>/reset', methods=['POST'])
def reset_point(name, cidx, pidx):
    """Вернуть точку к расчётному значению, снять пометку "тронута"."""
    p = os.path.join(scene.SCENES, name, 'scene.json')
    if not os.path.exists(p):
        abort(404)
    with open(p, encoding='utf-8') as f:
        doc = json.load(f)
    c = doc['curves'][cidx]
    orig = c['points_original'][pidx]
    c['points'][pidx] = orig
    c['touched'][pidx] = False
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False)
    return jsonify(status='reset', point=orig)


@app.route('/api/scene/<name>/export', methods=['POST'])
def export_ls(name):
    """Собрать финальный .LS из текущих точек и отдать путь + сколько тронуто."""
    try:
        out_path, n_total, n_touched = export_final.export(name)
    except SystemExit as e:
        return jsonify(error=str(e)), 400
    return jsonify(status='ok', file=os.path.basename(out_path),
                   total=n_total, touched=n_touched)


# ------------------------------------------------------------ методи розрахунку
# Модульність (обговорено 2026-09-07): кожен метод - ОКРЕМИЙ ПРОЦЕС з однаковим
# контрактом (python <entry> --variant <ім'я> --in <archive/<ім'я>> --out <.LS>),
# щоб зовнішні методи (від інших розробників) підключались без жодних змін тут
# - і щоб наш власний ("виробничий") метод працював ТАК САМО, а не як виняток
# (реальна вимога користувача). pipeline/generate.py сам НЕ змінювався - лише
# обгорнутий у methods/production/run.py.
METHODS_PATH = os.path.join(BASE, 'calib', 'methods.json')
LAST_METHOD_PATH = os.path.join(BASE, 'data', 'last_method.json')


def _load_methods():
    with open(METHODS_PATH, encoding='utf-8') as f:
        return json.load(f)['methods']


def _default_method_id():
    methods = _load_methods()
    if not methods:
        return None
    if os.path.exists(LAST_METHOD_PATH):
        with open(LAST_METHOD_PATH, encoding='utf-8') as f:
            last = json.load(f).get('id')
        if any(m['id'] == last for m in methods):
            return last
    return methods[0]['id']


def _save_last_method(method_id):
    os.makedirs(os.path.dirname(LAST_METHOD_PATH), exist_ok=True)
    with open(LAST_METHOD_PATH, 'w', encoding='utf-8') as f:
        json.dump({'id': method_id}, f)


@app.route('/api/methods')
def list_methods():
    """Для випадаючого списку методу на кроці 3 - перелік + який обрати за
    замовчуванням (останній використаний, а не завжди перший - реальна
    вимога користувача)."""
    return jsonify(methods=_load_methods(), default=_default_method_id())


def _stage_method_input(variant):
    """Збирає для методу ОДНУ папку з усім, що йому може знадобитись - фото +
    калібрування камер + розмітка (якщо є) - тим самим іменуванням, що вже
    використовує incoming/<name>/ (discover.py), щоб зовнішній розробник міг
    зібрати таку саму папку руками для локального тесту, без нашого сервера.
    Раніше сюди йшов просто archive/<variant>/ - там БУЛИ фото, але НЕ було
    калібрування камер (воно лежить окремо, в calib/cameras/) - зовнішній
    метод не зміг би порахувати позу камери взагалі. Виправлено.
    """
    import tempfile
    from pipeline import generate as gen
    recipe = gen.load_recipe('production_2026-08-27')
    calib_dir = os.path.join(gen.CALIB, 'cameras', recipe['camera_calibration'])
    photo_dir = os.path.join(gen.ARCHIVE, variant)

    d = tempfile.mkdtemp(prefix=f'method_in_{variant}_')
    for v in ('back', 'left', 'top'):
        src_photo = os.path.join(photo_dir, f'{v}.png')
        if os.path.exists(src_photo):
            shutil.copyfile(src_photo, os.path.join(d, f'{v}.png'))
        src_cam = os.path.join(calib_dir, f'cam_{v}.npy')
        if os.path.exists(src_cam):
            shutil.copyfile(src_cam, os.path.join(d, f'cam_{v}.npy'))
    for v in ('back', 'left'):
        src_mark = os.path.join(BASE, 'lines', f'{variant}_{v}.json')
        if os.path.exists(src_mark):
            shutil.copyfile(src_mark, os.path.join(d, f'marks_{v}.json'))
    return d


def _run_method(method_id, variant, out_path, params=None):
    """params - додаткові, СВОЇ для конкретного методу аргументи (напр.
    Метод 2 потребує обрану форму заготовки - схема оголошена в
    calib/methods.json під "params", тут лише передається далі в CLI як
    --<name> <значення>, без жодного знання про конкретні методи."""
    methods = {m['id']: m for m in _load_methods()}
    m = methods.get(method_id)
    if not m:
        raise ValueError(f'невідомий метод: {method_id}')
    entry = os.path.join(BASE, m['entry'])
    in_dir = _stage_method_input(variant)
    try:
        cmd = [sys.executable, entry, '--variant', variant, '--in', in_dir, '--out', out_path]
        for spec in m.get('params', []):
            val = (params or {}).get(spec['name'])
            if val is None or val == '':
                raise ValueError(f'{m["name"]}: не вказано параметр "{spec.get("label", spec["name"])}"')
            cmd += [f'--{spec["name"]}', str(val)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if r.returncode != 0 or not os.path.exists(out_path):
            raise RuntimeError(f'{m["name"]} впав: {(r.stderr or r.stdout)[-2000:]}')
        return out_path
    finally:
        shutil.rmtree(in_dir, ignore_errors=True)


@app.route('/api/generate/<name>', methods=['POST'])
def generate_ls(name):
    """Порахувати лінію реза з нуля обраним методом (окремий процес - див.
    _run_method) і (пере)зібрати сцену з результату - як build_scene.py,
    повністю переписує scene.json. Використовувати лише для варіанта без
    збережених правок (або коли затирання правок - усвідомлене рішення)."""
    name = _safe_name(name)
    d = request.get_json(silent=True) or {}
    method_id = d.get('method') or _default_method_id()
    if not method_id:
        return jsonify(error='немає жодного зареєстрованого методу розрахунку'), 400

    from pipeline import generate as gen
    out_path = os.path.join(BASE, 'data', 'generated', f'{name}_{method_id}.LS')
    try:
        ls_path = _run_method(method_id, name, out_path, params=d.get('params'))
    except Exception as e:
        return jsonify(error=str(e)), 400
    _save_last_method(method_id)

    # Камери для build_scene - завжди та сама фізична калібровка, незалежно
    # від того, яким методом порахована лінія (метод не міняє, де стоять
    # камери реально).
    recipe = gen.load_recipe('production_2026-08-27')
    calib_dir = os.path.join(gen.CALIB, 'cameras', recipe['camera_calibration'])
    cams = {v: os.path.join(calib_dir, f'cam_{v}.npy') for v in ('back', 'left', 'top')}
    photo_dir = os.path.join(gen.ARCHIVE, name)
    photos = {v: os.path.join(photo_dir, f'{v}.png') for v in ('back', 'left', 'top')}
    # Якщо оператор при додаванні набору завантажив еталонний .LS
    # (archive/<name>/ground_truth.ls, kind=reference) - показати його в
    # Об'єктах поруч із розрахунком (build_scene.build уже вміє це, просто
    # тут раніше не передавали шлях).
    reference_path = os.path.join(photo_dir, 'ground_truth.ls')
    if not os.path.exists(reference_path):
        reference_path = None
    build_scene.build(name, ls_path, cams, photos, reference_path=reference_path)

    # Запам'ятати, яким методом порахований САМЕ ЦЕЙ набір - у scene.json,
    # окремо від "останній обраний глобально" (last_method.json вище).
    scene_path = os.path.join(scene.SCENES, name, 'scene.json')
    with open(scene_path, encoding='utf-8') as f:
        doc = json.load(f)
    doc['method'] = method_id
    with open(scene_path, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False)

    return jsonify(status='ok', file=os.path.basename(ls_path), method=method_id)


_NAME_RE = re.compile(r'^[A-Za-z0-9_.-]{1,64}$')


def _safe_name(name):
    """Ім'я набору йде прямо у шлях файлу (archive/<name>/...) - без цієї
    перевірки завантаження з довільним ім'ям було б обходом каталогу."""
    if not _NAME_RE.match(name or ''):
        abort(400, description="некоректне ім'я набору")
    return name


def _name_status(name):
    """Що вже існує під цим ім'ям - для модалки "Новий набір": відрізняємо
    "вже ПОРАХОВАНО" (calculated=True - реальний ризик тихо влізти у чиюсь
    готову роботу, як з archive/v21/back.png; це підстава ЗАБОРОНИТИ) від
    "вже є якісь файли, але ще не порахований" (has_data=True без calculated
    - це нормальний випадок повернутися й дозавантажити свій же учорашній
    набір; тут тільки попереджаємо, не блокуємо)."""
    from pipeline import generate as gen, line_marks
    has_photos = os.path.isdir(os.path.join(gen.ARCHIVE, name)) and bool(os.listdir(os.path.join(gen.ARCHIVE, name)))
    has_marks = any(os.path.exists(os.path.join(line_marks.LINES, f'{name}_{v}.json')) for v in ('back', 'left'))
    calculated = os.path.exists(os.path.join(scene.SCENES, name, 'scene.json'))
    return dict(has_data=has_photos or has_marks, calculated=calculated)


@app.route('/api/name_taken/<name>')
def name_taken(name):
    name = _safe_name(name)
    return jsonify(**_name_status(name))


@app.route('/api/suggest_name')
def suggest_name():
    """nabir-MMDD-NNN - наступний вільний номер за сьогодні. Рахує від уже
    зайнятих імен (archive/), а не від лічильника в файлі - не залежить від
    того, чи хтось видалив/перейменував щось руками."""
    from pipeline import generate as gen
    mmdd = datetime.date.today().strftime('%m%d')
    prefix = f'nabir-{mmdd}-'
    used = set()
    if os.path.isdir(gen.ARCHIVE):
        for d in os.listdir(gen.ARCHIVE):
            if d.startswith(prefix) and d[len(prefix):].isdigit():
                used.add(int(d[len(prefix):]))
    n = 1
    while n in used:
        n += 1
    return jsonify(name=f'{prefix}{n:03d}')


_RAW_RE = re.compile(r'_w(\d+)_h(\d+)_p(\w+)', re.IGNORECASE)


def _decode_upload_image(filename, data):
    """.raw (8-біт mono, без заголовка, wNNNN_hNNNN_pMono8 у імені) або
    звичайний jpg/png/... - в обох випадках повертає масив OpenCV (H,W)."""
    if filename.lower().endswith('.raw'):
        m = _RAW_RE.search(filename)
        w, h = (int(m.group(1)), int(m.group(2))) if m else (4096, 3000)
        arr = np.frombuffer(data, dtype=np.uint8)
        if arr.size != w * h:
            raise ValueError(f'.raw {filename}: очікував {w}x{h}={w*h} байт, отримав {arr.size}')
        return arr.reshape(h, w)
    arr = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    if arr is None:
        raise ValueError(f'не вдалося розпізнати зображення: {filename}')
    return arr


@app.route('/api/upload/<name>/<kind>', methods=['POST'])
def upload(name, kind):
    """Покласти одне фото (back/left/top, .raw або звичайне) чи еталонний
    .LS (kind=reference) у archive/<name>/ - той самий каталог, який читає
    pipeline/generate.py. Ім'я вихідного файлу завжди фіксоване
    (back.png/left.png/top.png/ground_truth.ls) - оригінальна назва файлу,
    яку прислали, для пайплайна не важлива і ніде не зберігається."""
    name = _safe_name(name)
    if kind not in ('back', 'left', 'top', 'reference'):
        abort(400, description='kind має бути back/left/top/reference')
    if _name_status(name)['calculated']:
        # Реальний захист, не тільки підказка в UI - вже траплялося, що
        # завантаження тихо переписувало archive/v21/back.png поверх уже
        # порахованого набору. Дозавантажувати СВІЙ незавершений набір
        # (фото є, розрахунку ще нема) можна й далі - блокуємо лише те, що
        # вже має готову сцену.
        return jsonify(error=f"«{name}» вже порахований - завантаження сюди "
                             f"заборонено, щоб не переписати готову роботу"), 409
    f = request.files.get('file')
    if f is None or not f.filename:
        return jsonify(error='файл не передано'), 400

    from pipeline import generate as gen
    dst_dir = os.path.join(gen.ARCHIVE, name)
    os.makedirs(dst_dir, exist_ok=True)
    data = f.read()

    if kind == 'reference':
        with open(os.path.join(dst_dir, 'ground_truth.ls'), 'wb') as out:
            out.write(data)
        return jsonify(status='ok', saved='ground_truth.ls')

    try:
        img = _decode_upload_image(f.filename, data)
    except ValueError as e:
        return jsonify(error=str(e)), 400
    cv2.imwrite(os.path.join(dst_dir, f'{kind}.png'), img)
    return jsonify(status='ok', saved=f'{kind}.png', shape=list(img.shape))


CAMERA_SERIALS_PATH = os.path.join(BASE, 'calib', 'camera_serials.json')


@app.route('/api/capture/<name>', methods=['POST'])
def capture(name):
    """"Зробити фото автоматично" (обговорено 2026-09-07) - запускає
    capture/run.py (ДООПРАЦЬОВАНА КОПІЯ кореневого capture.py, сам він не
    чіпається) окремим процесом, забирає готові кадри й розкладає по
    archive/<name>/back.png тощо - за тим самим правилом, що й ручне
    завантаження (upload() вище), просто без ручного вибору файлу.

    Camera -> ракурс береться з calib/camera_serials.json (заповнюється
    один раз фізичною перевіркою на машині оператора - серійники поки
    невідомі, тому цей маршрут працює й БЕЗ них: знімає, показує, що знайшов,
    але не може розкласти по back/left/top, поки мапу не заповнено).

    НІКОЛИ не валить сервер - будь-яка проблема (SDK відсутній, камер
    менше, ніж треба, помилка окремої камери) повертається текстом
    оператору, а не винятком.
    """
    name = _safe_name(name)
    if _name_status(name)['calculated']:
        return jsonify(error=f"«{name}» вже порахований - зйомка сюди "
                             f"заборонена, щоб не переписати готову роботу"), 409

    import tempfile
    out_dir = tempfile.mkdtemp(prefix=f'capture_{name}_')
    result_path = os.path.join(out_dir, 'result.json')
    entry = os.path.join(BASE, 'capture', 'run.py')
    try:
        r = subprocess.run([sys.executable, entry, '--out', out_dir, '--result', result_path],
                            capture_output=True, text=True, timeout=60)
        if not os.path.exists(result_path):
            return jsonify(error='Скрипт зйомки не відповів коректно: '
                                 + (r.stderr or r.stdout or 'немає виводу')[-1500:]), 500
        with open(result_path, encoding='utf-8') as f:
            result = json.load(f)
        if result.get('error'):
            return jsonify(error=result['error']), 500

        with open(CAMERA_SERIALS_PATH, encoding='utf-8') as f:
            serial_map = json.load(f)
        serial_to_view = {v: k for k, v in serial_map.items() if k != '_comment' and v}

        found = {}         # ракурс -> шлях до тимчасового файлу
        unmapped = []       # знято, але серійник не в мапі (чи мапа порожня)
        for cam in result['cameras']:
            if not cam.get('ok'):
                continue
            view = serial_to_view.get(cam['serial'])
            if view:
                found[view] = os.path.join(out_dir, cam['file'])
            else:
                unmapped.append(cam['serial'])

        missing = [v for v in ('back', 'left', 'top') if v not in found]
        if missing:
            if not serial_to_view:
                msg = (f"Знято камер: {len(result['cameras'])}, але зіставлення camera -> "
                       f"ракурс ще не налаштоване (calib/camera_serials.json) - розкласти "
                       f"по back/left/top автоматично не можу. Серійники знятих камер: "
                       + ', '.join(c['serial'] for c in result['cameras'] if c.get('ok')))
            else:
                msg = f"Не знайдено камеру для ракурсу: {', '.join(missing)}. Перевірте з'єднання."
                if unmapped:
                    msg += f" (знято, але не впізнано серійники: {', '.join(unmapped)})"
            return jsonify(error=msg), 409

        from pipeline import generate as gen
        dst_dir = os.path.join(gen.ARCHIVE, name)
        os.makedirs(dst_dir, exist_ok=True)
        for view, src in found.items():
            shutil.copyfile(src, os.path.join(dst_dir, f'{view}.png'))
        return jsonify(status='ok', saved=list(found.keys()))
    except subprocess.TimeoutExpired:
        return jsonify(error='Зйомка не відповіла за 60с - перевірте з\'єднання з камерами'), 504
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)


PENDING_PATH = os.path.join(BASE, 'data', 'pending.json')


def _load_pending():
    if not os.path.exists(PENDING_PATH):
        return []
    with open(PENDING_PATH, encoding='utf-8') as f:
        return json.load(f)


@app.route('/api/pending', methods=['GET'])
def pending_list():
    """Набори, які користувач попросив 'запам'ятати' під час завантаження,
    але які ще НЕ порахували (є scene.json - значить вже в основному списку,
    прибираємо зі списку 'в процесі' самі, вручну чистити не треба)."""
    names = [n for n in _load_pending()
            if not os.path.exists(os.path.join(scene.SCENES, n, 'scene.json'))]
    if names != _load_pending():
        with open(PENDING_PATH, 'w', encoding='utf-8') as f:
            json.dump(names, f, ensure_ascii=False)
    return jsonify(names)


@app.route('/api/pending/<name>', methods=['POST'])
def pending_add(name):
    name = _safe_name(name)
    names = _load_pending()
    if name not in names:
        names.append(name)
        os.makedirs(os.path.dirname(PENDING_PATH), exist_ok=True)
        with open(PENDING_PATH, 'w', encoding='utf-8') as f:
            json.dump(names, f, ensure_ascii=False)
    return jsonify(status='ok')


@app.route('/download/<name>/<path:filename>')
def download(name, filename):
    d = os.path.join(scene.SCENES, name)
    if not os.path.isdir(d):
        abort(404)
    return send_from_directory(d, filename, as_attachment=True)


@app.route('/asset/<name>/<path:filename>')
def asset(name, filename):
    d = os.path.join(scene.SCENES, name)
    if not os.path.isdir(d):
        abort(404)
    return send_from_directory(d, filename)


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    print('Сервис 2021: доводка траектории реза руками')
    print(f'сцены: {scene.SCENES}')
    # 127.0.0.1, не 0.0.0.0 - робоче місце оператора одне, доступ по мережі
    # не потрібен (навпаки, зайвий ризик), сервіс не повинен бути видний
    # нікому іншому в локальній мережі.
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT', 2021)), debug=False)
