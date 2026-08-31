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
const M = { img: new Image(), scale: 0.25, ox: 0, oy: 0, manual: [],
           drag: null, variant: null, view: null, touched: false, drawing: false,
           auto: null, autoAdj: { dx: 0, dy: 0, rot: 0 } };
const $m = id => document.getElementById(id);

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

  // Жовта чернетка - гладкий контур CAD-обода на номінальній позі (без
  // підгонки, /api/mark/template), а не шумна піксельна трасування. Завжди
  // суцільна - тут нема поняття "невпевненості", як у детектора, форма не
  // залежить від конкретного фото. Показується ЛИШЕ поки в M.manual ще нема
  // жодної точки (щойно оператор застосував її або намалював свою - чернетка
  // ховається, плутати з чимось уже готовим не повинна).
  if (M.auto && !M.manual.length) {
    const pts = autoTransformed();
    mctx.lineWidth = 2; mctx.strokeStyle = '#facc15';
    mctx.beginPath();
    pts.forEach(([x, y], i) => {
      const [sx, sy] = mToScreen(x, y);
      i ? mctx.lineTo(sx, sy) : mctx.moveTo(sx, sy);
    });
    mctx.stroke();
  }

  if (M.manual.length) {
    // НЕ сортувати по x - лінія згину не завжди монотонна по x (виміряно на
    // шаблоні з CAD: до 32% сегментів "назад" по x на ракурсі back, біля
    // країв/вух). Сортування по x там перемішувало правильно впорядковані
    // точки і давало ті самі "гори"/ривки, про які повідомив користувач.
    // M.manual зберігається вже у правильному порядку вздовж лінії
    // (insertManualPoint вставляє нову точку в найкраще місце вздовж шляху,
    // не в кінець і не за x).
    const pts = M.manual;
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

// Жорсткий зсув+поворот чернетки навколо її ж центроїда - той самий принцип,
// що й групова правка в 3D-в'ювері (viewer.js::buildGroupEditor), тільки в
// 2D-піксельних координатах фото. Повертає [x, y, ok] на точку.
function autoTransformed() {
  if (!M.auto) return null;
  const { x, y } = M.auto;
  const cx = x.reduce((a, b) => a + b, 0) / x.length;
  const cy = y.reduce((a, b) => a + b, 0) / y.length;
  const rad = M.autoAdj.rot * Math.PI / 180, c = Math.cos(rad), s = Math.sin(rad);
  const out = [];
  for (let i = 0; i < x.length; i++) {
    const rx = x[i] - cx, ry = y[i] - cy;
    out.push([cx + rx * c - ry * s + M.autoAdj.dx, cy + rx * s + ry * c + M.autoAdj.dy]);
  }
  return out;
}
// Перетворює поточну (можливо зсунуту/повернуту) чернетку на звичайні "ваші"
// точки - розріджено (кожна N-та), щоб далі з нею можна було працювати як із
// будь-якою ручною лінією (klik по точці - прибрати, клік деінде - додати).
function applyAutoAsManual() {
  const pts = autoTransformed();
  if (!pts) return;
  pushHistory();
  // Рівномірно по ДОВЖИНІ ШЛЯХУ, не по індексу - однаковий крок по індексу
  // лишав нерівні, іноді дуже помітні розриви ("гори/ривки", реальний звіт
  // користувача) там, де крива йде "швидше" на екрані (типово - ближче до
  // країв видимої дуги, біля вух). Той самий принцип, що вже використовує
  // contour_fit.py::resample() на бекенді - параметризація по кумулятивній
  // довжині, не по порядковому номеру точки.
  const target = 40;
  const dist = [0];
  for (let i = 1; i < pts.length; i++) {
    dist.push(dist[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  }
  const total = dist[dist.length - 1];
  M.manual = [];
  for (let k = 0; k < target; k++) {
    const want = total * k / (target - 1);
    let i = 0;
    while (i < dist.length - 2 && dist[i + 1] < want) i++;
    const segLen = dist[i + 1] - dist[i] || 1;
    const t = (want - dist[i]) / segLen;
    M.manual.push([
      Math.round(pts[i][0] + t * (pts[i + 1][0] - pts[i][0])),
      Math.round(pts[i][1] + t * (pts[i + 1][1] - pts[i][1])),
    ]);
  }
  document.getElementById('autoAdjBox').hidden = true;
  mRefreshManual();
  mdraw();
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
  pushHistory();
  if (near >= 0) M.manual.splice(near, 1);
  else insertManualPoint([Math.round(ix), Math.round(iy)]);
  if (M.manual.length) document.getElementById('autoAdjBox').hidden = true;
  mRefreshManual();
  mdraw();
});
// Вставляє нову точку в НАЙКРАЩЕ місце вздовж поточної лінії (мінімальний
// приріст довжини шляху), а не в кінець масиву і не за сортуванням по x -
// лінія згину не завжди монотонна по x (див. коментар у mdraw()). Лінія
// вважається розімкненою (не кільцем) - додавання в самий початок теж
// перевіряється окремо.
function insertManualPoint(pt) {
  const n = M.manual.length;
  if (n < 2) { M.manual.push(pt); return; }
  const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
  let bestIdx = n, bestCost = dist(M.manual[n - 1], pt);
  for (let i = 0; i < n - 1; i++) {
    const cost = dist(M.manual[i], pt) + dist(pt, M.manual[i + 1]) - dist(M.manual[i], M.manual[i + 1]);
    if (cost < bestCost) { bestCost = cost; bestIdx = i + 1; }
  }
  const prependCost = dist(pt, M.manual[0]);
  if (prependCost < bestCost) bestIdx = 0;
  M.manual.splice(bestIdx, 0, pt);
}
$m('mdraw').addEventListener('click', () => mSetDrawing(!M.drawing));

// Стек знімків ДО кожної правки - потрібен, бо insertManualPoint() вставляє
// нову точку в середину масиву (найкраще місце вздовж лінії), не завжди в
// кінець, тож просте "прибрати останній елемент масиву" (як було раніше)
// прибирало б не ту точку, що клацнули останньою.
M.history = [];
function pushHistory() {
  M.history.push(M.manual.map(p => p.slice()));
  if (M.history.length > 50) M.history.shift();
}
function mUndo() {
  if (!M.history.length) return;
  M.manual = M.history.pop();
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
  $m('markhud').textContent = `x ${Math.round(ix)}  y ${Math.round(iy)}   масштаб ${M.scale.toFixed(2)}`;
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

async function mSave() {
  await fetch(`/api/mark/lines/${M.variant}/${M.view}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ points: M.manual })
  });
  mstatus(`вашу лінію збережено (${M.manual.length} точок)`);
  if (window.refreshWizard) refreshWizard();
}

$m('msave').addEventListener('click', mSave);
$m('mclear').addEventListener('click', () => {
  pushHistory();
  M.manual = []; mRefreshManual();
  if (M.auto) document.getElementById('autoAdjBox').hidden = false;
  mdraw();
  mstatus('вашу лінію очищено (на диску лишилась, доки не збережете)');
});
$m('mfit').addEventListener('click', () => { M.touched = false; mresize(true); });

const AD_STEP_PX = 5, AD_STEP_ROT = 0.5;
$m('ad_xm').addEventListener('click', () => { M.autoAdj.dx -= AD_STEP_PX; mdraw(); });
$m('ad_xp').addEventListener('click', () => { M.autoAdj.dx += AD_STEP_PX; mdraw(); });
$m('ad_ym').addEventListener('click', () => { M.autoAdj.dy -= AD_STEP_PX; mdraw(); });
$m('ad_yp').addEventListener('click', () => { M.autoAdj.dy += AD_STEP_PX; mdraw(); });
$m('ad_rm').addEventListener('click', () => { M.autoAdj.rot -= AD_STEP_ROT; mdraw(); });
$m('ad_rp').addEventListener('click', () => { M.autoAdj.rot += AD_STEP_ROT; mdraw(); });
$m('ad_apply').addEventListener('click', applyAutoAsManual);

// -------------------------------------------------------------- відкрити/закрити
async function openMarkOverlay(variant, view) {
  M.variant = variant; M.view = view; M.manual = []; M.touched = false; M.history = [];
  M.auto = null; M.autoAdj = { dx: 0, dy: 0, rot: 0 };
  document.getElementById('autoAdjBox').hidden = true;
  document.getElementById('markOverlay').hidden = false;
  mSetDrawing(false);
  const saved = await (await fetch(`/api/mark/lines/${variant}/${view}`)).json();
  M.manual = saved.points || [];
  M.img = new Image();
  M.img.onload = () => { mresize(true); requestAnimationFrame(() => mresize(true)); };
  M.img.src = `/mark/img/${variant}/${view}.jpg?t=${Date.now()}`;
  mRefreshManual();
  // Чернетку з автодетектора пропонуємо ЛИШЕ якщо своєї лінії ще нема -
  // не хочемо непомітно підмінювати вже збережену ручну розмітку.
  if (!M.manual.length) {
    try {
      const res = await (await fetch(`/api/mark/template?view=${view}`)).json();
      if (res && res.x && res.y) {
        M.auto = { x: res.x, y: res.y };
        document.getElementById('autoAdjBox').hidden = false;
        mdraw();
      }
    } catch (e) { /* деталь не знайдена на фото - просто без чернетки */ }
  }
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
