"""Сервис 2021: доводка траектории реза руками, поверх расчёта 3030.

Тот же принцип, что у 2020: сервис самостоятельный, не импортирует ни 5056,
ни 3030 - только читает и правит файл сцены. Кто его туда положил и что с ним
будет дальше - сервису безразлично.

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
