// Сервис 3030: просмотр снимка с зумом, наложение найденных линий и ручная разметка.
//
// Зум здесь не удобство, а требование: на картинке, уменьшенной вчетверо, промах
// линии в 15 px не виден - именно так и был сделан неверный вывод "легла точно".
// Поэтому координаты всегда живут в полном разрешении снимка, а масштаб только
// меняет то, как мы на него смотрим.

const cv = document.getElementById('cv'), ctx = cv.getContext('2d');
const prof = document.getElementById('prof'), pctx = prof.getContext('2d');
const S = { img: new Image(), scale: 0.25, ox: 0, oy: 0, lines: null, manual: [],
            drag: null, variant: null, view: null, mm: 0.09 };

const $ = id => document.getElementById(id);
const PARAMS = ['band_lo', 'win', 'jump', 'edge', 'smooth', 'step'];
const COLORS = { upper: '#38bdf8', center: '#f59e0b', lower: '#22c55e' };
const NAMES = { upper: 'верхня межа', center: 'дно борозни', lower: 'нижня межа' };

function status(t) { $('status').textContent = t || ''; }
function resize() { cv.width = cv.clientWidth; cv.height = cv.clientHeight; draw(); }
window.addEventListener('resize', resize);

// -------------------------------------------------------------- координаты
const toScreen = (x, y) => [x * S.scale + S.ox, y * S.scale + S.oy];
const toImage = (sx, sy) => [(sx - S.ox) / S.scale, (sy - S.oy) / S.scale];

function draw() {
  ctx.fillStyle = '#000';
  ctx.fillRect(0, 0, cv.width, cv.height);
  if (!S.img.width) return;
  ctx.imageSmoothingEnabled = S.scale < 1;
  ctx.drawImage(S.img, S.ox, S.oy, S.img.width * S.scale, S.img.height * S.scale);

  if (S.lines) {
    for (const key of ['upper', 'center', 'lower']) {
      if (!$('c_' + key).checked) continue;
      ctx.strokeStyle = COLORS[key];
      ctx.lineWidth = 1.6;
      ctx.beginPath();
      let started = false;
      S.lines.x.forEach((x, i) => {
        if (!S.lines.ok[i]) { started = false; return; }   // разрыв там, где ненадёжно
        const [sx, sy] = toScreen(x, S.lines[key][i]);
        started ? ctx.lineTo(sx, sy) : ctx.moveTo(sx, sy);
        started = true;
      });
      ctx.stroke();
    }
  }

  if ($('c_manual').checked && S.manual.length) {
    const pts = [...S.manual].sort((a, b) => a[0] - b[0]);
    ctx.strokeStyle = '#ef4444'; ctx.lineWidth = 2;
    ctx.beginPath();
    pts.forEach(([x, y], i) => {
      const [sx, sy] = toScreen(x, y);
      i ? ctx.lineTo(sx, sy) : ctx.moveTo(sx, sy);
    });
    ctx.stroke();
    ctx.fillStyle = '#ef4444';
    pts.forEach(([x, y]) => {
      const [sx, sy] = toScreen(x, y);
      ctx.beginPath(); ctx.arc(sx, sy, 4, 0, 7); ctx.fill();
    });
  }
}

// -------------------------------------------------------------- навигация
cv.addEventListener('wheel', e => {
  e.preventDefault();
  const [ix, iy] = toImage(e.offsetX, e.offsetY);
  S.scale *= e.deltaY < 0 ? 1.2 : 1 / 1.2;
  S.scale = Math.min(Math.max(S.scale, 0.05), 8);
  S.ox = e.offsetX - ix * S.scale;
  S.oy = e.offsetY - iy * S.scale;
  draw();
}, { passive: false });

cv.addEventListener('mousedown', e => {
  if (e.button === 1 || e.shiftKey) { S.drag = [e.offsetX - S.ox, e.offsetY - S.oy]; return; }
  const [ix, iy] = toImage(e.offsetX, e.offsetY);
  const near = S.manual.findIndex(([x, y]) =>
    Math.hypot(x - ix, y - iy) * S.scale < 8);
  if (near >= 0) S.manual.splice(near, 1);      // клик по точке - удалить
  else S.manual.push([Math.round(ix), Math.round(iy)]);
  draw();
});
cv.addEventListener('mousemove', e => {
  if (S.drag) { S.ox = e.offsetX - S.drag[0]; S.oy = e.offsetY - S.drag[1]; draw(); return; }
  const [ix, iy] = toImage(e.offsetX, e.offsetY);
  let extra = '';
  if (S.lines) {
    const i = S.lines.x.findIndex(x => x >= ix);
    if (i > 0) extra = ['upper', 'center', 'lower']
      .map(k => `${k[0]}:${Math.round(S.lines[k][i])}`).join('  ');
  }
  $('hud').textContent = `x ${Math.round(ix)}  y ${Math.round(iy)}   ` +
    `масштаб ${S.scale.toFixed(2)}   ${extra}`;
  clearTimeout(S.pt);
  S.pt = setTimeout(() => profile(ix, iy), 120);
});
window.addEventListener('mouseup', () => S.drag = null);

