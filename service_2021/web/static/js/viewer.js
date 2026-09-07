'use strict';
// Просмотрщик сцены. Без внешних библиотек - и не из аскетизма.
//
// Проекция здесь считается ТОЙ ЖЕ моделью камеры, в которой камеры посчитаны:
// Xc = R (X - C), пиксель = focal * Xc.xy / Xc.z + размер/2. Возьми мы готовый
// движок, режим "взгляд камерой" показывал бы похожую картинку, а не ту, что
// видит настоящая камера, и сверять с фотографией стало бы нельзя.

// cv/ctx - НЕ const: у режимі "2 ракурси" (split) вони на час рендеру/кліку
// однієї з панелей тимчасово підміняються на cv2/ctx2 (див. withPane2 нижче),
// щоб уся наявна логіка малювання й вибору точки (яка звертається до cv/ctx/
// camIndex/camZoom/camPanX/camPanY як до вільних змінних) працювала для ДРУГОЇ
// панелі без дублювання коду. Поза підміною cv/ctx завжди вказують на #c -
// саме тому одноракурсний режим і "back"-панель у split-режимі не потребують
// жодних змін у своїй логіці.
let cv = document.getElementById('c');
let ctx = cv.getContext('2d');
const cv2 = document.getElementById('c2');
const ctx2 = cv2.getContext('2d');
const HUD = document.getElementById('hud');

// Стан другої панелі (завжди камера "left"). Перша панель ("back") - це
// просто звичайні camIndex/camZoom/camPanX/camPanY, як у одноракурсному
// режимі, зафіксовані на камері back на час split-режиму.
let splitMode = false;
let activePane = 'back';    // яка панель востаннє була активна - куди дивиться плаваюча панель
const pane2 = { camIdx: -1, zoom: 1, panX: 0, panY: 0 };
let preSplit = null;        // збережений одноракурсний стан (camIndex/zoom/pan) - повернутись при виході

// ЕКСПЕРИМЕНТАЛЬНО (варіант 3, "авто-доведення", обговорено 2026-09-07) -
// клацнути кілька точок одразу на back+left замість ручного пересування
// панеллю; /api/scene/.../auto_pose рахує ОДНУ жорстку позу під усі
// клацання. Повністю ізольовано: свій прапорець/масив, свій маршрут на
// сервері, застосовує результат ЧЕРЕЗ ту саму rotFromDeg-математику, що й
// ручні кнопки - "Скасувати"/"Зберегти" в group-редакторі це не зачіпає.
// Якщо нестабільно - прибрати autoPoseMode/autoPoseCorr/recordAutoPoseClick/
// applyAutoPoseTotals і кнопки #autoPoseToggle/#autoPosePanel, більше нічого
// не займає.
let autoPoseMode = false;
const autoPoseCorr = [];    // [{view, idx, img:[u,v]}, ...]

let scene = null;           // документ сцены
let sceneName = null;
// Поле зрения узкое намеренно: на 45 градусах купол по краям кадра заметно
// растягивается, и это принимают за ошибку геометрии.
let view = { yaw: 0.9, pitch: 0.5, dist: 3000, target: [0, 0, 0], fov: 30 };
let camIndex = -1;          // -1 = свободный обзор, иначе индекс камеры сцены
let sel_point = null;        // {cidx, pidx} выбранной точки редактируемой кривой (тонкая правка)
let group_sel = [];           // [pidx, ...] группа для комплексного сдвига (Shift+клик)
let camZoom = 1, camPanX = 0, camPanY = 0;   // зум/сдвиг ТОЛЬКО картинки в виде камерой, не самой камеры
// Тимчасова допомога для очей при розгляданні/розмітці фото - НЕ зберігається
// ніде (ні в scene.json, ні в localStorage), скидається на 100/100 при
// кожному відкритті сторінки і кнопкою "Скинути".
let photoBrightness = 100, photoContrast = 100;
const NOMINAL_STANDOFF = 10.0;               // мм, тот же, что ls_points.NOMINAL_STANDOFF в 2021
const shown = {};           // имя слоя -> показывать
const photos = {};          // имя камеры -> Image
// Ручна розмітка лінії згину (крок 3, mark.js) - точки в ПІКСЕЛЯХ фото, не в
// координатах верстата, тому малюються тим самим f=pr.fit, що й саме фото,
// а не через звичайну 3D-проекцію pr.p(). Має сенс лише під тим самим видом
// камерою, з якого його малювали - на back-фото ліва розмітка беззмістовна.
const markLines = { back: [], left: [] };
const meshes = {};          // имя меша -> {tris:Float32Array}
// Пробна "шаблонна лінія" - той самий контур rim+off, що й у розмітці, але
// ПОВНИЙ ЗАМКНЕНИЙ і в світових координатах (/api/mark/template3d), не
// прив'язаний до пікселів одного фото - тому рухається ОДИН РАЗ (як лінія
// різу - зсув/поворот/масштаб навколо центроїда) і однаково видний під
// будь-яким ракурсом і у вільному огляді. Суто "пісочниця" для очей: ніде не
// зберігається, скидається на кожне завантаження сцени.
let templateBase = null;   // [[x,y,z],...] як прийшло з сервера, для "Скинути"
let templatePts = null;    // робоча (посунута) копія, що й малюється
const tplTotals = { rot: [0, 0, 0], t: [0, 0, 0], scale: 100 };
let tplStep = 1;

// ---------------------------------------------------------------- математика
function rodrigues(r) {
  const th = Math.hypot(r[0], r[1], r[2]);
  if (th < 1e-12) return [1, 0, 0, 0, 1, 0, 0, 0, 1];
  const [x, y, z] = [r[0] / th, r[1] / th, r[2] / th];
  const c = Math.cos(th), s = Math.sin(th), t = 1 - c;
  return [t * x * x + c, t * x * y - s * z, t * x * z + s * y,
          t * x * y + s * z, t * y * y + c, t * y * z - s * x,
          t * x * z - s * y, t * y * z + s * x, t * z * z + c];
}
const mulv = (R, v) => [R[0] * v[0] + R[1] * v[1] + R[2] * v[2],
                        R[3] * v[0] + R[4] * v[1] + R[5] * v[2],
                        R[6] * v[0] + R[7] * v[1] + R[8] * v[2]];
const trmulv = (R, v) => [R[0] * v[0] + R[3] * v[1] + R[6] * v[2],
                          R[1] * v[0] + R[4] * v[1] + R[7] * v[2],
                          R[2] * v[0] + R[5] * v[1] + R[8] * v[2]];
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];

// ------------------------------------------------ напрямок осі на екрані (лише вид з камери)
// Кнопки "пов X/Y/Z"/"зсв X/Y/Z" рухають точку вздовж осей ВЕРСТАТА, які не
// збігаються з тим, що оператор бачить на екрані під конкретним ракурсом
// камери - звідси й скарга "не можу второпати, куди що рухати" при вигляді
// з камери. Тут переводимо вісь верстата в напрямок на екрані ЦІЄЇ камери,
// щоб підписати кнопки стрілками за реальним рухом на фото. У вільному
// огляді (camIndex<0) сенсу нема - там саму камеру крутить миша, лишаємо
// звичайні -/+.
// camRotOverride - опційний rotation-вектор конкретної камери (як
// scene.cameras[i].rotation), в обхід поточного camIndex. Потрібен розмітці
// (mark.js): вона завжди дивиться з ФІКСОВАНОЇ камери view (back/left), не
// пов'язаної з тим, який ракурс зараз обраний в основному 3D-перегляді.
function camDir(vec, camRotOverride) {
  if (camRotOverride) return mulv(rodrigues(camRotOverride), vec);
  if (camIndex < 0 || !scene) return null;
  return mulv(rodrigues(scene.cameras[camIndex].rotation), vec);
}
const ARROWS8 = ['→', '↘', '↓', '↙', '←', '↖', '↑', '↗']; // → ↘ ↓ ↙ ← ↖ ↑ ↗
function arrow8(dx, dy) {
  let deg = Math.atan2(dy, dx) * 180 / Math.PI;
  if (deg < 0) deg += 360;
  return ARROWS8[Math.round(deg / 45) % 8];
}
// Якщо вісь лежить переважно У ПЛОЩИНІ екрана - підписуємо кнопки стрілками
// (+ у бік осі, - у протилежний). Якщо вісь дивиться переважно ВЗДОВЖ
// погляду камери (на глядача чи від нього) - стрілка була б непомітною і
// оманливою на майже нерухомій картинці, лишаємо звичайні -/+.
function shiftGlyphs(axis, camRot) {
  const d = camDir(axis, camRot);
  if (!d) return ['−', '+'];
  if (Math.hypot(d[0], d[1]) < 0.35) return ['−', '+'];
  return [arrow8(-d[0], -d[1]), arrow8(d[0], d[1])];
}
// Кнопки повороту навколо axis: u,v - ті самі дві осі в тому ж циклічному
// порядку, в якому rotFromDeg() реально крутить точки (перевірено: "пов X"
// рухає Y у бік Z, "пов Y" рухає Z у бік X, "пов Z" рухає X у бік Y). Дивимось,
// у який бік на екрані (за/проти годинникової) рух від u до v - це і є
// напрямок ДОДАТНОГО повороту. Екран має вісь Y вниз, тому знак навпаки, ніж
// у звичній математичній площині (y вгору) - враховано у виборі '↻'/'↺' нижче.
function rotGlyphs(u, v, camRot) {
  const du = camDir(u, camRot), dv = camDir(v, camRot);
  if (!du) return ['−', '+'];
  const cross = du[0] * dv[1] - du[1] * dv[0];
  const plus = cross > 0 ? '↻' : '↺';       // ↻ ↺
  const minus = plus === '↻' ? '↺' : '↻';
  return [minus, plus];
}

// Плаваюча панель (axisPad) отримує не текстовий '↻'/'↺', а справжню
// перспективну еліпсу-кільце: коло обертання (в площині u,v) буквально
// проєктується цією ж камерою, тому лягає "плазом" (тонкою еліпсою), коли
// вісь повороту майже в площині екрана (нахил), і лишається повним колом,
// коли вісь дивиться майже вздовж променя камери (чистий обертання екрана) -
// саме це мав на увазі "иконки должны быть 3д". Суцільна дуга - ближня до
// камери половина кільця, пунктирна - дальня (та сама ідея, що й у
// гізмо-кільцях CAD-редакторів), стрілка - на найближчій до глядача точці,
// напрямок хвостика показує бік ЦІЄЇ конкретної кнопки (sign=+1 - у бік u->v,
// sign=-1 - назад).
function rotIconSVG(u, v, sign, camRot) {
  const du = camDir(u, camRot), dv = camDir(v, camRot);
  if (!du) return null;
  const N = 28, R = 13, CX = 18, CY = 18;
  const pts = [];
  for (let i = 0; i <= N; i++) {
    const th = i / N * 2 * Math.PI, c = Math.cos(th), s = Math.sin(th);
    pts.push([du[0]*c + dv[0]*s, du[1]*c + dv[1]*s, du[2]*c + dv[2]*s]);
  }
  const maxR = Math.max(1e-6, ...pts.map(p => Math.hypot(p[0], p[1])));
  const k = R / maxR;
  const scr = pts.map(p => [CX + p[0]*k, CY + p[1]*k, p[2]]);
  let solid = '', dashed = '';
  for (let i = 0; i < N; i++) {
    const a = scr[i], b = scr[i+1];
    const seg = `M${a[0].toFixed(1)},${a[1].toFixed(1)} L${b[0].toFixed(1)},${b[1].toFixed(1)} `;
    if (a[2] < 0 && b[2] < 0) solid += seg; else dashed += seg;
  }
  let fi = 0;
  for (let i = 1; i <= N; i++) if (scr[i][2] < scr[fi][2]) fi = i;
  const nb = scr[(fi + 1) % (N + 1)], pb = scr[(fi - 1 + N + 1) % (N + 1)];
  let tx = nb[0] - pb[0], ty = nb[1] - pb[1];
  const tl = Math.hypot(tx, ty) || 1; tx /= tl; ty /= tl;
  if (sign < 0) { tx = -tx; ty = -ty; }
  const apex = scr[fi];
  // Тільки стрілка-хвостик більша (реальний запит: лише жовті стрілочки,
  // решту іконки не чіпати) - 5/8/5.6 замість 3.5/5.5/3.8.
  // Форма-шеврон (спроба за скріншотом) виявилась гіршою за практикою -
  // повернуто на залиту трикутну голівку, лише зі збільшеним розміром.
  const tipx = apex[0] + tx * 5, tipy = apex[1] + ty * 5;
  const bx = apex[0] - tx * 8, by = apex[1] - ty * 8;
  const px = -ty, py = tx, wing = 5.6;
  const w1x = bx + px*wing, w1y = by + py*wing, w2x = bx - px*wing, w2y = by - py*wing;
  // Ближня половина кільця - яскрава й товста (currentColor, як текст кнопки),
  // дальня - тонший розріджений пунктир СВОГО, приглушеного кольору. 27x27 -
  // щось середнє між початковими 24 і пробними 30 (реальний звіт: 30 забагато).
  // Стрілка-хвостик - ОКРЕМИЙ, яскравий колір (не currentColor, як кільце) -
  // тим самим кольором, що й вона зливалася з кільцем на однаковому кольорі
  // (реальний звіт: "стрілочки всередині іконки зливаються із загальною
  // білою лінією").
  return `<svg viewBox="0 0 36 36" width="27" height="27">
    <path d="${dashed}" stroke="#5b6b85" stroke-width="1.6" stroke-linecap="round" stroke-dasharray="1,2.6" fill="none"/>
    <path d="${solid}" stroke="currentColor" stroke-width="2.7" stroke-linecap="round" fill="none"/>
    <path d="M${tipx.toFixed(1)},${tipy.toFixed(1)} L${w1x.toFixed(1)},${w1y.toFixed(1)} L${w2x.toFixed(1)},${w2y.toFixed(1)} Z" fill="#fbbf24"/>
  </svg>`;
}
// Наскільки вісь лежить У ПЛОЩИНІ екрана (0 - дивиться вздовж променя камери,
// 1 - строго в площині) - той самий поріг, що вирішує показувати стрілку чи
// -/+ в shiftGlyphs(). Тут ним же вирішуємо, чи показувати кнопки зсуву
// вздовж цієї осі на плаваючій панелі взагалі: якщо на екрані майже не
// видно руху, налаштовувати цю вісь із цього ракурсу все одно не варто.
function screenPlanar(axis, camRot) {
  const d = camDir(axis, camRot);
  if (!d) return 1;
  return Math.hypot(d[0], d[1]);
}

