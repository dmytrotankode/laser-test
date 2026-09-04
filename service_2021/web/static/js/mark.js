// Розмітка лінії згину - вендорено з service_3030/web/static/js/app.js.
//
// Окремий 2D-інструмент (не 3D-в'ювер): зум тут не зручність, а вимога - на
// картинці, зменшеній вчетверо, промах лінії в 15 px не видно. Координати
// завжди живуть у повному розділенні знімка, масштаб лише міняє те, як ми
// на нього дивимось. Формат data/lines/<variant>_<view>.json той самий, що
// вже читає pipeline/line_marks.py - жодної конвертації не потрібно.
'use strict';

const mcv = document.getElementById('markcv'), mctx = mcv.getContext('2d');
// tplTotals - точно той самий підсумок "зсув X/Y/Z, поворот X/Y/Z, масштаб %",
// що й totals у buildGroupEditor() (viewer.js) для лінії різу - тут лише
// застосовується на сервері (rim + off) до проекції в камеру, а не локально
// до вже готових точок (тому й totals, а не одноразова дельта).
// Функція, не спільний об'єкт зі спред-копією - rot/t це масиви, поверхнева
// копія {...x} лишила б їх СПІЛЬНИМИ між M.tplTotals і "дефолтом" (реальний
// ризик: правка одного мовчки псувала б інший).
function freshTplTotals() { return { rot: [0, 0, 0], t: [0, 0, 0], scale: 100 }; }
const M = { img: new Image(), scale: 0.25, ox: 0, oy: 0, manual: [],
           drag: null, variant: null, view: null, touched: false, drawing: false,
           auto: null, tplTotals: freshTplTotals(), refFull: null };
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
  // підгонки, /api/mark/template), а не шумна піксельна трасування. Яскрава
  // суцільна, поки в M.manual ще нема жодної точки (тут нема поняття
  // "невпевненості", як у детектора, форма не залежить від конкретного фото).
  if (M.auto && !M.manual.length) {
    mctx.lineWidth = 2; mctx.strokeStyle = '#facc15';
    mctx.beginPath();
    M.auto.x.forEach((x, i) => {
      const [sx, sy] = mToScreen(x, M.auto.y[i]);
      i ? mctx.lineTo(sx, sy) : mctx.moveTo(sx, sy);
    });
    mctx.stroke();
  }

  // Щойно оператор натиснув "Застосувати як лінію" - ПОВНИЙ ЗАМКНЕНИЙ контур
  // (не лише видима near_arc-половина) лишається тьмяним пунктиром позаду:
  // не для правки, а щоб бачити "як воно йде" цілком, включно з частиною,
  // що йде за фото - той самий принцип, що й еталонна лінія в основному
  // 3D-перегляді. Знімок стану НА МОМЕНТ застосування (M.refFull), тому не
  // рухається, коли оператор потім тягає окремі точки вручну.
  if (M.refFull && M.manual.length) {
    mctx.lineWidth = 1.5; mctx.strokeStyle = 'rgba(250,204,21,0.35)';
    mctx.setLineDash([7, 6]);
    mctx.beginPath();
    M.refFull.forEach(([x, y], i) => {
      const [sx, sy] = mToScreen(x, y);
      i ? mctx.lineTo(sx, sy) : mctx.moveTo(sx, sy);
    });
    mctx.closePath();
    mctx.stroke();
    mctx.setLineDash([]);
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

// Перетворює поточну (можливо зсунуту/повернуту) чернетку на звичайні "ваші"
// точки - розріджено (кожна N-та), щоб далі з нею можна було працювати як із
// будь-якою ручною лінією (klik по точці - прибрати, клік деінде - додати).
async function applyAutoAsManual() {
  if (!M.auto) return;
  const pts = M.auto.x.map((x, i) => [x, M.auto.y[i]]);
  // Знімок ПОВНОГО контуру на момент застосування, з тими самими totals -
  // для тьмяної лінії-довідки, що лишається позаду (див. mdraw()).
  M.refFull = await projectFullRim(M.view, M.tplTotals);
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
  showChernetkaUI(false);
  mRefreshManual();
  mdraw();
}

// Сайдбар-блок (опис + "Застосувати") і плаваюча панель зсув/поворот/масштаб
// над фото завжди показуються/ховаються РАЗОМ - панель без пояснення й кнопки
// "Застосувати" поруч була б незрозумілою, а показ панелі без активної
// чернетки (M.auto === null) не має сенсу.
function showChernetkaUI(show) {
  document.getElementById('autoAdjBox').hidden = !show;
  document.getElementById('markPad').hidden = !show;
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
  if (M.manual.length) showChernetkaUI(false);
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
  if (M.drag) { M.ox = e.offsetX - M.drag[0]; M.oy = e.offsetY - M.drag[1]; M.touched = true; mdraw(); }
});
window.addEventListener('mouseup', () => {
  M.drag = null;
  mcv.style.cursor = M.drawing ? 'crosshair' : 'grab';
});

