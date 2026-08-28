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


@app.route('/api/mark/profile')
def mark_profile():
    from pipeline import detect
    img = _mark_load(request.args.get('variant'), request.args.get('view'))
    if img is None:
        return jsonify(error='немає такого знімку'), 404
    return jsonify(detect.profile_at(img, float(request.args.get('x', 0)),
                                     float(request.args.get('y', 0))))


@app.route('/api/mark/lines/<variant>/<view>', methods=['GET', 'POST'])
def mark_lines(variant, view):
    from pipeline import line_marks
    p = os.path.join(line_marks.LINES, f'{variant}_{view}.json')
    if request.method == 'POST':
        data = request.get_json(force=True) or {}
        data['variant'], data['view'] = variant, view
        os.makedirs(line_marks.LINES, exist_ok=True)
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        return jsonify(status='saved')
    if not os.path.exists(p):
        return jsonify(points=[])
    with open(p, encoding='utf-8') as f:
        return jsonify(json.load(f))


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
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 2021)), debug=False)
