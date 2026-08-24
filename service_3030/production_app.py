"""Запуск генерации .LS без консоли: положить фото в папку, нажать кнопку.

Как пользоваться:
  1. Создать папку service_3030/incoming/<имя>/
  2. Положить туда back.jpg (или .png), left.jpg, top.jpg - обычные фото,
     цветные или чёрно-белые, без разницы, робот в кадре быть не должен.
  3. Открыть http://localhost:3031, найти папку в списке.
  4. Разметить линию сгиба (кнопка "Разметить" - откроет app.py на 3030).
  5. Нажать "Сгенерировать .LS".

Фото сами копируются, куда их ждёт остальной код (archive/<имя>/) - руками
это делать больше не нужно, раньше я сам через это спотыкался.
"""
import os
import sys
import shutil
import io
import contextlib
from flask import Flask, jsonify, render_template_string, send_file

BASE = os.path.dirname(os.path.abspath(__file__))
S5056 = os.path.abspath(os.path.join(BASE, '..', 'service_5056'))
S2020 = os.path.abspath(os.path.join(BASE, '..', 'service_2020'))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(S5056, 'scripts'))

INCOMING = os.path.join(BASE, 'incoming')
ARCHIVE = os.path.join(S5056, 'input', 'archive')
LINES = os.path.join(BASE, 'data', 'lines')
OUT = os.path.join(BASE, 'out')
os.makedirs(INCOMING, exist_ok=True)

app = Flask(__name__)

PAGE = """
<!doctype html><html><head><meta charset="utf-8">
<title>Генерация .LS</title>
<style>
body{font-family:system-ui;max-width:900px;margin:30px auto;background:#1b1b1b;color:#eee}
.card{background:#262626;border:1px solid #444;border-radius:8px;padding:16px;margin-bottom:14px}
.ok{color:#7dd87d} .bad{color:#e88} a,button{color:#8ecbff}
button{background:#2d5a8c;border:none;padding:8px 14px;border-radius:5px;color:#fff;cursor:pointer;font-size:14px}
button:hover{background:#3a70ad}
pre{background:#111;padding:10px;border-radius:6px;white-space:pre-wrap;font-size:13px}
h1{font-size:20px} h2{font-size:16px;margin:0 0 8px}
.muted{color:#999;font-size:13px}
</style></head><body>
<h1>Генерация .LS лучшим методом (маркерные камеры + контур top)</h1>
<p class="muted">Папки ищутся в <code>service_3030/incoming/&lt;имя&gt;/</code> -
back.jpg/left.jpg/top.jpg (или .png), без робота в кадре.</p>
{% for f in folders %}
<div class="card">
  <h2>{{ f.name }}</h2>
  <p>
    фото: back {{ '✓' if f.back else '✗' }} · left {{ '✓' if f.left else '✗' }} · top {{ '✓' if f.top else '✗' }}
    &nbsp;|&nbsp;
    разметка: back {{ '✓' if f.mark_back else '✗' }} · left {{ '✓' if f.mark_left else '✗' }}
  </p>
  {% if f.back and f.left and f.top %}
    <a href="http://localhost:3030/" target="_blank">Разметить линию (app.py, порт 3030)</a>
    &nbsp;·&nbsp;
    {% if f.mark_back and f.mark_left %}
      <button onclick="gen('{{ f.name }}')">Сгенерировать .LS</button>
    {% else %}
      <span class="bad">сначала разметьте линию на back и left</span>
    {% endif %}
  {% else %}
    <span class="bad">не хватает фото</span>
  {% endif %}
  <div id="out-{{ f.name }}"></div>
</div>
{% endfor %}
{% if not folders %}<p class="muted">Папок в incoming/ пока нет.</p>{% endif %}
<script>
async function gen(name) {
  const box = document.getElementById('out-' + name);
  box.innerHTML = '<p class="muted">Считаю... (может занять пару минут)</p>';
  const r = await fetch('/generate/' + encodeURIComponent(name), {method: 'POST'});
  const j = await r.json();
  if (j.error) { box.innerHTML = '<pre class="bad">' + j.error + '</pre>'; return; }
  box.innerHTML = '<pre>' + j.log + '</pre>' +
    '<a href="/download/' + encodeURIComponent(name) + '">скачать ' + j.filename + '</a>';
}
</script>
</body></html>
"""


def scan():
    out = []
    if not os.path.isdir(INCOMING):
        return out
    for name in sorted(os.listdir(INCOMING)):
        d = os.path.join(INCOMING, name)
        if not os.path.isdir(d):
            continue
        views = {}
        for v in ('back', 'left', 'top'):
            views[v] = any(os.path.exists(os.path.join(d, v + ext))
                           for ext in ('.jpg', '.jpeg', '.png'))
        marks = {v: os.path.exists(os.path.join(LINES, f'{name}_{v}.json'))
                 for v in ('back', 'left')}
        out.append(dict(name=name, back=views['back'], left=views['left'],
                        top=views['top'], mark_back=marks['back'], mark_left=marks['left']))
    return out


def sync_to_archive(name):
    """Копирует фото из incoming/<name>/ в archive/<name>/, куда их ждёт остальной код."""
    src = os.path.join(INCOMING, name)
    dst = os.path.join(ARCHIVE, name)
    os.makedirs(dst, exist_ok=True)
    for v in ('back', 'left', 'top'):
        for ext in ('.jpg', '.jpeg', '.png'):
            p = os.path.join(src, v + ext)
            if os.path.exists(p):
                shutil.copy(p, os.path.join(dst, v + '.png'))
                break


@app.route('/')
def index():
    return render_template_string(PAGE, folders=scan())


@app.route('/generate/<name>', methods=['POST'])
def generate(name):
    try:
        sync_to_archive(name)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            import export_cad_ls_contour as C
            import export_scene as XS, exp_cad_fit as F, exp_all_methods as A
            import features as f5, fit_model, line_features
            import exp_three_cams as T
            marks = line_features.load_marks()
            rim = XS.mesh_rim(F.STL)
            verts_ = __import__('numpy').unique(F.load_stl(F.STL).reshape(-1, 3), axis=0)
            cams = T.marker_cams()
            R0, t0 = A.cad_start()
            every = A.TRAIN + A.CLEAN
            for v in every:
                fit_model.standoff(v)
            F_all = f5.load(every + [name])
            path = C.export(name, rim, verts_, marks, cams, R0, t0, F_all)
        return jsonify(log=buf.getvalue(), filename=os.path.basename(path))
    except Exception as e:
        return jsonify(error=f'{type(e).__name__}: {e}')


@app.route('/download/<name>')
def download(name):
    matches = [f for f in os.listdir(OUT) if name.upper() in f.upper() and f.startswith('DISTI_CADC')]
    if not matches:
        return 'не найдено', 404
    return send_file(os.path.join(OUT, sorted(matches)[-1]), as_attachment=True)


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print('Генерация .LS без консоли: http://localhost:3031')
    print(f'кладите фото в: {INCOMING}')
    app.run(host='0.0.0.0', port=3031, debug=False)