// Розмітка йде по черзі: спочатку left, потім back - підганяти лінію одразу
// під два фото складніше, ніж по одному (реальний запит користувача), а
// оператору й не треба вибирати вид заздалегідь - "Зберегти" сам веде далі.
const MARK_SEQUENCE = ['left', 'back'];

async function mSave() {
  await fetch(`/api/mark/lines/${M.variant}/${M.view}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ points: M.manual })
  });
  const next = MARK_SEQUENCE[MARK_SEQUENCE.indexOf(M.view) + 1];
  if (next) {
    mstatus(`${M.view} збережено (${M.manual.length} точок) - переходжу до ${next}...`);
    openMarkOverlay(M.variant, next);
  } else {
    mstatus(`вашу лінію збережено (${M.manual.length} точок)`);
    document.getElementById('markOverlay').hidden = true;
    if (window.refreshWizard) refreshWizard();
  }
}

$m('msave').addEventListener('click', mSave);
$m('mclear').addEventListener('click', () => {
  pushHistory();
  M.manual = []; mRefreshManual();
  if (M.auto) showChernetkaUI(true);
  mdraw();
  mstatus('вашу лінію очищено (на диску лишилась, доки не збережете)');
});
$m('mfit').addEventListener('click', () => { M.touched = false; mresize(true); });

// Крок - той самий 0.1/1/5/10, що й у груповій правці лінії різу (viewer.js),
// використовується напряму як мм (зсув), градуси (поворот) чи % (масштаб) -
// без окремих "базових" констант, щоб не плутати з їхнім змістом.
let AD_MULT = 1;

// Шаблон (M.auto) - завжди РЕЗУЛЬТАТ проекції з сервера для ПОТОЧНИХ totals
// (rim+off повернутий/зсунутий/масштабований навколо власного центроїда в
// світових координатах, ДО проекції в камеру near_arc) - жодної локальної
// піксельної правки на клієнті, той самий принцип, що й у templateTranslate/
// templateRotate/templateScaleTo для жовтої лінії на кроці 4, лише порахований
// на сервері (бо тут потрібен ще й near_arc - видима половина кільця).
async function fetchAutoTemplate(view, totals) {
  const t = totals || freshTplTotals();
  try {
    const q = `?view=${view}&rx=${t.rot[0]}&ry=${t.rot[1]}&rz=${t.rot[2]}`
      + `&dx=${t.t[0]}&dy=${t.t[1]}&dz=${t.t[2]}&scale=${t.scale}`;
    const res = await (await fetch(`/api/mark/template${q}`)).json();
    return (res && res.x && res.y) ? { x: res.x, y: res.y } : null;
  } catch (e) { return null; }
}

// Змінити totals і перевантажити чернетку з сервера - спільний шлях для всіх
// кнопок панелі.
async function adjustMark(mutate) {
  mutate(M.tplTotals);
  const a = await fetchAutoTemplate(M.view, M.tplTotals);
  if (a) { M.auto = a; mdraw(); }
}

// Калібрування камер back/left - НЕ з scene.cameras основного в'ювера: для
// щойно завантаженого набору (ще не порахованого через "Розрахувати")
// scene.json не існує, а без нього в'ювер нічого не завантажив (scene===null
// або лишилась чужа сцена з попереднього сеансу) - саме тому іконки панелі
// зривались на дефолтні -/+ лише для НОВИХ наборів, а для вже порахованих
// працювали (реальний звіт користувача). /api/mark/cameras віддає ту саму
// калібровку стенду незалежно від того, яка сцена (якщо взагалі якась)
// зараз завантажена у в'ювері.
let markCamerasCache = null;
async function ensureMarkCameras() {
  if (!markCamerasCache) {
    try { markCamerasCache = await (await fetch('/api/mark/cameras')).json(); }
    catch (e) { markCamerasCache = {}; }
  }
  return markCamerasCache;
}

// Повний (не near_arc-відсічений) контур - лінія згину насправді ЗАМКНЕНА,
// просто камера бачить лише її ближню половину; та частина, що "йде за
// фото" (дальня половина кільця), теж належить до тієї ж лінії. Той самий
// /api/mark/template3d, що й жовта лінія на кроці 4 (той самий контур,
// нічого нового не вигадуємо) - лише спроєцьований у пікселі ЦІЄЇ камери
// розмітки з ТИМИ САМИМИ totals, що й поточна (near_arc-відсічена) чернетка,
// щоб обидві лягали одна на одну там, де співпадають.
const IMG_W = 4096, IMG_H = 3000;   // camera_model.IMG_W/IMG_H (фіксовані для всіх камер)
let fullRimBase = null;
async function ensureFullRimBase() {
  if (!fullRimBase) {
    try {
      const res = await (await fetch('/api/mark/template3d')).json();
      if (res && res.points) fullRimBase = res.points;
    } catch (e) { /* немає - просто без повного контуру */ }
  }
  return fullRimBase;
}
async function projectFullRim(view, totals) {
  const [base, cams] = await Promise.all([ensureFullRimBase(), ensureMarkCameras()]);
  const cam = cams[view];
  if (!base || !cam) return null;
  const R = rotFromDeg(totals.rot);
  const c0 = base.reduce((a, p) => [a[0] + p[0], a[1] + p[1], a[2] + p[2]], [0, 0, 0])
    .map(v => v / base.length);
  const s = totals.scale / 100;
  const Rc = rodrigues(cam.rotation), C = cam.position, f = cam.focal_px;
  return base.map(p => {
    const rel = [p[0] - c0[0], p[1] - c0[1], p[2] - c0[2]];
    const rot = mulv(R, rel);
    const world = [c0[0] + rot[0] * s + totals.t[0], c0[1] + rot[1] * s + totals.t[1],
                    c0[2] + rot[2] * s + totals.t[2]];
    const v = mulv(Rc, sub(world, C));
    return [f * v[0] / v[2] + IMG_W / 2, f * v[1] / v[2] + IMG_H / 2];
  });
}

// Панель зсув/поворот/масштаб - буквально та сама структура і ті самі
// функції (screenPlanar/shiftGlyphs/rotIconSVG), що й axisPad/tplPad для
// лінії різу в основному 3D-перегляді (viewer.js), лише з ротацією камери
// ФІКСОВАНОЇ камери розмітки (M.view) замість поточного camIndex - будується
// ОДИН РАЗ на відкриття/перегенерацію (напрямок камери під час розмітки не
// змінюється), а не на кожен клік.
async function buildMarkPad() {
  const cams = await ensureMarkCameras();
  const camRot = cams[M.view] ? cams[M.view].rotation : null;

  const shiftRow = document.getElementById('mkShift'); shiftRow.innerHTML = '';
  const shiftDefs = [['зсв X', [1, 0, 0]], ['зсв Y', [0, 1, 0]], ['зсв Z', [0, 0, 1]]];
  shiftDefs.forEach(([label, axis], i) => {
    if (screenPlanar(axis, camRot) < 0.35) return;
    const [g1, g2] = shiftGlyphs(axis, camRot);
    const g = document.createElement('div'); g.className = 'padGroup'; g.title = label;
    const bMinus = document.createElement('button'); bMinus.textContent = g1;
    bMinus.onclick = () => adjustMark(t => { t.t[i] -= AD_MULT; });
    const bPlus = document.createElement('button'); bPlus.textContent = g2;
    bPlus.onclick = () => adjustMark(t => { t.t[i] += AD_MULT; });
    g.append(bMinus, bPlus);
    shiftRow.appendChild(g);
  });

  const rotRow = document.getElementById('mkRotate'); rotRow.innerHTML = '';
  const rotDefs = [
    ['пов X', [0, 1, 0], [0, 0, 1]],
    ['пов Y', [0, 0, 1], [1, 0, 0]],
    ['пов Z', [1, 0, 0], [0, 1, 0]],
  ];
  rotDefs.forEach(([label, u, v], i) => {
    const g = document.createElement('div'); g.className = 'padGroup'; g.title = label;
    const bMinus = document.createElement('button'); bMinus.innerHTML = rotIconSVG(u, v, -1, camRot) || '⟲';
    bMinus.onclick = () => adjustMark(t => { t.rot[i] -= AD_MULT; });
    const bPlus = document.createElement('button'); bPlus.innerHTML = rotIconSVG(u, v, 1, camRot) || '⟳';
    bPlus.onclick = () => adjustMark(t => { t.rot[i] += AD_MULT; });
    g.append(bMinus, bPlus);
    rotRow.appendChild(g);
  });

  const scaleRow = document.getElementById('mkScale'); scaleRow.innerHTML = '';
  {
    const g = document.createElement('div'); g.className = 'padGroup'; g.title = 'масштаб';
    const bMinus = document.createElement('button'); bMinus.textContent = '−';
    bMinus.onclick = () => adjustMark(t => { t.scale = Math.max(50, t.scale - AD_MULT); });
    const bPlus = document.createElement('button'); bPlus.textContent = '+';
    bPlus.onclick = () => adjustMark(t => { t.scale = Math.min(200, t.scale + AD_MULT); });
    g.append(bMinus, bPlus);
    scaleRow.appendChild(g);
  }

  const stepRow = document.getElementById('mkStep'); stepRow.innerHTML = '';
  const stepGroup = document.createElement('div'); stepGroup.className = 'padGroup'; stepGroup.title = 'крок';
  for (const v of [0.1, 1, 5, 10]) {
    const b = document.createElement('button'); b.textContent = v;
    b.classList.toggle('on', v === AD_MULT);
    b.onclick = () => { AD_MULT = v; [...stepGroup.children].forEach(x => x.classList.toggle('on', +x.textContent === AD_MULT)); };
    stepGroup.appendChild(b);
  }
  stepRow.appendChild(stepGroup);

  const resetRow = document.getElementById('mkReset'); resetRow.innerHTML = '';
  const bReset = document.createElement('button'); bReset.textContent = 'Скинути';
  bReset.onclick = () => adjustMark(t => { t.rot = [0, 0, 0]; t.t = [0, 0, 0]; t.scale = 100; });
  resetRow.appendChild(bReset);
}
$m('ad_apply').addEventListener('click', applyAutoAsManual);

// Перегенерувати чернетку в БУДЬ-ЯКИЙ момент (не лише на порожній лінії, як
// раніше) - реальний запит користувача: іноді простіше почати з чистого
// номінального контуру, ніж вручну повертати вже застосовану/збережену
// розмітку назад. Якщо є що втрачати - явне попередження перед скиданням.
async function regenerateTemplate() {
  if (M.manual.length &&
      !confirm(`Поточна розмітка (${M.manual.length} точок) буде скинута. Продовжити?`)) {
    return;
  }
  pushHistory();
  M.manual = [];
  M.tplTotals = freshTplTotals();
  M.refFull = null;
  M.auto = await fetchAutoTemplate(M.view, M.tplTotals);
  if (M.auto) await buildMarkPad();
  showChernetkaUI(!!M.auto);
  mRefreshManual();
  mdraw();
}
$m('mregen').addEventListener('click', regenerateTemplate);

// -------------------------------------------------------------- відкрити/закрити
async function openMarkOverlay(variant, view) {
  M.variant = variant; M.view = view; M.manual = []; M.touched = false; M.history = [];
  M.auto = null; M.tplTotals = freshTplTotals(); M.refFull = null;
  showChernetkaUI(false);
  document.getElementById('markOverlay').hidden = false;
  mSetDrawing(false);
  const saved = await (await fetch(`/api/mark/lines/${variant}/${view}`)).json();
  M.manual = saved.points || [];
  M.img = new Image();
  M.img.onload = () => { mresize(true); requestAnimationFrame(() => mresize(true)); };
  M.img.src = `/mark/img/${variant}/${view}.jpg?t=${Date.now()}`;
  mRefreshManual();
  // Чернетку з автодетектора пропонуємо ЛИШЕ якщо своєї лінії ще нема -
  // не хочемо непомітно підмінювати вже збережену ручну розмітку. Якщо вона
  // вже є - "Згенерувати шаблон" завжди доступна поруч, з попередженням.
  if (!M.manual.length) {
    M.auto = await fetchAutoTemplate(view, M.tplTotals);
    if (M.auto) { await buildMarkPad(); showChernetkaUI(true); mdraw(); }
  }
}
$m('mclose').addEventListener('click', () => {
  document.getElementById('markOverlay').hidden = true;
  if (window.refreshWizard) refreshWizard();
});

document.getElementById('markopen').addEventListener('click', () => {
  const name = window.currentTargetName ? currentTargetName() : null;
  if (!name) { alert('спершу оберіть або введіть ім\'я набору в кроці 1'); return; }
  openMarkOverlay(name, MARK_SEQUENCE[0]);
});