// ------------------------------------------------ режим "2 ракурси" (split)
// Друга панель (завжди камера "left") використовує ті самі функції малювання
// й вибору точки, що й перша (cv/ctx/camIndex/camZoom/camPanX/camPanY) - але
// не власні, а ТИМЧАСОВО підмінені на cv2/ctx2/pane2.*. Після виконання fn()
// підсумковий зум/зсув зберігається назад у pane2, а глобальний стан
// повертається до того, яким був "back"-панелі - інакше кожен виклик у
// pane2-контексті непомітно зіпсував би стан першої панелі.
function withPane2(fn) {
  const sCv = cv, sCtx = ctx, sIdx = camIndex, sZ = camZoom, sPX = camPanX, sPY = camPanY;
  cv = cv2; ctx = ctx2; camIndex = pane2.camIdx;
  camZoom = pane2.zoom; camPanX = pane2.panX; camPanY = pane2.panY;
  try { return fn(); }
  finally {
    pane2.zoom = camZoom; pane2.panX = camPanX; pane2.panY = camPanY;
    cv = sCv; ctx = sCtx; camIndex = sIdx; camZoom = sZ; camPanX = sPX; camPanY = sPY;
  }
}

function findCamIdx(name) {
  return scene ? scene.cameras.findIndex(c => c.name === name) : -1;
}

// Увімкнути/вимкнути режим "2 ракурси". Обидві камери фіксовані (back/left) -
// вільного огляду в цьому режимі нема, але кнопки "Ракурс" (Загальний/back/
// left/top) лишаються видимими й клікабельними - клік по будь-якій одразу
// виходить із split (див. їхні onclick вище/нижче).
function setSplitMode(on) {
  if (on === splitMode) return;
  if (on) {
    const backIdx = findCamIdx('back'), leftIdx = findCamIdx('left');
    if (backIdx < 0 || leftIdx < 0) return;      // немає обох камер у сцені - нема сенсу
    preSplit = { camIndex, camZoom, camPanX, camPanY };
    camIndex = backIdx; camZoom = 1; camPanX = 0; camPanY = 0;
    pane2.camIdx = leftIdx; pane2.zoom = 1; pane2.panX = 0; pane2.panY = 0;
    activePane = 'back';
    splitMode = true;
  } else {
    splitMode = false;
    if (preSplit) ({ camIndex, camZoom, camPanX, camPanY } = preSplit);
  }
  if (!splitMode) setAutoPoseMode(false);   // авто-доведення лише в split - вимкнути й прибрати клацання
  document.getElementById('splitToggle').classList.toggle('on', splitMode);
  document.getElementById('autoPoseToggle').hidden = !splitMode;
  document.getElementById('paneLeftWrap').hidden = !splitMode;
  document.getElementById('paneBackLabel').hidden = !splitMode;
  // camIndex у split-режимі технічно дорівнює камері "back" (щоб уся наявна
  // логіка малювання/вибору точки працювала для першої панелі без змін), але
  // візуально це не "обрано одноракурсний back" - тому в split жодна з кнопок
  // Загальний/back/left/top підсвічуватись не повинна (реальний звіт: плутало).
  [...document.getElementById('cams').children].forEach((x, j) => x.classList.toggle('on', !splitMode && j === camIndex));
  document.getElementById('reset').classList.toggle('on', !splitMode && camIndex < 0);
  document.getElementById('photoAdjust').hidden = camIndex < 0 || splitMode;
  buildGroupEditor(); buildPointEditor();
  draw();
}

// ------------------------------------------------ ЕКСПЕРИМЕНТ: авто-доведення
// ФІКСОВАНІ орієнтири (за індексом уздовж ВИДИМОЇ - near-side - дуги цієї
// камери, не всі 97 точок), а не "клікни біля існуючої точки": якщо лінія
// реально сильно з'їхала, "туди, куди насправді треба" може бути далі, ніж
// поріг пошуку найближчої точки - клік просто мовчки нічого не знаходив
// (реальний звіт: "точки поставити не виходить"). Тепер послідовність
// наперед визначена (3 на кожен ракурс), клік будь-де на фото просто
// призначається НАСТУПНІЙ точці в черзі - відстань кліку від її поточного
// (можливо, хибного) положення й Є сигналом правки, а не перешкодою.
const autoPoseQueue = { back: [], left: [] };

function autoPoseTargets(camIdx) {
  const ci = activeCurveIndex();
  if (ci < 0 || camIdx < 0) return [];
  const c = scene.curves[ci];
  const savedIdx = camIndex; camIndex = camIdx;
  const near = nearSideMask(c, projector());
  camIndex = savedIdx;
  const idxs = near.map((v, i) => v ? i : -1).filter(i => i >= 0);
  if (!idxs.length) return [];
  return [0.15, 0.5, 0.85].map(f => idxs[Math.min(idxs.length - 1, Math.floor(f * idxs.length))]);
}

function setAutoPoseMode(on) {
  autoPoseMode = on;
  autoPoseCorr.length = 0;
  autoPoseQueue.back = on ? autoPoseTargets(findCamIdx('back')) : [];
  autoPoseQueue.left = on ? autoPoseTargets(findCamIdx('left')) : [];
  document.getElementById('autoPoseToggle').classList.toggle('on', on);
  document.getElementById('autoPosePanel').hidden = !on;
  refreshAutoPosePanel();
  draw();
}
document.getElementById('autoPoseToggle').onclick = () => setAutoPoseMode(!autoPoseMode);
document.getElementById('autoPoseCancel').onclick = () => setAutoPoseMode(false);
document.getElementById('autoPoseUndo').onclick = () => {
  const item = autoPoseCorr.pop();
  if (item) autoPoseQueue[item.view].unshift(item.idx);
  refreshAutoPosePanel(); draw();
};

function refreshAutoPosePanel() {
  const msg = document.getElementById('autoPoseMsg');
  const back = autoPoseCorr.filter(c => c.view === 'back').length;
  const left = autoPoseCorr.filter(c => c.view === 'left').length;
  const done = !autoPoseQueue.back.length && !autoPoseQueue.left.length;
  msg.textContent = done
    ? `клацнуто back:${back}/3 left:${left}/3 - можна розв'язувати`
    : `клацни жовті кружечки по черзі - back:${back}/3 left:${left}/3`;
  document.getElementById('autoPoseSolve').disabled = !done;
}

// Клік у режимі авто-доведення: НЕ вибирає точку для правки (як звичайний
// клік) і НЕ шукає найближчу точку - призначається НАСТУПНОМУ орієнтиру в
// черзі цього ракурсу (autoPoseQueue), байдуже, наскільки далеко клікнули
// від його поточного (можливо, хибного) положення на фото.
function recordAutoPoseClick(e) {
  if (!scene || camIndex < 0) return;
  const view = scene.cameras[camIndex].name;
  const queue = autoPoseQueue[view];
  if (!queue || !queue.length) return;
  const idx = queue.shift();
  const rect = cv.getBoundingClientRect();
  const mx = (e.clientX - rect.left) * devicePixelRatio;
  const my = (e.clientY - rect.top) * devicePixelRatio;
  const f = projector().fit;
  autoPoseCorr.push({ view, idx, img: [(mx - f.ox) / f.k, (my - f.oy) / f.k] });
}

// Застосовує totals (rot/t/scale), що прийшли з сервера, ТІЄЮ Ж математикою
// (rotFromDeg навколо центроїда поточної лінії), що й ручні кнопки групової
// панелі - тому "Скасувати"/"Зберегти" в group-редакторі далі працюють як і
// раніше, ніби це були звичайні натискання кнопок.
function applyAutoPoseTotals(ci, totals) {
  const c = scene.curves[ci];
  const cen = c.points.reduce((a, p) => [0,1,2].map(k => a[k] + p[k]), [0,0,0])
    .map(v => v / c.points.length);
  const R = rotFromDeg(totals.rot);
  for (let i = 0; i < c.points.length; i++) {
    const p = c.points[i];
    const rel = [0,1,2].map(k => p[k] - cen[k]);
    const rot = [0,1,2].map(k => R[k][0]*rel[0] + R[k][1]*rel[1] + R[k][2]*rel[2]);
    c.points[i] = [0,1,2].map(k => cen[k] + rot[k] + totals.t[k]);
  }
}

document.getElementById('autoPoseSolve').onclick = async () => {
  const ci = activeCurveIndex();
  if (ci < 0 || !sceneName) return;
  const btn = document.getElementById('autoPoseSolve');
  btn.disabled = true; btn.textContent = 'рахую...';
  try {
    const r = await fetch(`/api/scene/${sceneName}/curve/${ci}/auto_pose`,
      { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ corr: autoPoseCorr }) });
    const j = await r.json();
    if (!r.ok) { document.getElementById('autoPoseMsg').textContent = 'помилка: ' + (j.error || r.status); return; }
    applyAutoPoseTotals(ci, j.totals);
    setAutoPoseMode(false);
    buildGroupEditor();   // totals групової панелі рахуються "з початку правки" - скинути на 0, як і мало б
    draw();
  } finally {
    btn.disabled = false; btn.textContent = "Розв'язати і застосувати";
  }
};

// Свободная камера: смотрит на target, ось Y кадра вниз - как у настоящих.
function orbitPose() {
  const cp = Math.cos(view.pitch), sp = Math.sin(view.pitch);
  const cy = Math.cos(view.yaw), sy = Math.sin(view.yaw);
  const dir = [cp * cy, cp * sy, sp];                 // от цели к камере
  const C = [view.target[0] + view.dist * dir[0],
             view.target[1] + view.dist * dir[1],
             view.target[2] + view.dist * dir[2]];
  let f = [-dir[0], -dir[1], -dir[2]];                // вперёд
  let up = [0, 0, -1];
  let right = [f[1] * up[2] - f[2] * up[1], f[2] * up[0] - f[0] * up[2],
               f[0] * up[1] - f[1] * up[0]];
  let n = Math.hypot(...right); right = right.map(v => v / n);
  up = [f[1] * right[2] - f[2] * right[1], f[2] * right[0] - f[0] * right[2],
        f[0] * right[1] - f[1] * right[0]];
  return { R: [right[0], right[1], right[2], up[0], up[1], up[2], f[0], f[1], f[2]], C };
}

// Текущая проекция: мир -> пиксели холста. Возвращает и глубину.
function projector() {
  const W = cv.width, H = cv.height;
  if (camIndex >= 0) {
    const cam = scene.cameras[camIndex];
    const R = rodrigues(cam.rotation), C = cam.position;
    const [iw, ih] = cam.size;
    const k = Math.min(W / iw, H / ih) * camZoom;     // кадр в холст + ручной зум
    const ox = (W - iw * k) / 2 + camPanX, oy = (H - ih * k) / 2 + camPanY;
    return { fit: { k, ox, oy, iw, ih },
      p: (X) => { const v = mulv(R, sub(X, C));
        return [ox + k * (cam.focal_px * v[0] / v[2] + iw / 2),
                oy + k * (cam.focal_px * v[1] / v[2] + ih / 2), v[2]]; } };
  }
  const { R, C } = orbitPose();
  const f = (H / 2) / Math.tan(view.fov * Math.PI / 360);
  return { fit: null,
    p: (X) => { const v = mulv(R, sub(X, C));
      return [W / 2 + f * v[0] / v[2], H / 2 + f * v[1] / v[2], v[2]]; } };
}

// Отрезок, уходящий за камеру, рисовать нельзя - его проекция улетает в бесконечность.
function clipSeg(a, b, pr) {
  const NEAR = 1;
  let A = pr.p(a), B = pr.p(b);
  if (A[2] > NEAR && B[2] > NEAR) return [A, B];
  if (A[2] <= NEAR && B[2] <= NEAR) return null;
  const [in_, out] = A[2] > NEAR ? [a, b] : [b, a];
  const zi = pr.p(in_)[2], zo = pr.p(out)[2];
  const t = (zi - NEAR) / (zi - zo);
  const m = [in_[0] + (out[0] - in_[0]) * t, in_[1] + (out[1] - in_[1]) * t,
             in_[2] + (out[2] - in_[2]) * t];
  return A[2] > NEAR ? [A, pr.p(m)] : [pr.p(m), B];
}

