// Розмітка лінії згину - вендорено з service_3030/web/static/js/app.js.
//
// Окремий 2D-інструмент (не 3D-в'ювер): зум тут не зручність, а вимога - на
// картинці, зменшеній вчетверо, промах лінії в 15 px не видно. Координати
// завжди живуть у повному розділенні знімка, масштаб лише міняє те, як ми
// на нього дивимось. Формат data/lines/<variant>_<view>.json той самий, що
// вже читає pipeline/line_marks.py - жодної конвертації не потрібно.
'use strict';

const mcv = document.getElementById('markcv'), mctx = mcv.getContext('2d');
const mprof = document.getElementById('markprof'), mpctx = mprof.getContext('2d');
const M = { img: new Image(), scale: 0.25, ox: 0, oy: 0, lines: null, manual: [],
           drag: null, variant: null, view: null, touched: false, drawing: false };
const $m = id => document.getElementById(id);
const M_COLORS = { upper: '#38bdf8', center: '#f59e0b', lower: '#22c55e', edge_lo: '#c084fc' };
const M_NAMES = { upper: 'верхня межа', center: 'дно борозни', lower: 'нижня межа',
                  edge_lo: 'край напливу' };

function mstatus(t) { $m('mstatus').textContent = t || ''; }

function mfitView() {
  if (!M.img.width || !mcv.width) return;
  const k = Math.min(mcv.width / M.img.width, mcv.height / M.img.height) * 0.96;
  M.scale = k;
  M.ox = (mcv.width - M.img.width * k) / 2;
  M.oy = (mcv.height - M.img.height * k) / 2;
  mdraw();
}
function mresize(refit) {
  const r = mcv.parentElement.getBoundingClientRect();
  mcv.width = Math.max(1, Math.round(r.width));
  mcv.height = Math.max(1, Math.round(r.height));
  if (refit) mfitView(); else mdraw();
}
new ResizeObserver(() => {
  const had = mcv.width > 2;
  mresize(!M.touched);
  if (!had) mfitView();
}).observe(mcv.parentElement);

const mToScreen = (x, y) => [x * M.scale + M.ox, y * M.scale + M.oy];
const mToImage = (sx, sy) => [(sx - M.ox) / M.scale, (sy - M.oy) / M.scale];

function mdraw() {
  mctx.fillStyle = '#000';
  mctx.fillRect(0, 0, mcv.width, mcv.height);
  if (!M.img.width) return;
  mctx.imageSmoothingEnabled = M.scale < 1;
  mctx.drawImage(M.img, M.ox, M.oy, M.img.width * M.scale, M.img.height * M.scale);

  if (M.lines) {
    for (const key of ['upper', 'center', 'lower', 'edge_lo']) {
      if (!$m('mc_' + key).checked) continue;
      mctx.strokeStyle = M_COLORS[key];
      mctx.lineWidth = 1.6;
      mctx.beginPath();
      let started = false;
      M.lines.x.forEach((x, i) => {
        if (!M.lines.ok[i]) { started = false; return; }
        const [sx, sy] = mToScreen(x, M.lines[key][i]);
        started ? mctx.lineTo(sx, sy) : mctx.moveTo(sx, sy);
        started = true;
      });
      mctx.stroke();
    }
  }
  if ($m('mc_manual').checked && M.manual.length) {
    const pts = [...M.manual].sort((a, b) => a[0] - b[0]);
    mctx.strokeStyle = '#ef4444'; mctx.lineWidth = 2;
    mctx.beginPath();
    pts.forEach(([x, y], i) => {
      const [sx, sy] = mToScreen(x, y);
      i ? mctx.lineTo(sx, sy) : mctx.moveTo(sx, sy);
    });
    mctx.stroke();
    mctx.fillStyle = '#ef4444';
    pts.forEach(([x, y]) => {
      const [sx, sy] = mToScreen(x, y);
      mctx.beginPath(); mctx.arc(sx, sy, 4, 0, 7); mctx.fill();
    });
  }
}