// профиль яркости поперёк линии - видно, где на самом деле дно
async function profile(x, y) {
  if (!S.variant) return;
  const r = await fetch(`/api/profile?variant=${S.variant}&view=${S.view}` +
                        `&x=${Math.round(x)}&y=${Math.round(y)}`);
  const d = await r.json();
  if (!d.values) return;
  const v = d.values, W = prof.width, H = prof.height;
  pctx.clearRect(0, 0, W, H);
  pctx.fillStyle = 'rgba(15,23,42,.9)'; pctx.fillRect(0, 0, W, H);
  const lo = Math.min(...v), hi = Math.max(...v) || 1;
  pctx.strokeStyle = '#e2e8f0'; pctx.lineWidth = 1; pctx.beginPath();
  v.forEach((val, i) => {
    const px = i / (v.length - 1) * W, py = H - (val - lo) / (hi - lo + 1e-6) * (H - 14) - 7;
    i ? pctx.lineTo(px, py) : pctx.moveTo(px, py);
  });
  pctx.stroke();
  const mid = (y - d.y0) / v.length * W;
  pctx.strokeStyle = '#ef4444'; pctx.beginPath();
  pctx.moveTo(mid, 0); pctx.lineTo(mid, H); pctx.stroke();
  pctx.fillStyle = '#94a3b8'; pctx.font = '10px monospace';
  pctx.fillText('яскравість поперек лінії', 6, 11);
}

// -------------------------------------------------------------- данные
async function loadShots() {
  const list = await (await fetch('/api/shots')).json();
  S.shots = list;
  $('variant').innerHTML = list.map(s =>
    `<option value="${s.variant}">${s.variant}${s.marked.length ? ' ●' : ''}</option>`).join('');
  onVariant();
}
function onVariant() {
  const s = S.shots.find(s => s.variant === $('variant').value);
  $('view').innerHTML = s.views.map(v => `<option>${v}</option>`).join('');
  onView();
}
async function onView() {
  S.variant = $('variant').value; S.view = $('view').value;
  S.lines = null; S.manual = [];
  const saved = await (await fetch(`/api/lines/${S.variant}/${S.view}`)).json();
  S.manual = saved.points || [];
  S.img = new Image();
  S.img.onload = () => {
    const k = Math.min(cv.width / S.img.width, cv.height / S.img.height) * 0.95;
    S.scale = k; S.ox = (cv.width - S.img.width * k) / 2;
    S.oy = (cv.height - S.img.height * k) / 2;
    draw();
  };
  S.img.src = `/img/${S.variant}/${S.view}.jpg?t=${Date.now()}`;
  status(`${S.variant} / ${S.view}` + (S.manual.length ? `, еталон: ${S.manual.length} точок` : ''));
}

const qs = () => PARAMS.map(p => `${p}=${$(p).value}`).join('&');

async function run() {
  status('шукаю…');
  const r = await fetch(`/api/detect?variant=${S.variant}&view=${S.view}&${qs()}`);
  const d = await r.json();
  if (d.error) { status('помилка: ' + d.error); return; }
  S.lines = d; S.mm = d.mm_per_px;
  const good = d.ok.filter(Boolean).length;
  status(`знайдено, надійних точок ${good} з ${d.ok.length}`);
  draw();
}

async function save() {
  await fetch(`/api/lines/${S.variant}/${S.view}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ points: S.manual, params: Object.fromEntries(
      PARAMS.map(p => [p, $(p).value])) })
  });
  status(`еталон збережено (${S.manual.length} точок)`);
  loadShots();
}

async function compare() {
  const d = await (await fetch(`/api/compare?variant=${S.variant}&view=${S.view}&${qs()}`)).json();
  if (d.error) { status(d.error); $('metrics').innerHTML = ''; return; }
  let html = '<tr><th>лінія</th><th>медіана</th><th>p90</th><th>зсув</th></tr>';
  for (const k of ['upper', 'center', 'lower']) {
    const m = d.metrics[k]; if (!m) continue;
    html += `<tr><td style="color:${COLORS[k]}">${NAMES[k]}</td>` +
            `<td>${m.median.toFixed(1)} px<br><span style="color:#94a3b8">` +
            `${m.median_mm.toFixed(2)} мм</span></td>` +
            `<td>${m.p90.toFixed(1)}</td><td>${m.bias > 0 ? '+' : ''}${m.bias.toFixed(1)}</td></tr>`;
  }
  $('metrics').innerHTML = html;
  status(`порівняно на ${d.covered} точках`);
}

PARAMS.forEach(p => {
  const el = $(p), out = $('v_' + p);
  const upd = () => out.textContent = el.value;
  el.addEventListener('input', upd); upd();
});
['c_upper', 'c_center', 'c_lower', 'c_manual'].forEach(id =>
  $(id).addEventListener('change', draw));
$('variant').addEventListener('change', onVariant);
$('view').addEventListener('change', onView);
$('run').addEventListener('click', run);
$('save').addEventListener('click', save);
$('cmp').addEventListener('click', compare);
$('clear').addEventListener('click', () => { S.manual = []; draw(); status('еталон очищено (не збережено)'); });

resize();
loadShots();