// Ближняя к камере половина кольца - те точки, которые реально видно на фото,
// не закрыты куполом. В свободном обзоре (camIndex<0) считаем всё видимым.
// Та же идея, что в python (exp_camera_fit.near_arc): глубина ниже медианной.
function nearSideMask(c, pr) {
  if (camIndex < 0) return c.points.map(() => true);
  const zs = c.points.map(q => pr.p(q)[2]);
  const sorted = zs.slice().sort((a, b) => a - b);
  const med = sorted[Math.floor(sorted.length / 2)];
  return zs.map(z => z < med);
}

function polyline(pts, closed, pr) {
  ctx.beginPath();
  const n = pts.length;
  for (let i = 0; i + 1 < n + (closed ? 1 : 0); i++) {
    const s = clipSeg(pts[i], pts[(i + 1) % n], pr);
    if (!s) continue;
    ctx.moveTo(s[0][0], s[0][1]);
    ctx.lineTo(s[1][0], s[1][1]);
  }
  ctx.stroke();
}

// ---------------------------------------------------------------- рисование
function drawGrid(pr) {
  const z = scene._gridZ, c = scene._center;
  const step = 100, n = 12;
  ctx.strokeStyle = '#1c2432'; ctx.lineWidth = 1;
  const x0 = Math.round(c[0] / step) * step, y0 = Math.round(c[1] / step) * step;
  for (let i = -n; i <= n; i++) {
    polyline([[x0 + i * step, y0 - n * step, z], [x0 + i * step, y0 + n * step, z]], false, pr);
    polyline([[x0 - n * step, y0 + i * step, z], [x0 + n * step, y0 + i * step, z]], false, pr);
  }
}

function drawAxes(pr) {
  const L = 300;
  const ax = [[[L, 0, 0], '#ef4444', 'X'], [[0, L, 0], '#22c55e', 'Y'],
              [[0, 0, L], '#3b82f6', 'Z']];
  ctx.lineWidth = 2;
  for (const [v, col, name] of ax) {
    ctx.strokeStyle = col; polyline([[0, 0, 0], v], false, pr);
    const p = pr.p(v);
    if (p[2] > 1) { ctx.fillStyle = col; ctx.fillText(name, p[0] + 4, p[1]); }
  }
  const o = pr.p([0, 0, 0]);
  if (o[2] > 1) { ctx.fillStyle = '#94a3b8'; ctx.fillText('0 верстата', o[0] + 6, o[1] + 14); }
}

function drawCamera(cam, i, pr) {
  const R = rodrigues(cam.rotation), C = cam.position;
  const [iw, ih] = cam.size, d = 260;                 // длина пирамидки, мм
  const corner = (sx, sy) => {
    const v = [sx * iw / 2 / cam.focal_px * d, sy * ih / 2 / cam.focal_px * d, d];
    const w = trmulv(R, v);
    return [C[0] + w[0], C[1] + w[1], C[2] + w[2]];
  };
  const c4 = [corner(-1, -1), corner(1, -1), corner(1, 1), corner(-1, 1)];
  ctx.strokeStyle = i === camIndex ? '#f59e0b' : '#38bdf8';
  ctx.lineWidth = i === camIndex ? 2 : 1.4;
  polyline(c4, true, pr);
  for (const q of c4) polyline([C, q], false, pr);
  const p = pr.p(C);
  if (p[2] > 1) {
    ctx.fillStyle = ctx.strokeStyle;
    ctx.beginPath(); ctx.arc(p[0], p[1], 4, 0, 7); ctx.fill();
    ctx.fillText(cam.name, p[0] + 8, p[1] - 6);
  }
}

// Направление, в котором ИДЁТ свет. Верх в координатах станка это -Z, значит
// свет сверху обязан идти в +Z. С отрицательным Z он светил снизу, и купол
// выглядел вывернутым - на это и указал заказчик.
const LIGHT = (() => { const v = [-0.4, -0.5, 0.75];
  const n = Math.hypot(...v); return v.map(x => x / n); })();

function drawMesh(m, pr) {
  const data = meshes[m.name];
  if (!data) return;
  const T = m.transform, tris = data.tris;
  const camPos = camIndex >= 0 ? scene.cameras[camIndex].position : orbitPose().C;
  const out = [];
  for (let i = 0; i < tris.length; i += 9) {
    const P = [], W = [];
    let ok = true, zs = 0;
    for (let k = 0; k < 3; k++) {
      const x = tris[i + k * 3], y = tris[i + k * 3 + 1], z = tris[i + k * 3 + 2];
      const w = [T[0][0] * x + T[0][1] * y + T[0][2] * z + T[0][3],
                 T[1][0] * x + T[1][1] * y + T[1][2] * z + T[1][3],
                 T[2][0] * x + T[2][1] * y + T[2][2] * z + T[2][3]];
      const p = pr.p(w);
      if (p[2] <= 1) { ok = false; break; }
      W.push(w); P.push(p); zs += p[2];
    }
    if (!ok) continue;
    // Нормаль грани. Отвернувшиеся от нас грани не рисуем: у замкнутого меша
    // они всё равно закрыты, а рисовать их поверх лицевых - главный источник
    // «рваной» картинки на косых углах, потому что порядок по средней глубине
    // для длинных треугольников врёт.
    const u = [W[1][0]-W[0][0], W[1][1]-W[0][1], W[1][2]-W[0][2]];
    const v = [W[2][0]-W[0][0], W[2][1]-W[0][1], W[2][2]-W[0][2]];
    let N = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]];
    const nl = Math.hypot(...N) || 1; N = N.map(x => x / nl);
    const toCam = [camPos[0]-W[0][0], camPos[1]-W[0][1], camPos[2]-W[0][2]];
    let facing = N[0]*toCam[0] + N[1]*toCam[1] + N[2]*toCam[2];
    if (facing < 0) { N = N.map(x => -x); facing = -facing; }
    if (m.cull !== false && facing <= 0) continue;
    const lam = Math.max(0, -(N[0]*LIGHT[0] + N[1]*LIGHT[1] + N[2]*LIGHT[2]));
    // еле заметный разброс по граням: вблизи читается как фактура ткани
    const jitter = 0.97 + 0.06 * (((i * 2654435761) >>> 8) & 255) / 255;
    out.push([zs / 3, P, Math.min(1, (0.34 + 0.66 * lam) * jitter)]);
  }
  out.sort((a, b) => b[0] - a[0]);
  const [r, g, b] = m._rgb || [214, 190, 74];
  ctx.globalAlpha = m.opacity;
  for (const [, P, sh] of out) {
    ctx.fillStyle = `rgb(${r*sh|0},${g*sh|0},${b*sh|0})`;
    ctx.beginPath();
    ctx.moveTo(P[0][0], P[0][1]); ctx.lineTo(P[1][0], P[1][1]);
    ctx.lineTo(P[2][0], P[2][1]); ctx.closePath(); ctx.fill();
  }
  ctx.globalAlpha = 1;
}

// draw() - точка входу: в одноракурсному режимі просто малює #c (як і
// раніше), в split-режимі малює ОБИДВІ панелі (drawSingle викликається двічі,
// вдруге - через withPane2, щоб код усередині нічого не знав про друге вікно)
// і після цього оновлює спільну плаваючу панель під активну панель.
function draw() {
  if (splitMode) { drawSplitPanes(); return; }
  drawSingle(true);
}
function drawSplitPanes() {
  drawSingle(false);
  withPane2(() => drawSingle(false));
  refreshSharedPanels();
}
// tplPad/axisPad/point - спільні на весь #view, тому в split-режимі
// перебудовуються ОДИН раз (не з кожної панелі), під камеру activePane.
function refreshSharedPanels() {
  if (!splitMode) { buildTplPad(); updatePadSaveButtons(); return; }
  const idx = activePane === 'left' ? pane2.camIdx : camIndex;
  const camRot = (scene && idx >= 0) ? scene.cameras[idx].rotation : null;
  buildTplPad(camRot);
  buildAxisPad(camRot);
  buildPointEditor(camRot);
  updatePadSaveButtons();
  document.getElementById('paneBackLabel').classList.toggle('active', activePane === 'back');
  document.getElementById('paneLeftLabel').classList.toggle('active', activePane === 'left');
}

function drawSingle(updatePanels = true) {
  // Если вкладка ещё не разложена по местам, clientWidth равен нулю, холст
  // получает нулевой размер и остаётся пустым навсегда - первый вызов приходит
  // раньше вёрстки. Ждём следующего кадра.
  if (!cv.clientWidth || !cv.clientHeight) { requestAnimationFrame(draw); return; }
  const W = cv.width = cv.clientWidth * devicePixelRatio;
  const H = cv.height = cv.clientHeight * devicePixelRatio;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = '#0b0f16'; ctx.fillRect(0, 0, W, H);
  if (!scene) return;
  ctx.font = `${12 * devicePixelRatio}px sans-serif`;
  const pr = projector();
  if (updatePanels) buildTplPad();

  // фотография под режимом "взгляд камерой"
  if (camIndex >= 0 && document.getElementById('photo').checked) {
    const cam = scene.cameras[camIndex], im = photos[cam.name];
    if (im && im.complete && im.naturalWidth) {
      const f = pr.fit;
      ctx.globalAlpha = 0.75;
      if (photoBrightness !== 100 || photoContrast !== 100) {
        ctx.filter = `brightness(${photoBrightness}%) contrast(${photoContrast}%)`;
      }
      ctx.drawImage(im, f.ox, f.oy, f.iw * f.k, f.ih * f.k);
      ctx.filter = 'none';
      ctx.globalAlpha = 1;
    }
  }
  // Ручна розмітка лінії згину - тільки під тим самим видом камерою, звідки
  // її малювали (пікселі фото, не 3D-точки; безглуздо показувати їх деінде).
  if (camIndex >= 0) {
    const camName = scene.cameras[camIndex].name;
    const pts = markLines[camName];
    if (pts && pts.length >= 2 && shown['markline:' + camName]) {
      const f = pr.fit;
      const toScreen = ([x, y]) => [f.ox + f.k * x, f.oy + f.k * y];
      // НЕ #ef4444 - тим самим кольором позначені touched-точки лінії реза,
      // разом на фото ззаду/збоку вони зливалися в одну пляму (звіт користувача).
      ctx.strokeStyle = '#f472b6'; ctx.lineWidth = 2 * devicePixelRatio * 0.8;
      ctx.beginPath();
      [...pts].sort((a, b) => a[0] - b[0]).forEach(([x, y], i) => {
        const [sx, sy] = toScreen([x, y]);
        i ? ctx.lineTo(sx, sy) : ctx.moveTo(sx, sy);
      });
      ctx.stroke();
      ctx.fillStyle = '#f472b6';
      for (const p of pts) {
        const [sx, sy] = toScreen(p);
        ctx.beginPath(); ctx.arc(sx, sy, 3.5 * devicePixelRatio * 0.8, 0, 7); ctx.fill();
      }
    }
  }
  // ЕКСПЕРИМЕНТ (авто-доведення) - хрестики там, куди вже клацнули на ЦЬОМУ
  // ракурсі, щоб було видно, що вже зафіксовано, перш ніж тиснути "Розв'язати".
  // Темний контур під яскраво-лаймовим хрестиком - щоб було видно і на
  // темному тлі канви, і на світлому фото (сам блакитний #22d3ee губився на
  // фото - реальний звіт користувача).
  if (camIndex >= 0 && autoPoseMode) {
    const camName = scene.cameras[camIndex].name;
    const f = pr.fit;
    const r = 8 * devicePixelRatio * 0.8;
    for (const item of autoPoseCorr) {
      if (item.view !== camName) continue;
      const sx = f.ox + f.k * item.img[0], sy = f.oy + f.k * item.img[1];
      for (const [col, w] of [['#000', 4], ['#a3e635', 2]]) {
        ctx.strokeStyle = col; ctx.lineWidth = w * devicePixelRatio * 0.8;
        ctx.beginPath();
        ctx.moveTo(sx - r, sy); ctx.lineTo(sx + r, sy);
        ctx.moveTo(sx, sy - r); ctx.lineTo(sx, sy + r);
        ctx.stroke();
      }
    }
    // Жовті кружечки - НАСТУПНИЙ орієнтир у черзі цього ракурсу, на його
    // ПОТОЧНОМУ (можливо, хибному) положенні - лише орієнтир, куди приблизно
    // дивитись; сам клік можна ставити будь-де на фото, не обов'язково тут.
    const c = scene.curves[activeCurveIndex()];
    if (c) {
      autoPoseQueue[camName].forEach((idx, qi) => {
        const p = pr.p(c.points[idx]);
        if (p[2] <= 1) return;
        const rr = (qi === 0 ? 9 : 6) * devicePixelRatio * 0.8;
        ctx.strokeStyle = qi === 0 ? '#facc15' : '#a16207';
        ctx.lineWidth = 2.4 * devicePixelRatio * 0.8;
        ctx.beginPath(); ctx.arc(p[0], p[1], rr, 0, 7); ctx.stroke();
      });
    }
  }
  if (document.getElementById('grid').checked) drawGrid(pr);
  if (document.getElementById('axes').checked) drawAxes(pr);

  for (const m of scene.meshes || []) if (shown[m.name]) drawMesh(m, pr);
  // Собственная кромка модели. Хранится в её координатах, поэтому едет вместе с
  // ней при ручной установке - иначе сравнивать было бы не с чем.
  for (const m of scene.meshes || []) {
    if (!m.rim || !shown['rim:' + m.name]) continue;
    const T = m.transform;
    const pts = m.rim.map(v => [
      T[0][0]*v[0] + T[0][1]*v[1] + T[0][2]*v[2] + T[0][3],
      T[1][0]*v[0] + T[1][1]*v[1] + T[1][2]*v[2] + T[1][3],
      T[2][0]*v[0] + T[2][1]*v[1] + T[2][2]*v[2] + T[2][3]]);
    ctx.strokeStyle = '#f97316';
    ctx.lineWidth = 2.5 * devicePixelRatio * 0.8;
    polyline(pts, true, pr);
  }
  for (const c of scene.curves || []) {
    if (!shown[c.name]) continue;
    ctx.strokeStyle = c.color; ctx.lineWidth = (c.width || 2) * devicePixelRatio * 0.8;
    polyline(c.points, c.closed, pr);
  }
  // Шаблонна лінія (проба) - замкнений контур rim+off у світових координатах,
  // рухомий вручну (панель зверху) виключно для очей: той самий контур одразу
  // під будь-яким ракурсом і у вільному огляді, без прив'язки до однієї камери.
  if (templatePts && shown['template']) {
    ctx.strokeStyle = '#eab308'; ctx.lineWidth = 2 * devicePixelRatio * 0.8;
    polyline(templatePts, true, pr);
  }
  // Путь сопла нашей (редактируемой) линии - НЕ хранится, считается на лету из
  // текущих точек + их осей (сопло = рез + 10*ось), иначе после правки он бы
  // молча врал. Формула - см. ls_points.py, NOMINAL_STANDOFF.
  for (const c of scene.curves || []) {
    if (!c.editable || !c.axes || !shown['nozzle:' + c.name]) continue;
    const nozzle = c.points.map((p, i) => [0,1,2].map(k => p[k] + NOMINAL_STANDOFF * c.axes[i][k]));
    ctx.strokeStyle = '#93c5fd'; ctx.lineWidth = 1 * devicePixelRatio * 0.8;
    polyline(nozzle, c.closed, pr);
  }
  // Точки редактируемых кривых поверх линии - тронутые и выбранная отдельным
  // цветом, чтобы сразу было видно, где уже правили, а где ещё расчётное.
  // На дальней (самозакрытой куполом) стороне от текущей камеры точки гасим -
  // их не видно на этом фото, править вслепую по ним нельзя.
  scene.curves.forEach((c, ci) => {
    if (!c.editable || !shown[c.name]) return;
    const near = nearSideMask(c, pr);
    c.points.forEach((q, pi) => {
      const p = pr.p(q);
      if (p[2] <= 1) return;
      const sel = sel_point && sel_point.cidx === ci && sel_point.pidx === pi;
      const inGroup = group_sel.some(g => g.cidx === ci && g.pidx === pi);
      const touched = c.touched && c.touched[pi];
      const far = camIndex >= 0 && !near[pi];
      if (inGroup) {
        ctx.fillStyle = '#22d3ee';
        ctx.beginPath(); ctx.arc(p[0], p[1], 5.5 * devicePixelRatio * 0.8, 0, 7); ctx.fill();
        ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.2; ctx.stroke();
        return;
      }
      if (far && !sel) {
        ctx.fillStyle = '#3a4252';
        const r = 2.5 * devicePixelRatio * 0.8;
        ctx.beginPath(); ctx.arc(p[0], p[1], r, 0, 7); ctx.fill();
        return;
      }
      // Приглушений відтінок навмисно (не яскраво-червоний #ef4444) - той
      // самий колір тепер займає рядна розмітка від руки (нижче), і на
      // фото ззаду/збоку вони раніше зливалися в одну пляму.
      ctx.fillStyle = sel ? '#facc15' : (touched ? '#dc2626' : '#94a3b8');
      const r = (sel ? 6 : (touched ? 4 : 3.5)) * devicePixelRatio * 0.8;
      ctx.beginPath(); ctx.arc(p[0], p[1], r, 0, 7); ctx.fill();
      if (sel) { ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.stroke(); }
    });
  });
  for (const s of scene.points || []) {
    if (!shown[s.name]) continue;
    ctx.fillStyle = s.color;
    for (const q of s.points) {
      const p = pr.p(q);
      if (p[2] <= 1) continue;
      ctx.beginPath(); ctx.arc(p[0], p[1], (s.size || 4) * devicePixelRatio * 0.7, 0, 7);
      ctx.fill();
    }
  }
  scene.cameras.forEach((cam, i) => { if (shown['cam:' + cam.name]) drawCamera(cam, i, pr); });

  // "вільний огляд"/назва камери/фокус/frame прибрані - усе це вже видно з
  // підсвічених кнопок у "Ракурс", окремий текст в кутку робочої зони був
  // зайвим (звіт користувача). HUD тепер показує лише "проти еталона",
  // коли є з чим порівнювати - і нічого, коли нема.
  if (!updatePanels) return;
  let hud = '';
  const rs = refStats();
  if (rs) hud += (hud ? '\n\n' : '') + `проти еталона:\nсереднє ${rs.mean.toFixed(2)} мм, макс ${rs.max.toFixed(2)} мм\nв допуску 2мм: ${rs.pct.toFixed(0)}%`;
  HUD.textContent = hud;
  updatePadSaveButtons();
}

