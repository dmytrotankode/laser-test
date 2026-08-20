"""Сервис 3030: разметка и подбор линии границы прессования.

Отдельный от 5056 инструмент. Из проекта только ЧИТАЕТ снимки
(service_5056/input/archive) - ничего там не меняет и ни на какие расчёты не
влияет.

Зачем он нужен: линия, по которой ориентируется оператор, до сих пор
подбиралась вслепую - я настраивал детектор на глаз, а результат оказывался не
на месте. Здесь заказчик размечает эталон руками, и у детектора появляется
объективная мера ошибки. Разметка кладётся в data/lines/*.json и читается
напрямую, без скриншотов.
"""
import os
import io
import sys
import json
import numpy as np
import cv2
from flask import Flask, jsonify, request, send_file, render_template

import detect
from shots import BASE, ARCHIVE, LINES, EXTRA, MM_PER_PX, img_path

os.makedirs(LINES, exist_ok=True)

app = Flask(__name__, template_folder='web/templates', static_folder='web/static')

# Шаблоны и статика перечитываются с диска на каждый запрос. Без этого Flask
# кэширует их при debug=False, и правку в index.html или app.js не видно, пока
# не перезапустишь сервер. Инструмент отладочный, цена перечитывания никакая,
# зато перезапуск нужен только после правок в .py
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


@app.after_request
def no_cache(resp):
    if request.path.startswith('/static/'):
        resp.headers['Cache-Control'] = 'no-store'
    return resp


_cache = {}


def load(variant, view):
    key = (variant, view)
    if key not in _cache:
        p = img_path(variant, view)
        if not os.path.exists(p):
            return None
        _cache.clear()                     # снимки большие, держим один
        _cache[key] = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
    return _cache[key]


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/shots')
def shots():
    out = []
    names = [d for d in sorted(os.listdir(ARCHIVE), key=lambda s: (len(s), s))
             if os.path.isdir(os.path.join(ARCHIVE, d))]
    names += [k for k in EXTRA if os.path.isdir(EXTRA[k])]
    for d in names:
        views = [v for v in ('back', 'left', 'top')
                 if os.path.exists(img_path(d, v))]
        if views:
            out.append(dict(variant=d, views=views,
                            marked=[v for v in views
                                    if os.path.exists(os.path.join(
                                        LINES, f'{d}_{v}.json'))]))
    return jsonify(out)


@app.route('/img/<variant>/<view>.jpg')
def image(variant, view):
    img = load(variant, view)
    if img is None:
        return 'no such shot', 404
    ok, buf = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return send_file(io.BytesIO(buf.tobytes()), mimetype='image/jpeg')


@app.route('/api/detect')
def api_detect():
    variant = request.args.get('variant')
    view = request.args.get('view')
    img = load(variant, view)
    if img is None:
        return jsonify(error='no such shot'), 404
    kw = {}
    for k in detect.DEFAULTS:
        v = request.args.get(k)
        if v not in (None, ''):
            kw[k] = float(v) if k in ('band_lo', 'band_hi', 'edge') else int(float(v))
    res = detect.find_lines(img, **kw)
    if res is None:
        return jsonify(error='деталь на снимке не найдена'), 400
    res['mm_per_px'] = MM_PER_PX.get(view, 0.09)
    return jsonify(res)


@app.route('/api/profile')
def api_profile():
    img = load(request.args.get('variant'), request.args.get('view'))
    if img is None:
        return jsonify(error='no such shot'), 404
    return jsonify(detect.profile_at(img, float(request.args.get('x', 0)),
                                     float(request.args.get('y', 0))))


@app.route('/api/lines/<variant>/<view>', methods=['GET', 'POST'])
def lines(variant, view):
    p = os.path.join(LINES, f'{variant}_{view}.json')
    if request.method == 'POST':
        data = request.get_json(force=True) or {}
        data['variant'], data['view'] = variant, view
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        return jsonify(status='saved', path=os.path.relpath(p, BASE))
    if not os.path.exists(p):
        return jsonify(points=[])
    with open(p, encoding='utf-8') as f:
        return jsonify(json.load(f))


@app.route('/api/compare')
def compare():
    """Расхождение автоматических линий с ручной разметкой, px и мм."""
    variant, view = request.args.get('variant'), request.args.get('view')
    p = os.path.join(LINES, f'{variant}_{view}.json')
    if not os.path.exists(p):
        return jsonify(error='эталон не размечен')
    with open(p, encoding='utf-8') as f:
        pts = json.load(f).get('points', [])
    if len(pts) < 2:
        return jsonify(error='в эталоне меньше двух точек')
    img = load(variant, view)
    kw = {}
    for k in detect.DEFAULTS:
        v = request.args.get(k)
        if v not in (None, ''):
            kw[k] = float(v) if k in ('band_lo', 'band_hi', 'edge') else int(float(v))
    res = detect.find_lines(img, **kw)
    if res is None:
        return jsonify(error='деталь на снимке не найдена')

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


if __name__ == '__main__':
    # Консоль Windows по умолчанию cp1252/cp866 и на кириллице падает.
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    print('Сервис 3030: разметка линии границы прессования')
    print(f'снимки: {ARCHIVE}')
    print(f'разметка: {LINES}')
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3030)), debug=False)