mcv.addEventListener('wheel', e => {
  e.preventDefault();
  const [ix, iy] = mToImage(e.offsetX, e.offsetY);
  M.scale *= e.deltaY < 0 ? 1.2 : 1 / 1.2;
  M.scale = Math.min(Math.max(M.scale, 0.02), 12);
  M.ox = e.offsetX - ix * M.scale;
  M.oy = e.offsetY - iy * M.scale;
  M.touched = true;
  mdraw();
}, { passive: false });

function mSetDrawing(on) {
  M.drawing = on;
  $m('mdraw').textContent = on ? '✏️ Малювання: УВІМК' : '✏️ Малювання: вимк';
  $m('mdraw').classList.toggle('on', on);
  mcv.style.cursor = on ? 'crosshair' : 'grab';
}
mcv.addEventListener('mousedown', e => {
  const panning = !M.drawing || e.button === 1 || e.shiftKey;
  if (panning) {
    M.drag = [e.offsetX - M.ox, e.offsetY - M.oy];
    mcv.style.cursor = 'grabbing';
    return;
  }
  const [ix, iy] = mToImage(e.offsetX, e.offsetY);
  const near = M.manual.findIndex(([x, y]) => Math.hypot(x - ix, y - iy) * M.scale < 8);
  if (near >= 0) M.manual.splice(near, 1);
  else M.manual.push([Math.round(ix), Math.round(iy)]);
  mRefreshManual();
  mdraw();
});
$m('mdraw').addEventListener('click', () => mSetDrawing(!M.drawing));

function mUndo() {
  if (!M.manual.length) return;
  M.manual.pop();
  mRefreshManual();
  mdraw();
}
$m('mundo').addEventListener('click', mUndo);
window.addEventListener('keydown', e => {
  if (document.getElementById('markOverlay').hidden) return;
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
  if (e.key === 'd' || e.key === 'D' || e.key === 'в' || e.key === 'В') mSetDrawing(!M.drawing);
  if ((e.ctrlKey || e.metaKey) && (e.key === 'z' || e.key === 'Z' || e.key === 'я' || e.key === 'Я')) {
    e.preventDefault(); mUndo();
  }
});

function mRefreshManual() {
  const n = M.manual.length;
  $m('mcount').textContent = n;
  mstatus(`${M.variant} / ${M.view}` + (n ? `, вашa лінія: ${n} точок` : ', вашої лінії ще немає'));
}
mcv.addEventListener('mousemove', e => {
  if (M.drag) { M.ox = e.offsetX - M.drag[0]; M.oy = e.offsetY - M.drag[1]; M.touched = true; mdraw(); return; }
  const [ix, iy] = mToImage(e.offsetX, e.offsetY);
  let extra = '';
  if (M.lines) {
    const i = M.lines.x.findIndex(x => x >= ix);
    if (i > 0) extra = ['upper', 'center', 'lower', 'edge_lo']
      .map(k => `${k[0]}:${Math.round(M.lines[k][i])}`).join('  ');
  }
  $m('markhud').textContent = `x ${Math.round(ix)}  y ${Math.round(iy)}   масштаб ${M.scale.toFixed(2)}   ${extra}`;
  clearTimeout(M.pt);
  M.pt = setTimeout(() => mProfile(ix, iy), 120);
});
window.addEventListener('mouseup', () => {
  M.drag = null;
  mcv.style.cursor = M.drawing ? 'crosshair' : 'grab';
});

async function mProfile(x, y) {
  if (!M.variant) return;
  const r = await fetch(`/api/mark/profile?variant=${M.variant}&view=${M.view}&x=${Math.round(x)}&y=${Math.round(y)}`);
  const d = await r.json();
  if (!d.values) return;
  const v = d.values, W = mprof.width, H = mprof.height;
  mpctx.clearRect(0, 0, W, H);
  mpctx.fillStyle = 'rgba(15,23,42,.9)'; mpctx.fillRect(0, 0, W, H);
  const lo = Math.min(...v), hi = Math.max(...v) || 1;
  mpctx.strokeStyle = '#e2e8f0'; mpctx.lineWidth = 1; mpctx.beginPath();
  v.forEach((val, i) => {
    const px = i / (v.length - 1) * W, py = H - (val - lo) / (hi - lo + 1e-6) * (H - 14) - 7;
    i ? mpctx.lineTo(px, py) : mpctx.moveTo(px, py);
  });
  mpctx.stroke();
  const mid = (y - d.y0) / v.length * W;
  mpctx.strokeStyle = '#ef4444'; mpctx.beginPath();
  mpctx.moveTo(mid, 0); mpctx.lineTo(mid, H); mpctx.stroke();
  mpctx.fillStyle = '#94a3b8'; mpctx.font = '10px monospace';
  mpctx.fillText('яскравість поперек лінії', 6, 11);
}