// Расхождение редактируемой линии с эталонной кривой (если есть) - ближайшая
// точка эталона к каждой точке нашей линии, не по id (шаблоны разные).
function refStats() {
  if (!scene) return null;
  const edit = scene.curves.find(c => c.editable);
  const ref = scene.curves.find(c => !c.editable && c.name.startsWith('еталон'));
  if (!edit || !ref || !ref.points.length) return null;
  const ds = edit.points.map(q => {
    let best = Infinity;
    for (const r of ref.points) {
      const dd = Math.hypot(q[0]-r[0], q[1]-r[1], q[2]-r[2]);
      if (dd < best) best = dd;
    }
    return best;
  });
  const mean = ds.reduce((a,b) => a+b, 0) / ds.length;
  const max = Math.max(...ds);
  const pct = 100 * ds.filter(d => d <= 2).length / ds.length;
  return { mean, max, pct };
}

// ---------------------------------------------------------------- управление
let drag = null;
cv.addEventListener('mousedown', e => {
  drag = { x: e.clientX, y: e.clientY, sh: e.shiftKey, x0: e.clientX, y0: e.clientY };
  if (splitMode) { activePane = 'back'; refreshSharedPanels(); }
});
addEventListener('mouseup', e => {
  // Клик почти без движения мыши - выбор точки, а не вращение обзора.
  if (drag && Math.hypot(e.clientX - drag.x0, e.clientY - drag.y0) < 4) {
    if (autoPoseMode) { recordAutoPoseClick(e); refreshAutoPosePanel(); draw(); }
    else trySelectPoint(e);
  }
  drag = null;
});

// Друга панель (left) у split-режимі - окремий drag/клік, бо перший canvas
// (cv/#c) вже займає власний mousedown/mouseup вище. Сама дія (панорама/вибір
// точки) - та сама логіка, просто виконана через withPane2 (cv/ctx/camIndex/
// camZoom/camPanX/camPanY на час виклику вказують на pane2/cv2).
let drag2 = null;
cv2.addEventListener('mousedown', e => {
  drag2 = { x: e.clientX, y: e.clientY, x0: e.clientX, y0: e.clientY };
  activePane = 'left'; refreshSharedPanels();
});
addEventListener('mouseup', e => {
  // НЕ trySelectPoint(e) напряму - вона сама викликає draw(), а той у
  // split-режимі перемальовує ОБИДВІ панелі; зробити це, поки ми ще
  // всередині withPane2 (тобто cv/camIndex підмінені на ліву панель), означає
  // рендерити "задню" панель туди ж, куди й ліву. Тому тут лишень підміняємо
  // на час пошуку точки під курсором, а draw() кличемо вже ПІСЛЯ, коли
  // withPane2 встиг повернути глобальний стан на місце.
  if (drag2 && Math.hypot(e.clientX - drag2.x0, e.clientY - drag2.y0) < 4) {
    activePane = 'left';
    if (autoPoseMode) { withPane2(() => recordAutoPoseClick(e)); refreshAutoPosePanel(); }
    else withPane2(() => { sel_point = findPointAt(e); });
    draw();
  }
  drag2 = null;
});
addEventListener('mousemove', e => {
  if (!drag2) return;
  const dx = e.clientX - drag2.x, dy = e.clientY - drag2.y;
  drag2.x = e.clientX; drag2.y = e.clientY;
  pane2.panX += dx; pane2.panY += dy;
  withPane2(() => drawSingle(false));
});
cv2.addEventListener('wheel', e => {
  e.preventDefault();
  activePane = 'left';
  withPane2(() => { zoomAtPoint(e); drawSingle(false); });
  refreshSharedPanels();
}, { passive: false });

function findPointAt(e) {
  const rect = cv.getBoundingClientRect();
  const mx = (e.clientX - rect.left) * devicePixelRatio;
  const my = (e.clientY - rect.top) * devicePixelRatio;
  const pr = projector();
  let best = null, bestD = 16 * devicePixelRatio;
  scene.curves.forEach((c, ci) => {
    if (!c.editable || !shown[c.name]) return;
    const near = nearSideMask(c, pr);
    c.points.forEach((q, pi) => {
      if (!near[pi]) return;               // не видно на этом фото - не выбираем
      const p = pr.p(q);
      if (p[2] <= 1) return;
      const d = Math.hypot(p[0] - mx, p[1] - my);
      if (d < bestD) { bestD = d; best = { cidx: ci, pidx: pi }; }
    });
  });
  return best;
}

// Клик - вибір однієї точки для тонкої правки. Раніше Shift+клік копичив
// точки в окрему групу для "комплексного зсуву" з вибором підмножини -
// прибрано разом з усією UI цього режиму (завжди діємо на всю лінію,
// group_sel лишається порожнім, activePoints() завжди повертає всю криву).
function trySelectPoint(e) {
  if (!scene) return;
  sel_point = findPointAt(e);
  buildPointEditor();
  draw();
}

function buildPointEditor(camRotOverride) {
  const box = document.getElementById('point');
  if (!sel_point) { box.hidden = true; return; }
  box.hidden = false;
  const c = scene.curves[sel_point.cidx], pi = sel_point.pidx;
  const id = c.ids ? c.ids[pi] : pi;
  const touched = c.touched && c.touched[pi];
  document.getElementById('ptitle').textContent =
    `#${id}${touched ? '' : ' (розрахункова)'}`;
  const ctl = document.getElementById('pointctl');
  ctl.innerHTML = '';
  const labels = ['X', 'Y', 'Z'];
  const axes3 = [[1,0,0], [0,1,0], [0,0,1]];
  // На фіксованому одноракурсному фото (back/left/top, НЕ вільний огляд і НЕ
  // split) вісь, що дивиться вздовж променя камери, рухається на екрані
  // непомітно - показувати для неї кнопки (хай навіть як звичайні -/+) лише
  // плутає (реальний звіт користувача). У split-режимі лишаємо всі три - там
  // разом обидва ракурси зазвичай перекривають будь-яку вісь.
  const hideInvisible = !splitMode && camIndex >= 0;
  for (let i = 0; i < 3; i++) {
    if (hideInvisible && screenPlanar(axes3[i], camRotOverride) < 0.35) continue;
    const row = document.createElement('div');
    row.className = 'prow';
    const [g1, g2] = shiftGlyphs(axes3[i], camRotOverride);
    row.innerHTML = `<b>${labels[i]}</b><button>${g1}</button><input><button>${g2}</button>`;
    const inp = row.querySelector('input');
    const sync = () => { inp.value = c.points[pi][i].toFixed(2); draw(); };
    row.children[1].onclick = () => { c.points[pi][i] -= step; sync(); };
    row.children[3].onclick = () => { c.points[pi][i] += step; sync(); };
    inp.onchange = () => { c.points[pi][i] = parseFloat(inp.value) || 0; sync(); };
    inp.value = c.points[pi][i].toFixed(2);
    ctl.appendChild(row);
  }
  document.getElementById('ptsave').onclick = async () => {
    const r = await fetch(`/api/scene/${sceneName}/curve/${sel_point.cidx}/point/${pi}`,
      { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ xyz: c.points[pi] }) });
    c.touched = c.touched || [];
    c.touched[pi] = true;
    if (c._saved) c._saved[pi] = c.points[pi].slice();
    document.getElementById('ptmsg').textContent = r.ok ? 'збережено в scene.json' : 'не збереглося';
    buildPointEditor(); draw();
  };
  document.getElementById('ptreset').onclick = async () => {
    const r = await fetch(`/api/scene/${sceneName}/curve/${sel_point.cidx}/point/${pi}/reset`,
      { method: 'POST' });
    if (r.ok) {
      c.points[pi] = c.points_original[pi].slice(); c.touched[pi] = false;
      if (c._saved) c._saved[pi] = c.points[pi].slice();
    }
    document.getElementById('ptmsg').textContent = r.ok ? 'повернено до розрахунку' : 'не збереглося';
    buildPointEditor(); draw();
  };
}
addEventListener('mousemove', e => {
  if (!drag) return;
  const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
  drag.x = e.clientX; drag.y = e.clientY;
  if (camIndex >= 0) {
    camPanX += dx; camPanY += dy; draw();
    return;
  }
  if (drag.sh || e.shiftKey) {
    const { R } = orbitPose(), s = view.dist * 0.0015;
    const right = trmulv(R, [1, 0, 0]), up = trmulv(R, [0, 1, 0]);
    for (let i = 0; i < 3; i++) view.target[i] -= right[i] * dx * s - up[i] * dy * s;
  } else {
    view.yaw -= dx * 0.006;
    view.pitch = Math.max(-1.5, Math.min(1.5, view.pitch + dy * 0.006));
  }
  draw();
});
// Зум коліщатком навколо точки під курсором (тримає ту саму точку кадра під
// мишею) - винесено окремою функцією, щоб друга панель (cv2, через withPane2)
// використовувала ЦЮ Ж математику, а не копію, яка могла б розійтися з нею.
function zoomAtPoint(e) {
  const rect = cv.getBoundingClientRect();
  const mx = (e.clientX - rect.left) * devicePixelRatio;
  const my = (e.clientY - rect.top) * devicePixelRatio;
  const cam = scene.cameras[camIndex];
  const [iw, ih] = cam.size;
  const W = cv.width, H = cv.height;
  const kBase = Math.min(W / iw, H / ih);
  const kBefore = kBase * camZoom;
  const oxBefore = (W - iw * kBefore) / 2 + camPanX;
  const oyBefore = (H - ih * kBefore) / 2 + camPanY;
  // точка кадра (в исходных, неотмасштабированных пикселях фото) под курсором
  const ux = (mx - oxBefore) / kBefore, uy = (my - oyBefore) / kBefore;
  camZoom *= Math.exp(-e.deltaY * 0.0012);
  camZoom = Math.max(0.2, Math.min(camZoom, 20));
  const kAfter = kBase * camZoom;
  // сдвигаем pan так, чтобы та же точка кадра снова оказалась под курсором
  camPanX = mx - kAfter * ux - (W - iw * kAfter) / 2;
  camPanY = my - kAfter * uy - (H - ih * kAfter) / 2;
}
cv.addEventListener('wheel', e => {
  e.preventDefault();
  if (camIndex >= 0) {
    if (splitMode) { activePane = 'back'; refreshSharedPanels(); }
    zoomAtPoint(e);
    draw();
    return;
  }
  view.dist *= Math.exp(e.deltaY * 0.0012);
  draw();
}, { passive: false });
addEventListener('resize', draw);

