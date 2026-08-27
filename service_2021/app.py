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
import sys
import json

from flask import Flask, jsonify, render_template, send_from_directory, abort, request

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