async function mRun() {
  mstatus('шукаю…');
  const r = await fetch(`/api/mark/detect?variant=${M.variant}&view=${M.view}`);
  const d = await r.json();
  if (d.error) { mstatus('помилка: ' + d.error); return; }
  M.lines = d;
  const good = d.ok.filter(Boolean).length;
  mstatus(`знайдено, надійних точок ${good} з ${d.ok.length}`);
  mdraw();
}
async function mSave() {
  await fetch(`/api/mark/lines/${M.variant}/${M.view}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ points: M.manual })
  });
  mstatus(`вашу лінію збережено (${M.manual.length} точок)`);
  if (window.refreshWizard) refreshWizard();
}
async function mCompare() {
  const d = await (await fetch(`/api/mark/compare?variant=${M.variant}&view=${M.view}`)).json();
  if (d.error) { mstatus(d.error); $m('mmetrics').innerHTML = ''; return; }
  let html = '<tr><th>лінія</th><th>медіана</th><th>p90</th><th>зсув</th></tr>';
  for (const k of ['upper', 'center', 'lower']) {
    const m = d.metrics[k]; if (!m) continue;
    html += `<tr><td style="color:${M_COLORS[k]}">${M_NAMES[k]}</td>` +
            `<td>${m.median.toFixed(1)} px<br><span style="color:#94a3b8">${m.median_mm.toFixed(2)} мм</span></td>` +
            `<td>${m.p90.toFixed(1)}</td><td>${m.bias > 0 ? '+' : ''}${m.bias.toFixed(1)}</td></tr>`;
  }
  $m('mmetrics').innerHTML = html;
  mstatus(`порівняно на ${d.covered} точках`);
}

$m('mrun').addEventListener('click', mRun);
$m('msave').addEventListener('click', mSave);
$m('mcmp').addEventListener('click', mCompare);
$m('mclear').addEventListener('click', () => {
  M.manual = []; mRefreshManual(); mdraw();
  mstatus('вашу лінію очищено (на диску лишилась, доки не збережете)');
});
$m('mfit').addEventListener('click', () => { M.touched = false; mresize(true); });
['mc_upper', 'mc_center', 'mc_lower', 'mc_manual'].forEach(id => $m(id).addEventListener('change', mdraw));

// -------------------------------------------------------------- відкрити/закрити
async function openMarkOverlay(variant, view) {
  M.variant = variant; M.view = view; M.lines = null; M.manual = []; M.touched = false;
  document.getElementById('markOverlay').hidden = false;
  mSetDrawing(false);
  $m('mmetrics').innerHTML = '';
  const saved = await (await fetch(`/api/mark/lines/${variant}/${view}`)).json();
  M.manual = saved.points || [];
  M.img = new Image();
  M.img.onload = () => { mresize(true); requestAnimationFrame(() => mresize(true)); };
  M.img.src = `/mark/img/${variant}/${view}.jpg?t=${Date.now()}`;
  mRefreshManual();
}
$m('mclose').addEventListener('click', () => {
  document.getElementById('markOverlay').hidden = true;
  if (window.refreshWizard) refreshWizard();
});

document.getElementById('markopen').addEventListener('click', () => {
  const name = window.currentTargetName ? currentTargetName() : null;
  if (!name) { alert('спершу оберіть або введіть ім\'я набору в кроці 1'); return; }
  openMarkOverlay(name, document.getElementById('markview').value);
});