// ---------------------------------------------------------------- загрузка
function layerRow(name, color, key, defaultOn = true) {
  const l = document.createElement('label');
  l.innerHTML = `<input type="checkbox"${defaultOn ? ' checked' : ''}><span class="sw" style="background:${color}"></span>${name}`;
  l.querySelector('input').onchange = e => { shown[key] = e.target.checked; draw(); };
  shown[key] = defaultOn;
  return l;
}

async function loadScene(name) {
  setSplitMode(false);   // нова сцена - інші індекси камер, pane2.camIdx з попередньої більше не діє
  scene = await (await fetch('/api/scene/' + name)).json();
  sceneName = name;
  scene.curves = scene.curves || []; scene.points = scene.points || [];
  scene.meshes = scene.meshes || []; scene.cameras = scene.cameras || [];
  const splitBtn = document.getElementById('splitToggle');
  const hasBoth = findCamIdx('back') >= 0 && findCamIdx('left') >= 0;
  splitBtn.disabled = !hasBoth;
  splitBtn.title = hasBoth ? '' : 'потрібні обидві камери: back і left';

  const all = [];
  for (const c of scene.curves) all.push(...c.points);
  for (const s of scene.points) all.push(...s.points);
  if (!all.length) for (const c of scene.cameras) all.push(c.position);
  const mn = [Infinity, Infinity, Infinity], mx = [-Infinity, -Infinity, -Infinity];
  for (const p of all) for (let i = 0; i < 3; i++) {
    mn[i] = Math.min(mn[i], p[i]); mx[i] = Math.max(mx[i], p[i]);
  }
  scene._center = [0, 1, 2].map(i => (mn[i] + mx[i]) / 2);
  scene._gridZ = mn[2];
  view.target = scene._center.slice();
  view.dist = Math.max(600, 2.2 * Math.max(...[0, 1, 2].map(i => mx[i] - mn[i])));

  const layers = document.getElementById('layers'); layers.innerHTML = '';
  for (const c of scene.curves) {
    layers.appendChild(layerRow(c.name, c.color, c.name));
    if (c.editable && c.axes) layers.appendChild(layerRow('шлях сопла (живий)', '#93c5fd', 'nozzle:' + c.name, false));
  }
  for (const s of scene.points) layers.appendChild(layerRow(s.name, s.color, s.name));
  for (const m of scene.meshes) {
    layers.appendChild(layerRow(m.name, m.color, m.name));
    if (m.rim) layers.appendChild(layerRow('кромка моделі', '#f97316', 'rim:' + m.name));
  }
  for (const c of scene.cameras) layers.appendChild(layerRow('камера ' + c.name, '#38bdf8', 'cam:' + c.name));

  // Ручна розмітка лінії згину - лише для back/left (на top її не малюють) і
  // лише якщо камера з такою назвою є в цій сцені (без неї немає pr.fit,
  // яким малюються точки в пікселях фото).
  markLines.back = []; markLines.left = [];
  for (const view of ['back', 'left']) {
    if (!scene.cameras.some(c => c.name === view)) continue;
    fetch(`/api/mark/lines/${name}/${view}`).then(r => r.json()).then(d => {
      markLines[view] = d.points || [];
      if (markLines[view].length >= 2) {
        layers.appendChild(layerRow(`розмітка ${view} (від руки)`, '#f472b6', 'markline:' + view));
      }
      draw();
    }).catch(() => {});
  }

  // "Шаблонна лінія" - один замкнений 3D-контур на всю сцену одразу (не
  // прив'язаний до конкретної камери), тому підвантажується один раз.
  templateBase = null; templatePts = null;
  tplTotals.rot = [0, 0, 0]; tplTotals.t = [0, 0, 0]; tplTotals.scale = 100;
  layers.appendChild(layerRow('шаблонна лінія (CAD, проба)', '#eab308', 'template', false));
  fetch('/api/mark/template3d').then(r => r.json()).then(d => {
    if (d.points) { templateBase = d.points; templatePts = templateBase.map(p => p.slice()); }
    draw();
  }).catch(() => {});

  const cams = document.getElementById('cams'); cams.innerHTML = '';
  scene.cameras.forEach((cam, i) => {
    const b = document.createElement('button');
    b.textContent = cam.name;
    b.title = 'Погляд камерою ' + cam.name;
    b.style.width = 'auto'; b.style.flex = '1';
    b.onclick = () => {
      // Кнопки одноракурсного режиму лишаються видимими й у split-режимі
      // (щоб можна було в будь-яку мить переключитись назад однією камерою) -
      // клік по будь-якій з них спершу виходить із split, а вже тоді показує
      // саме ту камеру, яку натиснули.
      if (splitMode) setSplitMode(false);
      camIndex = camIndex === i ? -1 : i;
      camZoom = 1; camPanX = 0; camPanY = 0;
      [...cams.children].forEach((x, j) => x.classList.toggle('on', j === camIndex));
      document.getElementById('reset').classList.toggle('on', camIndex < 0);
      document.getElementById('photoAdjust').hidden = camIndex < 0;
      buildGroupEditor(); buildPointEditor();
      draw();
    };
    cams.appendChild(b);
    if (cam.image) {
      const im = new Image();
      im.onload = draw;
      im.src = `/asset/${name}/${cam.image}`;
      photos[cam.name] = im;
    }
  });
  [...cams.children].forEach((x, j) => x.classList.toggle('on', j === camIndex));
  document.getElementById('reset').classList.toggle('on', camIndex < 0);
  for (const m of scene.meshes) {
    const h = (m.color || '#d6be4a').replace('#', '');
    m._rgb = [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16));
    loadMesh(name, m);
  }
  buildPlacement();
  group_sel = []; sel_point = null;
  // Снимок "последнее сохранённое на диске" - для "Отменить" в групповой
  // правке. НЕ points_original (расчётное) - иначе отмена стёрла бы уже
  // сохранённые ранее правки, а не только текущий несохранённый сдвиг.
  for (const c of scene.curves) if (c.editable) c._saved = c.points.map(p => p.slice());
  checkCurveGaps();
  buildGroupEditor();
  draw();
}

// Без розмітки в слабо видимих на фото ділянках (типово - згин біля вух)
// підгонка пози буває локально неточною, і точки сусіда, "прилипаючи" до
// моделі, можуть скупчитися в одному місці замість того, щоб рівномірно йти
// по кільцю - решта відрізка тоді стискається в один різкий стрибок (виміряно
// наживо: до ~59мм при медіані ~9мм). Це не косметика - фінальний .LS
// поведе лазер по прямій навпростець замість форми в цьому місці. Тут лише
// ВИЯВЛЯЄМО такий стрибок і показуємо текстом (навмисно без підсвічування
// точок на 3D - той самий колір/спосіб вже зайнятий під "тронуті" точки,
// друге значення тим самим кольором лише плутало б). Не намагаємось
// автоматично виправити - розтягнути скупчені точки назад по дузі це окрема,
// значно ризикованіша задача.
function checkCurveGaps() {
  const warn = document.getElementById('curveWarn');
  const c = scene.curves.find(x => x.editable);
  if (!c || c.points.length < 4) { warn.hidden = true; return; }
  const n = c.points.length - (c.closed ? 0 : 1);
  const seg = [];
  for (let i = 0; i < n; i++) {
    const a = c.points[i], b = c.points[(i + 1) % c.points.length];
    seg.push(Math.hypot(a[0]-b[0], a[1]-b[1], a[2]-b[2]));
  }
  const sorted = seg.slice().sort((x, y) => x - y);
  const median = sorted[Math.floor(sorted.length / 2)] || 1;
  const bad = [];
  for (let i = 0; i < seg.length; i++) {
    if (seg[i] > Math.max(3 * median, 15)) bad.push({ i, len: seg[i] });
  }
  if (!bad.length) { warn.hidden = true; return; }
  const id = pi => (c.ids ? c.ids[pi] : pi);
  warn.hidden = false;
  warn.innerHTML = `⚠ Підозрілі стрибки на лінії реза (${bad.length}):<br>` + bad
    .map(b => `#${id(b.i)}→#${id((b.i + 1) % c.points.length)}: ${b.len.toFixed(0)}мм `
      + `(медіана ${median.toFixed(0)}мм) - розгляньте розмітку для цієї ділянки`)
    .join('<br>');
}

// Двоичный STL: 80 байт заголовка, 4 байта числа треугольников, дальше по 50.
async function loadMesh(name, m) {
  const buf = await (await fetch(`/asset/${name}/${m.url}`)).arrayBuffer();
  const dv = new DataView(buf);
  const n = dv.getUint32(80, true);
  if (84 + n * 50 !== buf.byteLength) { console.warn('не двоичный STL:', m.url); return; }
  const tris = new Float32Array(n * 9);
  for (let i = 0; i < n; i++) {
    const o = 84 + i * 50 + 12;
    for (let k = 0; k < 9; k++) tris[i * 9 + k] = dv.getFloat32(o + k * 4, true);
  }
  meshes[m.name] = { tris };
  draw();
}

// ------------------------------------------------- ручная установка модели
// Слепая подгонка по силуэтам садится в ложный оптимум: она с равным
// удовольствием кладёт шлем набок и вверх дном, лишь бы закрыть площадь.
// Человек ставит модель на линию реза за минуту, поэтому углы и сдвиги правятся
// руками, а подгонка потом уже только уточняет.
let step = 5, placeIdx = -1;

function placementMatrix(pl) {
  const [rx, ry, rz] = pl.rot_deg.map(a => a * Math.PI / 180);
  const cx = Math.cos(rx), sx = Math.sin(rx), cy = Math.cos(ry), sy = Math.sin(ry);
  const cz = Math.cos(rz), sz = Math.sin(rz), s = pl.scale;
  const R = [[cz*cy, cz*sy*sx - sz*cx, cz*sy*cx + sz*sx],
             [sz*cy, sz*sy*sx + cz*cx, sz*sy*cx - cz*sx],
             [-sy,   cy*sx,            cy*cx]];
  return [0,1,2].map(i => [R[i][0]*s, R[i][1]*s, R[i][2]*s, pl.translate[i]])
                .concat([[0, 0, 0, 1]]);
}

