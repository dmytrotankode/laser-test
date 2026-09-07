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
    """ЕКСПЕРИМЕНТАЛЬНО (варіант 3 з обговорення 2026-09-07, "авто-доведення") -
    оператор клацає кілька точок одразу на back І на left (з двох ракурсів split-
    режиму), кожен клік означає "оцю точку лінії реально видно ТУТ", і замість
    ручного пересування панеллю рахується ОДНА жорстка поза (поворот+зсув, без
    масштабу), що найкраще узгоджує ВСІ клацання одразу - scipy.least_squares по
    репроекції, той самий принцип, що contour_fit.resid_of, тільки на вже
    ПОТОЧНИХ точках лінії (з їхніми ручними правками), а не на CAD-ободі.

    Навмисно ІЗОЛЬОВАНО від pipeline/contour_fit.py: не змінює оптимізатор
    підгонки, не викликається з generate(), нічого не пише на диск сама (як і
    /api/mark/solve_pnp - лише рахує й повертає). Повертає totals (rot/t/scale)
    у ТОМУ САМОМУ форматі, що й /api/mark/solve_pnp - клієнт застосовує їх тим
    самим поворотом/зсувом навколо центроїда, що й ручні кнопки групової
    панелі, тому "Скасувати"/"Зберегти" продовжують працювати без жодних змін.
    Якщо ідея виявиться нестабільною - видалити цей маршрут і відповідний
    блок у mark.js/viewer.js можна незалежно від решти застосунку.
    """
    d = request.get_json(force=True) or {}
    corr = d.get('corr') or []
    if len(corr) < 4:
        return jsonify(error='потрібно мінімум 4 точки (бажано з обох ракурсів)'), 400

    p = os.path.join(scene.SCENES, name, 'scene.json')
    if not os.path.exists(p):
        abort(404)
    with open(p, encoding='utf-8') as f:
        doc = json.load(f)
    if not (0 <= cidx < len(doc['curves'])):
        abort(404)
    c = doc['curves'][cidx]
    P0 = np.array(c['points'], dtype=float)
    n = len(P0)
    for item in corr:
        if item.get('view') not in ('back', 'left') or not (0 <= item.get('idx', -1) < n):
            return jsonify(error='некоректні дані кореспонденції'), 400

    from scipy.optimize import least_squares
    from pipeline import generate as gen, contour_fit, camera_model as CM, geometry
    recipe = gen.load_recipe('production_2026-08-27')
    calib_dir = os.path.join(gen.CALIB, 'cameras', recipe['camera_calibration'])
    cams = contour_fit.marker_cams(calib_dir)

    center = P0.mean(0)
    views = [item['view'] for item in corr]
    img = np.array([item['img'] for item in corr], dtype=float)
    obj0 = P0[[item['idx'] for item in corr]]

    def resid(p6):
        R = cv2.Rodrigues(p6[:3])[0]
        obj = (obj0 - center) @ R.T + center + p6[3:6]
        out = []
        for i, view in enumerate(views):
            pc, f = cams[view]
            uv, _ = CM.project(obj[i:i + 1], pc[:3], pc[3:6], f)
            out.append(uv[0] - img[i])
        return np.concatenate(out)

    r = least_squares(resid, np.zeros(6), method='lm', max_nfev=400)
    R = cv2.Rodrigues(r.x[:3])[0]
    yaw, pitch, roll = geometry.ypr_from_rot(R)
    totals = dict(rot=[roll, pitch, yaw], t=r.x[3:6].tolist(), scale=100.0)
    return jsonify(totals=totals, cost=float(r.cost), n=len(corr))


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


@app.route('/api/generate/<name>', methods=['POST'])
def generate_ls(name):
    """Посчитать линию реза с нуля через свой пайплайн (pipeline/generate.py) и
    (пере)собрать сцену из результата - как build_scene.py, полностью
    перезаписывает scene.json. Использовать только для варианта без сохранённых
    правок (или когда затирание правок - осознанное решение)."""
    name = _safe_name(name)
    d = request.get_json(silent=True) or {}
    recipe_name = d.get('recipe', 'production_2026-08-27')
    from pipeline import generate as gen
    try:
        ls_path, report = gen.generate(name, recipe_name)
    except Exception as e:
        return jsonify(error=f'{type(e).__name__}: {e}'), 400

    recipe = gen.load_recipe(recipe_name)
    calib_dir = os.path.join(gen.CALIB, 'cameras', recipe['camera_calibration'])
    cams = {v: os.path.join(calib_dir, f'cam_{v}.npy') for v in ('back', 'left', 'top')}
    photo_dir = os.path.join(gen.ARCHIVE, name)
    photos = {v: os.path.join(photo_dir, f'{v}.png') for v in ('back', 'left', 'top')}
    build_scene.build(name, ls_path, cams, photos)

    return jsonify(status='ok', file=os.path.basename(ls_path), report=report)


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