function buildPlacement() {
  const box = document.getElementById('place');
  if (!scene || !scene.meshes.length) { box.hidden = true; return; }
  box.hidden = false;
  placeIdx = 0;
  const m = scene.meshes[0];
  m.placement = m.placement || { rot_deg: [0, 0, 0], translate: [0, 0, 0], scale: 1 };
  m._start = JSON.parse(JSON.stringify(m.placement));
  const ctl = document.getElementById('pctl');
  ctl.innerHTML = '<div style="color:#7c8aa0;font-size:12px;margin-bottom:2px">'
                + 'крок на натискання: градуси / мм</div><div id="steps"></div>';
  const steps = ctl.querySelector('#steps');
  for (const v of [0.1, 1, 5, 20]) {
    const b = document.createElement('button');
    b.textContent = v; b.style.flex = '1';
    b.classList.toggle('on', v === step);
    b.onclick = () => { step = v; [...steps.children].forEach(x => x.classList.toggle('on', +x.textContent === step)); };
    steps.appendChild(b);
  }
  const rows = [['пов X', 'rot_deg', 0, '°'], ['пов Y', 'rot_deg', 1, '°'],
                ['пов Z', 'rot_deg', 2, '°'], ['зсв X', 'translate', 0, 'мм'],
                ['зсв Y', 'translate', 1, 'мм'], ['зсв Z', 'translate', 2, 'мм']];
  for (const [label, field, i] of rows) {
    const row = document.createElement('div');
    row.className = 'prow';
    row.innerHTML = `<b>${label}</b><button>−</button><input><button>+</button>`;
    const inp = row.querySelector('input');
    const sync = () => { inp.value = m.placement[field][i].toFixed(2); apply(); };
    row.children[1].onclick = () => { m.placement[field][i] -= step; sync(); };
    row.children[3].onclick = () => { m.placement[field][i] += step; sync(); };
    inp.onchange = () => { m.placement[field][i] = parseFloat(inp.value) || 0; sync(); };
    inp.value = m.placement[field][i].toFixed(2);
    ctl.appendChild(row);
  }
  const row = document.createElement('div');
  row.className = 'prow';
  row.innerHTML = '<b>масштаб</b><button>−</button><input><button>+</button>';
  const inp = row.querySelector('input');
  const sync = () => { inp.value = m.placement.scale.toFixed(3); apply(); };
  row.children[1].onclick = () => { m.placement.scale -= step / 100; sync(); };
  row.children[3].onclick = () => { m.placement.scale += step / 100; sync(); };
  inp.onchange = () => { m.placement.scale = parseFloat(inp.value) || 1; sync(); };
  inp.value = m.placement.scale.toFixed(3);
  ctl.appendChild(row);

  function apply() { m.transform = placementMatrix(m.placement); draw(); }

  document.getElementById('psave').onclick = async () => {
    const r = await fetch(`/api/scene/${sceneName}/mesh/${placeIdx}/placement`,
      { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(m.placement) });
    document.getElementById('pmsg').textContent =
      r.ok ? 'збережено в scene.json' : 'не збереглося';
  };
  document.getElementById('preset').onclick = () => {
    m.placement = JSON.parse(JSON.stringify(m._start));
    buildPlacement(); draw();
  };
}

// По умолчанию (group_sel пуст) область действия - ВСЯ редактируемая линия,
// не какое-то подмножество. Выбор (Shift+клик, "видимые здесь") сужает область,
// "Сбросить выбор" возвращает обратно к "вся линия" - это НЕ то же самое, что
// "ничего не выбрано".
function activeCurveIndex() {
  if (!scene) return -1;
  return scene.curves.findIndex(c => c.editable);
}
function activePoints() {
  const ci = activeCurveIndex();
  if (ci < 0) return [];
  if (group_sel.length) return group_sel.filter(g => g.cidx === ci);
  return scene.curves[ci].points.map((_, pi) => ({ cidx: ci, pidx: pi }));
}

// Плаваюча панель поверх 3D-вигляду - дублює кнопки +/- з groupctl (та сама
// логіка, ті самі totals), лише більшими іконками, підлаштованими під ракурс.
// Лишень для вигляду з камери - у вільному огляді осі верстата й так не
// прив'язані до жодного постійного напрямку на екрані (сама камера крутиться
// мишею), тому підказка була б безглуздою.
function buildAxisPad(camRotOverride) {
  const pad = document.getElementById('axisPad');
  const groupBox = document.getElementById('group');
  const haveCam = camRotOverride || camIndex >= 0;
  if (!haveCam || groupBox.hidden) { pad.hidden = true; return; }
  pad.hidden = false;
  const rows = [...document.getElementById('groupctl').querySelectorAll('.prow')];
  const findRow = label => rows.find(r => { const b = r.querySelector('b'); return b && b.textContent === label; });

  const shiftDefs = [['зсв X', [1,0,0]], ['зсв Y', [0,1,0]], ['зсв Z', [0,0,1]]];
  const rotDefs = [
    ['пов X', [0,1,0], [0,0,1]],
    ['пов Y', [0,0,1], [1,0,0]],
    ['пов Z', [1,0,0], [0,1,0]],
  ];

  // Вісь зсуву, вздовж якої з поточного ракурсу на екрані майже нічого не
  // рухається (дивиться вздовж променя камери) - тут не показуємо взагалі:
  // налаштовувати наосліп сенсу нема, а кнопки лише займали б місце. У
  // сайдбарі вона лишається (там завжди всі три, з тим самим -/+).
  const shiftRow = document.getElementById('padShift'); shiftRow.innerHTML = '';
  for (const [label, axis] of shiftDefs) {
    if (screenPlanar(axis, camRotOverride) < 0.35) continue;
    const row = findRow(label);
    if (!row) continue;
    // Стрілки рахуємо ЗАНОВО під camRotOverride (не з row.children[].textContent
    // сайдбарного рядка - той стрілки/значки має зафіксовані під АМБІЄНТНУ
    // camIndex, яка в split-режимі завжди дорівнює камері "back"; для панелі
    // "left" вони були б неправильні - реальний звіт користувача). Клік і далі
    // проксується у прихований рядок groupctl - сам рух точок не залежить від
    // того, під яким ракурсом підписані кнопки.
    const [g1, g2] = shiftGlyphs(axis, camRotOverride);
    const g = document.createElement('div'); g.className = 'padGroup';
    g.title = label;
    const bMinus = document.createElement('button'); bMinus.textContent = g1;
    bMinus.title = label + ' ' + g1;
    bMinus.onclick = () => row.children[1].click();
    const bPlus = document.createElement('button'); bPlus.textContent = g2;
    bPlus.title = label + ' ' + g2;
    bPlus.onclick = () => row.children[3].click();
    g.append(bMinus, bPlus);
    shiftRow.appendChild(g);
  }

  const rotRow = document.getElementById('padRotate'); rotRow.innerHTML = '';
  for (const [label, u, v] of rotDefs) {
    const row = findRow(label);
    if (!row) continue;
    const g = document.createElement('div'); g.className = 'padGroup';
    g.title = label;
    const bMinus = document.createElement('button'); bMinus.innerHTML = rotIconSVG(u, v, -1, camRotOverride) || row.children[1].textContent;
    bMinus.onclick = () => row.children[1].click();
    const bPlus = document.createElement('button'); bPlus.innerHTML = rotIconSVG(u, v, 1, camRotOverride) || row.children[3].textContent;
    bPlus.onclick = () => row.children[3].click();
    g.append(bMinus, bPlus);
    rotRow.appendChild(g);
  }

  // Масштаб - той самий проксі-прийом, що й зсув/поворот вище: клікаємо
  // справжні кнопки прихованого рядка "масштаб" у #groupctl, підсумок (%)
  // рахує і показує сам сайдбар, тут лишень великі кнопки під ракурс.
  const scaleRow = document.getElementById('padScale'); scaleRow.innerHTML = '';
  {
    const row = findRow('масштаб');
    if (row) {
      const g = document.createElement('div'); g.className = 'padGroup'; g.title = 'масштаб';
      const bMinus = document.createElement('button'); bMinus.textContent = row.children[1].textContent;
      bMinus.title = 'масштаб ' + row.children[1].textContent;
      bMinus.onclick = () => row.children[1].click();
      const bPlus = document.createElement('button'); bPlus.textContent = row.children[3].textContent;
      bPlus.title = 'масштаб ' + row.children[3].textContent;
      bPlus.onclick = () => row.children[3].click();
      g.append(bMinus, bPlus);
      scaleRow.appendChild(g);
    }
  }

  // Крок (0.1/1/5/10) - проксі на ті самі кнопки #gsteps у сайдбарі, щоб не
  // доводилось лізти в бокову панель заради зміни кроку під час роботи з
  // плаваючою панеллю. Реальний клік у сайдбарі сам оновлює лише СВОЇ класи
  // .on - тому після проксі-кліка підсвітку тут доводиться виставляти вручну.
  const stepBtns = [...document.querySelectorAll('#gsteps button')];
  const stepRow = document.getElementById('padStep'); stepRow.innerHTML = '';
  const stepGroup = document.createElement('div'); stepGroup.className = 'padGroup'; stepGroup.title = 'крок';
  const proxyBtns = stepBtns.map(sb => {
    const b = document.createElement('button');
    b.textContent = sb.textContent;
    b.classList.toggle('on', sb.classList.contains('on'));
    b.onclick = () => {
      sb.click();
      proxyBtns.forEach((x, j) => x.classList.toggle('on', stepBtns[j].classList.contains('on')));
    };
    stepGroup.appendChild(b);
    return b;
  });
  stepRow.appendChild(stepGroup);

  // Зберегти/скинути - той самий gsave/gundo, що й раніше в сайдбарі (тепер
  // прихований, лишень службовий стан). Кнопку "скинути" просто проксуємо
  // кліком, а "зберегти" - викликаємо напряму як функцію (а не .click()),
  // щоб дочекатись відповіді сервера (async) і на мить показати результат
  // прямо на кнопці - без окремого текстового повідомлення, яке нема кому
  // тут показувати.
  const saveRow = document.getElementById('padSave'); saveRow.innerHTML = '';
  const saveGroup = document.createElement('div'); saveGroup.className = 'padGroup';
  const bSave = document.createElement('button'); bSave.id = 'padSaveBtn'; bSave.textContent = 'Зберегти';
  bSave.onclick = async () => {
    bSave.disabled = true; bSave.classList.remove('dirty');
    const ok = await document.getElementById('gsave').onclick();
    bSave.textContent = ok ? '✓ Збережено' : '✗ Помилка';
    setTimeout(() => { bSave.textContent = 'Зберегти'; bSave.disabled = false; updatePadSaveButtons(); }, 1400);
  };
  const bUndo = document.createElement('button'); bUndo.id = 'padUndoBtn'; bUndo.textContent = 'Скинути';
  bUndo.onclick = () => { document.getElementById('gundo').click(); updatePadSaveButtons(); };
  saveGroup.append(bSave, bUndo);
  saveRow.appendChild(saveGroup);
  updatePadSaveButtons();
}

// Чи відрізняється поточна редагована крива від останнього збереженого на
// диск стану (c._saved) - і "Зберегти" підсвічуємо зеленим, і "Скинути"
// трохи активуємо, щоб не забували фіксувати правки перед вивантаженням .LS.
function isDirty(c) {
  if (!c || !c._saved) return false;
  for (let i = 0; i < c.points.length; i++) {
    const p = c.points[i], s = c._saved[i];
    if (Math.abs(p[0]-s[0]) > 1e-6 || Math.abs(p[1]-s[1]) > 1e-6 || Math.abs(p[2]-s[2]) > 1e-6) return true;
  }
  return false;
}
function updatePadSaveButtons() {
  const saveBtn = document.getElementById('padSaveBtn'), undoBtn = document.getElementById('padUndoBtn');
  if (!saveBtn) return;
  const ci = activeCurveIndex();
  const dirty = ci >= 0 && isDirty(scene.curves[ci]);
  if (!saveBtn.disabled) saveBtn.classList.toggle('dirty', dirty);
  undoBtn.classList.toggle('dirty', dirty);
}

function buildGroupEditor() {
  const box = document.getElementById('group');
  const ci = activeCurveIndex();
  if (ci < 0) { box.hidden = true; buildAxisPad(); return; }
  box.hidden = false;
  const pts = activePoints();
  const c = scene.curves[ci];

  // Применяется НЕМЕДЛЕННО к точкам и перерисовывает - как и одиночная точка,
  // а не копится в отдельной переменной до "Сохранить" (та версия визуально
  // не двигалась по кнопке, только по нажатию "Сохранить" - баг, отсюда жалоба
  // "смещение не работает с виду"). "Сохранить" лишь отправляет уже применённое
  // на сервер, "Отменить всё" возвращает точки группы к исходным.
  function currentCentroid() {
    return pts.reduce((a, g) => [0,1,2].map(i => a[i] + c.points[g.pidx][i]),
                      [0, 0, 0]).map(v => v / pts.length);
  }
  function translate(delta) {
    for (const g of pts) c.points[g.pidx] = [0,1,2].map(i => c.points[g.pidx][i] + delta[i]);
    draw();
  }
  function rotate(rotDeg) {
    const R = rotFromDeg(rotDeg), cen = currentCentroid();
    for (const g of pts) {
      const p = c.points[g.pidx];
      const rel = [0,1,2].map(i => p[i] - cen[i]);
      const rot = [0,1,2].map(i => R[i][0]*rel[0] + R[i][1]*rel[1] + R[i][2]*rel[2]);
      c.points[g.pidx] = [0,1,2].map(i => cen[i] + rot[i]);
    }
    draw();
  }
  // factor относительно ТЕКУЩЕГО состояния точек (не исходного) - см. вызов
  // ниже, где итоговый % пересчитывается в относительный множитель за шаг.
  function scaleBy(factor) {
    const cen = currentCentroid();
    for (const g of pts) {
      const p = c.points[g.pidx];
      c.points[g.pidx] = [0,1,2].map(i => cen[i] + (p[i] - cen[i]) * factor);
    }
    draw();
  }

  // Итог с начала этой правки (сбрасывается в 0 при Сохранить/Отменить/смене
  // выбора) - показывает "на сколько всего сдвинуто/повёрнуто СЕЙЧАС", не
  // абсолютную координату (для группы точек у неё и нет одного числа).
  const totals = { rot: [0, 0, 0], t: [0, 0, 0], scale: 100 };

  const ctl = document.getElementById('groupctl');
  ctl.innerHTML = '<div style="color:#7c8aa0;font-size:11px;margin-bottom:2px">'
                + 'крок на натискання: градуси / мм / %</div><div id="gsteps"></div>'
                + '<div style="color:#7c8aa0;font-size:11px;margin:6px 0 2px">'
                + 'підсумок з початку правки (можна вписати число):</div>';
  const stepsBox = ctl.querySelector('#gsteps');
  for (const v of [0.1, 1, 5, 10]) {
    const b = document.createElement('button');
    b.textContent = v; b.style.flex = '1';
    b.classList.toggle('on', v === step);
    b.onclick = () => { step = v; [...stepsBox.children].forEach(x => x.classList.toggle('on', +x.textContent === step)); };
    stepsBox.appendChild(b);
  }
  const rotRows = [
    ['пов X', [1,0,0], [0,1,0], [0,0,1]],
    ['пов Y', [0,1,0], [0,0,1], [1,0,0]],
    ['пов Z', [0,0,1], [1,0,0], [0,1,0]],
  ];
  for (const [label, axis, u, v, i] of rotRows.map((r, i) => [...r, i])) {
    const row = document.createElement('div');
    row.className = 'prow';
    const [g1, g2] = rotGlyphs(u, v);
    row.innerHTML = `<b>${label}</b><button>${g1}</button><input><button>${g2}</button>`;
    const inp = row.querySelector('input');
    const sync = () => { inp.value = totals.rot[i].toFixed(2); };
    const step_ = (sign) => { rotate(axis.map(a => a * sign * step)); totals.rot[i] += sign * step; sync(); };
    row.children[1].onclick = () => step_(-1);
    row.children[3].onclick = () => step_(1);
    inp.onchange = () => {
      const target = parseFloat(inp.value) || 0;
      rotate(axis.map(a => a * (target - totals.rot[i])));
      totals.rot[i] = target; sync();
    };
    sync();
    ctl.appendChild(row);
  }
  const tRows = [['зсв X', [1,0,0]], ['зсв Y', [0,1,0]], ['зсв Z', [0,0,1]]];
  for (const [label, axis, i] of tRows.map((r, i) => [...r, i])) {
    const row = document.createElement('div');
    row.className = 'prow';
    const [g1, g2] = shiftGlyphs(axis);
    row.innerHTML = `<b>${label}</b><button>${g1}</button><input><button>${g2}</button>`;
    const inp = row.querySelector('input');
    const sync = () => { inp.value = totals.t[i].toFixed(2); };
    const step_ = (sign) => { translate(axis.map(a => a * sign * step)); totals.t[i] += sign * step; sync(); };
    row.children[1].onclick = () => step_(-1);
    row.children[3].onclick = () => step_(1);
    inp.onchange = () => {
      const target = parseFloat(inp.value) || 0;
      translate(axis.map(a => a * (target - totals.t[i])));
      totals.t[i] = target; sync();
    };
    sync();
    ctl.appendChild(row);
  }
  {
    // Масштаб - относительно центроида активных точек, в % (100% = как сейчас
    // на момент открытия панели). Множитель мультипликативный, поэтому и
    // кнопка +, и ручной ввод пересчитывают ЦЕЛЕВОЙ % в относительный фактор
    // от totals.scale (а не аддитивно, как повороты/сдвиги).
    const row = document.createElement('div');
    row.className = 'prow';
    row.innerHTML = `<b>масштаб</b><button>−</button><input><button>+</button>`;
    const inp = row.querySelector('input');
    const sync = () => { inp.value = totals.scale.toFixed(2); };
    const scaleTo = (target) => {
      if (target <= 0) return;
      scaleBy(target / totals.scale);
      totals.scale = target; sync();
    };
    row.children[1].onclick = () => scaleTo(totals.scale - step);
    row.children[3].onclick = () => scaleTo(totals.scale + step);
    inp.onchange = () => scaleTo(parseFloat(inp.value) || totals.scale);
    sync();
    ctl.appendChild(row);
  }

  document.getElementById('gundo').onclick = () => {
    for (const g of pts) c.points[g.pidx] = (c._saved ? c._saved[g.pidx] : c.points_original[g.pidx]).slice();
    buildGroupEditor(); draw();
  };

  document.getElementById('gsave').onclick = async () => {
    const payload = pts.map(g => ({ pidx: g.pidx, xyz: c.points[g.pidx] }));
    const r = await fetch(`/api/scene/${sceneName}/curve/${ci}/points`,
      { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ points: payload }) });
    c.touched = c.touched || [];
    payload.forEach(p => { c.touched[p.pidx] = true; c._saved[p.pidx] = p.xyz.slice(); });
    document.getElementById('gmsg').textContent =
      r.ok ? `збережено, зсунуто ${payload.length}` : 'не збереглося';
    buildGroupEditor(); draw();
    return r.ok;
  };
  buildAxisPad();
}

// Матрица поворота Rz*Ry*Rx из градусов - та же формула, что placementMatrix,
// но без масштаба и переноса (те считаются отдельно, вокруг центроида группы).
function rotFromDeg(rotDeg) {
  const [rx, ry, rz] = rotDeg.map(a => a * Math.PI / 180);
  const cx = Math.cos(rx), sx = Math.sin(rx), cy = Math.cos(ry), sy = Math.sin(ry);
  const cz = Math.cos(rz), sz = Math.sin(rz);
  return [[cz*cy, cz*sy*sx - sz*cx, cz*sy*cx + sz*sx],
          [sz*cy, sz*sy*sx + cz*cx, sz*sy*cx - cz*sx],
          [-sy,   cy*sx,            cy*cx]];
}

document.getElementById('exportls').onclick = async () => {
  if (!sceneName) return;
  const msg = document.getElementById('exportmsg');
  msg.textContent = 'збираю...';
  const r = await fetch(`/api/scene/${sceneName}/export`, { method: 'POST' });
  const j = await r.json();
  if (!r.ok) { msg.textContent = 'помилка: ' + (j.error || r.status); return; }
  msg.innerHTML = `готово: <a href="/download/${sceneName}/${j.file}" target="_blank">${j.file}</a>` +
    ` (точок ${j.total}, торкнуто ${j.touched})`;
};

document.getElementById('splitToggle').onclick = () => setSplitMode(!splitMode);
document.getElementById('reset').onclick = () => {
  if (splitMode) setSplitMode(false);
  camIndex = -1;
  camZoom = 1; camPanX = 0; camPanY = 0;
  [...document.getElementById('cams').children].forEach(x => x.classList.remove('on'));
  document.getElementById('reset').classList.add('on');
  document.getElementById('photoAdjust').hidden = true;
  if (scene) { view.target = scene._center.slice(); view.yaw = 0.9; view.pitch = 0.5; }
  buildGroupEditor(); buildPointEditor();
  draw();
};
for (const id of ['grid', 'axes', 'photo'])
  document.getElementById(id).onchange = draw;
document.getElementById('oporyToggle').onclick = () => {
  document.getElementById('oporyPanel').hidden = !document.getElementById('oporyPanel').hidden;
};

// ------------------------------------------------- яскравість/контраст фото
function setPhotoAdjust(bright, contrast) {
  photoBrightness = bright; photoContrast = contrast;
  document.getElementById('pa_bright').value = bright;
  document.getElementById('pa_contrast').value = contrast;
  document.getElementById('pa_brightval').textContent = bright + '%';
  document.getElementById('pa_contrastval').textContent = contrast + '%';
  draw();
}
document.getElementById('pa_bright').oninput = e => setPhotoAdjust(+e.target.value, photoContrast);
document.getElementById('pa_contrast').oninput = e => setPhotoAdjust(photoBrightness, +e.target.value);
document.getElementById('pa_reset').onclick = () => setPhotoAdjust(100, 100);

// ------------------------------------------------- шаблонна лінія (проба)
// Той самий зсув/поворот/масштаб навколо центроїда, що й у buildGroupEditor
// для справжньої лінії різу (translate/rotate/scaleBy) - тут лише застосований
// до templatePts замість c.points, і крок tplStep НЕ ділить змінну "step" з
// реальною правкою (щоб одне не плуталось з іншим).
function templateCentroid() {
  return templatePts.reduce((a, p) => [0, 1, 2].map(k => a[k] + p[k]), [0, 0, 0])
    .map(v => v / templatePts.length);
}
function templateTranslate(delta) {
  for (let i = 0; i < templatePts.length; i++)
    templatePts[i] = [0, 1, 2].map(k => templatePts[i][k] + delta[k]);
}
function templateRotate(rotDeg) {
  const R = rotFromDeg(rotDeg), cen = templateCentroid();
  for (let i = 0; i < templatePts.length; i++) {
    const p = templatePts[i];
    const rel = [0, 1, 2].map(k => p[k] - cen[k]);
    const rot = [0, 1, 2].map(k => R[k][0] * rel[0] + R[k][1] * rel[1] + R[k][2] * rel[2]);
    templatePts[i] = [0, 1, 2].map(k => cen[k] + rot[k]);
  }
}
function templateScaleTo(target) {
  if (target <= 0) return;
  const factor = target / tplTotals.scale, cen = templateCentroid();
  for (let i = 0; i < templatePts.length; i++) {
    const p = templatePts[i];
    templatePts[i] = [0, 1, 2].map(k => cen[k] + (p[k] - cen[k]) * factor);
  }
  tplTotals.scale = target;
}
function templateReset() {
  templatePts = templateBase.map(p => p.slice());
  tplTotals.rot = [0, 0, 0]; tplTotals.t = [0, 0, 0]; tplTotals.scale = 100;
}

// Панель зверху - лише для ракурсу з камери (у вільному огляді осі верстата
// нічим не прив'язані до екрана, підказка була б безглуздою - та сама логіка,
// що й у buildAxisPad). Показує лише ті осі зсуву, які реально видно рухомими
// з поточного ракурсу (screenPlanar), поворот - всі три завжди.
function buildTplPad(camRotOverride) {
  const pad = document.getElementById('tplPad');
  const haveCam = camRotOverride || camIndex >= 0;
  if (!haveCam || !shown['template'] || !templatePts) { pad.hidden = true; return; }
  pad.hidden = false;

  const shiftRow = document.getElementById('tplShift'); shiftRow.innerHTML = '';
  const shiftDefs = [['зсв X', [1, 0, 0]], ['зсв Y', [0, 1, 0]], ['зсв Z', [0, 0, 1]]];
  shiftDefs.forEach(([label, axis], i) => {
    if (screenPlanar(axis, camRotOverride) < 0.35) return;
    const [g1, g2] = shiftGlyphs(axis, camRotOverride);
    const g = document.createElement('div'); g.className = 'padGroup'; g.title = label;
    const bMinus = document.createElement('button'); bMinus.textContent = g1;
    bMinus.onclick = () => { templateTranslate(axis.map(a => -a * tplStep)); tplTotals.t[i] -= tplStep; draw(); };
    const bPlus = document.createElement('button'); bPlus.textContent = g2;
    bPlus.onclick = () => { templateTranslate(axis.map(a => a * tplStep)); tplTotals.t[i] += tplStep; draw(); };
    g.append(bMinus, bPlus);
    shiftRow.appendChild(g);
  });

  const rotRow = document.getElementById('tplRotate'); rotRow.innerHTML = '';
  const rotDefs = [
    ['пов X', [1, 0, 0], [0, 1, 0], [0, 0, 1]],
    ['пов Y', [0, 1, 0], [0, 0, 1], [1, 0, 0]],
    ['пов Z', [0, 0, 1], [1, 0, 0], [0, 1, 0]],
  ];
  rotDefs.forEach(([label, axis, u, v], i) => {
    const g = document.createElement('div'); g.className = 'padGroup'; g.title = label;
    const bMinus = document.createElement('button'); bMinus.innerHTML = rotIconSVG(u, v, -1, camRotOverride) || '⟲';
    bMinus.onclick = () => { templateRotate(axis.map(a => -a * tplStep)); tplTotals.rot[i] -= tplStep; draw(); };
    const bPlus = document.createElement('button'); bPlus.innerHTML = rotIconSVG(u, v, 1, camRotOverride) || '⟳';
    bPlus.onclick = () => { templateRotate(axis.map(a => a * tplStep)); tplTotals.rot[i] += tplStep; draw(); };
    g.append(bMinus, bPlus);
    rotRow.appendChild(g);
  });

  const scaleRow = document.getElementById('tplScale'); scaleRow.innerHTML = '';
  {
    const g = document.createElement('div'); g.className = 'padGroup'; g.title = 'масштаб';
    const bMinus = document.createElement('button'); bMinus.textContent = '−';
    bMinus.onclick = () => { templateScaleTo(tplTotals.scale - tplStep); draw(); };
    const bPlus = document.createElement('button'); bPlus.textContent = '+';
    bPlus.onclick = () => { templateScaleTo(tplTotals.scale + tplStep); draw(); };
    g.append(bMinus, bPlus);
    scaleRow.appendChild(g);
  }

  const stepRow = document.getElementById('tplStepSec'); stepRow.innerHTML = '';
  const stepGroup = document.createElement('div'); stepGroup.className = 'padGroup'; stepGroup.title = 'крок';
  for (const v of [0.1, 1, 5, 10]) {
    const b = document.createElement('button'); b.textContent = v;
    b.classList.toggle('on', v === tplStep);
    b.onclick = () => { tplStep = v; [...stepGroup.children].forEach(x => x.classList.toggle('on', +x.textContent === tplStep)); };
    stepGroup.appendChild(b);
  }
  stepRow.appendChild(stepGroup);

  const resetRow = document.getElementById('tplResetSec'); resetRow.innerHTML = '';
  const bReset = document.createElement('button'); bReset.textContent = 'Скинути';
  bReset.onclick = () => { templateReset(); draw(); };
  resetRow.appendChild(bReset);
}

// ---------------------------------------------------------------- майстер (кроки)
// Розгорнутий лише один крок одразу - як в акордеоні. Крок сам по собі нічого
// не рахує, тільки показує, чого бракує (фото/розмітка) і чи вже є розрахунок.
function wizExpand(n) {
  document.querySelectorAll('.wstep').forEach(el => {
    el.classList.toggle('open', el.id === 'wstep-' + n);
  });
}
document.querySelectorAll('.whead').forEach(b => {
  b.onclick = () => wizExpand(+b.dataset.step);
});

function currentTargetName() {
  const raw = document.getElementById('rawname').value.trim();
  return raw || sceneName || '';
}

// Скидає все, що показувалося для ПОПЕРЕДНЬОГО набору (лінії, камери, шар-
// список), коли поточна ціль майстра-панелі ще не порахована - інакше
// у в'ювері лишалась стара лінія з іншого набору, ніби вона стосується
// нового (реальна плутанина, не лише естетика).
function clearViewer(placeholderName) {
  splitMode = false; preSplit = null;
  document.getElementById('splitToggle').classList.remove('on');
  document.getElementById('splitToggle').disabled = true;
  document.getElementById('viewModeSingle').hidden = false;
  document.getElementById('paneLeftWrap').hidden = true;
  document.getElementById('paneBackLabel').hidden = true;
  scene = null; sceneName = null;
  camIndex = -1; camZoom = 1; camPanX = 0; camPanY = 0;
  group_sel = []; sel_point = null;
  Object.keys(photos).forEach(k => delete photos[k]);
  Object.keys(meshes).forEach(k => delete meshes[k]);
  markLines.back = []; markLines.left = [];
  document.getElementById('cams').innerHTML = '';
  document.getElementById('layers').innerHTML = '';
  document.getElementById('photoAdjust').hidden = true;
  document.getElementById('place').hidden = true;
  document.getElementById('group').hidden = true;
  document.getElementById('point').hidden = true;
  HUD.textContent = placeholderName
    ? `«${placeholderName}» ще не порахований\nперейдіть до кроку 2 і натисніть «Розрахувати»`
    : '';
  draw();
}

async function refreshWizard() {
  const name = currentTargetName();
  document.getElementById('w1mark').textContent = name || '';
  const w2 = document.getElementById('w2mark'), w3 = document.getElementById('w3mark'),
        w4 = document.getElementById('w4mark');
  if (!name) { w2.textContent = w3.textContent = w4.textContent = ''; refreshPending(); return; }

  let st;
  try {
    st = await (await fetch('/api/pipeline/status/' + name)).json();
  } catch (e) {
    document.getElementById('inputcheck').textContent = 'не вдалося перевірити: ' + e;
    return;
  }

  const ic = document.getElementById('inputcheck');
  ic.innerHTML = ['back', 'left', 'top']
    .map(v => `<div>${st.photos[v] ? '✓' : '✗'} фото ${v}</div>`).join('');
  const allPhotos = st.photos.back && st.photos.left && st.photos.top;
  w2.className = 'wmark ' + (st.calculated ? 'ok' : (allPhotos ? '' : 'bad'));
  w2.textContent = st.calculated ? 'порахована' : (allPhotos ? 'готово рахувати' : 'бракує фото');

  // Розмітка НЕОБОВ'ЯЗКОВА (2026-08-29) - на виробництві 300 шлемів/день,
  // 3 хвилини на ручну розмітку кожного зверху ще й доведення - забагато.
  // Якщо розмітки нема, contour_fit.py просто пропускає цей член нев'язки
  // (лишається силует + контур зверху) - трохи слабший старт, який
  // добивається швидким доведенням у кроці 4. Тому тут не "помилка"
  // (жодного bad/✗), а нейтральна підказка: розмітка лише підвищує точність.
  const allMarks = st.marks.back && st.marks.left;
  const someMarks = st.marks.back || st.marks.left;
  const ms = document.getElementById('markstatus');
  ms.innerHTML = ['back', 'left']
    .map(v => `<div>${st.marks[v] ? '✓' : '—'} розмітка ${v}</div>`).join('');
  w3.className = 'wmark' + (allMarks ? ' ok' : '');
  w3.textContent = allMarks ? 'є' : (someMarks ? 'частково' : 'немає (необов\'язково)');

  const genBtn = document.getElementById('dogenerate');
  genBtn.disabled = !allPhotos;
  genBtn.title = genBtn.disabled ? 'бракує фото' : '';

  w4.textContent = st.calculated ? '' : 'ще не порахована';

  if (st.calculated) {
    if (sceneName !== name) await loadScene(name);
  } else if (sceneName !== name) {
    clearViewer(name);
  }
  refreshPending();
}
// ------------------------------------------------------- завантаження фото/еталона
// nabir-MMDD-NNN, порядковий номер за сьогодні - рахує сервер (GET
// /api/suggest_name) від того, що вже реально лежить в archive/, а не
// генерується наосліп на клієнті.
async function genName() {
  try {
    return (await (await fetch('/api/suggest_name')).json()).name;
  } catch (e) {
    return 'nabir-' + Date.now();          // мережа впала - хоч щось унікальне
  }
}

async function refreshPending() {
  const box = document.getElementById('pendingBox');
  let names;
  try { names = await (await fetch('/api/pending')).json(); }
  catch (e) { return; }
  if (!names.length) { box.innerHTML = ''; return; }
  const cur = currentTargetName();
  box.innerHTML = '<div style="color:#7c8aa0;font-size:11px;margin-bottom:3px">'
    + `у процесі (${names.length}):</div>`
    + names.map(n => `<button data-pending="${n}" style="${n === cur ? 'background:#1d4ed8' : ''}">${n}</button>`).join('');
  box.querySelectorAll('[data-pending]').forEach(b => {
    b.onclick = () => {
      document.getElementById('rawname').value = b.dataset.pending;
      refreshWizard();
    };
  });
}

// ------------------------------------------------------- модалка "новий набір"
// Навмисно НЕ використовує currentTargetName()/sceneName - своє окреме поле
// ns_name, щоб завантаження в жодному разі не могло потрапити у вже
// порахований набір, який зараз відкрито у в'ювері (був реальний ризик
// тихо переписати archive/v21/back.png, поки v21 обрано в дропдауні).
let _nsTaken = false;   // останній відомий статус ns_name - "вже порахований", блокує завантаження

async function checkNsName() {
  const el = document.getElementById('ns_namestatus');
  const name = document.getElementById('ns_name').value.trim();
  if (!name) { el.textContent = ''; _nsTaken = false; return; }
  let st;
  try { st = await (await fetch('/api/name_taken/' + encodeURIComponent(name))).json(); }
  catch (e) { el.textContent = ''; _nsTaken = false; return; }
  _nsTaken = !!st.calculated;
  if (st.calculated) {
    el.style.color = '#f87171';
    el.textContent = `⚠ «${name}» вже порахований - оберіть іншу назву`;
  } else if (st.has_data) {
    el.style.color = '#facc15';
    el.textContent = `«${name}» вже має якісь файли (це нормально, якщо це ваш же незавершений набір)`;
  } else {
    el.textContent = '';
  }
}
let _nsTimer = null;
document.getElementById('ns_name').oninput = () => {
  clearTimeout(_nsTimer);
  _nsTimer = setTimeout(checkNsName, 250);
};

async function openNewSet() {
  document.getElementById('ns_name').value = await genName();
  for (const id of ['ns_back', 'ns_left', 'ns_top', 'ns_ref']) document.getElementById(id).value = '';
  document.getElementById('ns_msg').textContent = '';
  document.getElementById('ns_namestatus').textContent = '';
  _nsTaken = false;
  document.getElementById('newsetOverlay').hidden = false;
}
document.getElementById('newsetopen').onclick = openNewSet;
document.getElementById('ns_cancel').onclick = () => { document.getElementById('newsetOverlay').hidden = true; };

document.getElementById('ns_upload').onclick = async () => {
  const msg = document.getElementById('ns_msg');
  const name = document.getElementById('ns_name').value.trim();
  if (!name) { msg.textContent = "вкажіть назву набору"; return; }
  await checkNsName();          // не покладаємось на застарілий результат дебаунса
  if (_nsTaken) { msg.textContent = `«${name}» вже порахований - оберіть іншу назву`; return; }
  const jobs = [['ns_back', 'back'], ['ns_left', 'left'], ['ns_top', 'top'], ['ns_ref', 'reference']]
    .map(([id, kind]) => ({ file: document.getElementById(id).files[0], kind }))
    .filter(j => j.file);
  if (!jobs.length) { msg.textContent = 'оберіть хоча б один файл'; return; }

  const done = [];
  for (const { file, kind } of jobs) {
    msg.textContent = `завантажую ${kind}...`;
    const fd = new FormData();
    fd.append('file', file);
    const r = await fetch(`/api/upload/${name}/${kind}`, { method: 'POST', body: fd });
    const j = await r.json();
    if (!r.ok) { msg.textContent = `помилка (${kind}): ` + (j.error || r.status); return; }
    done.push(j.saved);
  }
  if (document.getElementById('ns_pending').checked) {
    await fetch(`/api/pending/${name}`, { method: 'POST' });
  }
  msg.textContent = `завантажено: ${done.join(', ')}`;
  document.getElementById('newsetOverlay').hidden = true;
  document.getElementById('rawname').value = name;
  await refreshWizard();
  wizExpand(2);
};

// Немає реального потоку прогресу з бекенду (один блокуючий POST) - секундомір
// нижче єдине, що тут чесне (він завжди точний), тому це і є основний вміст
// оверлею. Раніше тут по колу гортались вигадані "етапи" (~4с кожен) - при
// типовому розрахунку в 2+ хв вони встигали повторитися разів 8-9, що на
// практиці читалося як "це несправжній прогрес", а не як інформація.
document.getElementById('dogenerate').onclick = async () => {
  const name = currentTargetName();
  if (!name) return;
  // /api/generate повністю перезбирає scene.json (як build_scene.py) - якщо
  // в поточному наборі вже є ручні правки, попереджаємо, бо повторний
  // розрахунок їх мовчки зітре. Перевіряємо тільки коли ЦЕЙ набір вже
  // завантажений у в'ювері (sceneName===name) - інакше touched ще нізвідки
  // взяти без зайвого запиту.
  if (sceneName === name && scene) {
    const editCurve = scene.curves.find(c => c.editable);
    const touchedCount = editCurve && editCurve.touched ? editCurve.touched.filter(Boolean).length : 0;
    if (touchedCount > 0) {
      const ok = confirm(`У наборі «${name}» вже є ${touchedCount} точок з ручними правками.\n`
        + 'Повторний розрахунок повністю перезбере лінію - усі правки буде втрачено.\n\n'
        + 'Продовжити?');
      if (!ok) return;
    }
  }
  const msg = document.getElementById('genmsg');
  const overlay = document.getElementById('calcOverlay');
  const calcText = document.getElementById('calcText');

  const t0 = Date.now();
  const fmt = s => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
  const setElapsed = () => {
    calcText.textContent = `Рахую «${name}»… ${fmt(Math.floor((Date.now() - t0) / 1000))}\n`
      + 'Перший розрахунок після запуску сервера триває довше (~2–3 хв) - '
      + 'наступні в цій сесії швидші.';
  };
  setElapsed();
  overlay.hidden = false;
  const timer = setInterval(setElapsed, 1000);

  msg.textContent = 'рахую...';
  try {
    const r = await fetch(`/api/generate/${name}`, { method: 'POST',
      headers: { 'Content-Type': 'application/json' }, body: '{}' });
    const j = await r.json();
    if (!r.ok) { msg.textContent = 'помилка: ' + (j.error || r.status); return; }
    msg.textContent = `готово: ${j.file}`;
    await reloadSceneList();
    document.getElementById('scenes').value = name;
    document.getElementById('rawname').value = '';
    await loadScene(name);
    await refreshWizard();
    wizExpand(4);
  } catch (e) {
    msg.textContent = 'помилка: ' + e;
  } finally {
    clearInterval(timer);
    overlay.hidden = true;
  }
};

function rebuildSceneSelect(list) {
  const sel = document.getElementById('scenes');
  sel.innerHTML = '';
  for (const s of list) {
    const o = document.createElement('option');
    o.value = s.name; o.textContent = `${s.name} — ${s.note || ''}`;
    sel.appendChild(o);
  }
}
async function reloadSceneList() {
  const list = await (await fetch('/api/scenes')).json();
  rebuildSceneSelect(list);
  return list;
}

(async () => {
  const list = await reloadSceneList();
  const sel = document.getElementById('scenes');
  sel.onchange = async () => {
    // Порожнить #rawname - інакше лишений там текст переважає в
    // currentTargetName() і refreshWizard() одразу ж скидає щойно обраний
    // сценарій назад (реальний баг, спіймано на v21 під час перевірки).
    // ПОСЛІДОВНО, не паралельно: якщо refreshWizard() стартує до того, як
    // loadScene() встиг записати sceneName, вона бачить СТАРЕ значення,
    // вирішує що "ціль змінилась" і сама викликає loadScene() ще раз - для
    // ІНШОГО (попереднього) імені, переписуючи щойно завантажене (теж
    // спіймано на живих кліках, не гіпотетично).
    document.getElementById('rawname').value = '';
    await loadScene(sel.value);
    await refreshWizard();
  };
  if (list.length) { await loadScene(list[0].name); wizExpand(4); }
  else { HUD.textContent = 'немає жодної сцени в data/scenes'; wizExpand(1); }
  await refreshWizard();
})();
