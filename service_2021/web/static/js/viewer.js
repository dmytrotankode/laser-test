'use strict';
// Просмотрщик сцены. Без внешних библиотек - и не из аскетизма.
//
// Проекция здесь считается ТОЙ ЖЕ моделью камеры, в которой камеры посчитаны:
// Xc = R (X - C), пиксель = focal * Xc.xy / Xc.z + размер/2. Возьми мы готовый
// движок, режим "взгляд камерой" показывал бы похожую картинку, а не ту, что
// видит настоящая камера, и сверять с фотографией стало бы нельзя.

const cv = document.getElementById('c');
const ctx = cv.getContext('2d');
const HUD = document.getElementById('hud');

let scene = null;           // документ сцены
let sceneName = null;
// Поле зрения узкое намеренно: на 45 градусах купол по краям кадра заметно
// растягивается, и это принимают за ошибку геометрии.
let view = { yaw: 0.9, pitch: 0.5, dist: 3000, target: [0, 0, 0], fov: 30 };
let camIndex = -1;          // -1 = свободный обзор, иначе индекс камеры сцены
let sel_point = null;        // {cidx, pidx} выбранной точки редактируемой кривой (тонкая правка)
let group_sel = [];           // [pidx, ...] группа для комплексного сдвига (Shift+клик)
let camZoom = 1, camPanX = 0, camPanY = 0;   // зум/сдвиг ТОЛЬКО картинки в виде камерой, не самой камеры
const NOMINAL_STANDOFF = 10.0;               // мм, тот же, что ls_points.NOMINAL_STANDOFF в 2021
const shown = {};           // имя слоя -> показывать
const photos = {};          // имя камеры -> Image
const meshes = {};          // имя меша -> {tris:Float32Array}

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
  ctx.globalAlpha = m.solid ? 1 : m.opacity;
  for (const [, P, sh] of out) {
    ctx.fillStyle = `rgb(${r*sh|0},${g*sh|0},${b*sh|0})`;
    ctx.beginPath();
    ctx.moveTo(P[0][0], P[0][1]); ctx.lineTo(P[1][0], P[1][1]);
    ctx.lineTo(P[2][0], P[2][1]); ctx.closePath(); ctx.fill();
  }
  ctx.globalAlpha = 1;
}

function draw() {
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

  // фотография под режимом "взгляд камерой"
  if (camIndex >= 0 && document.getElementById('photo').checked) {
    const cam = scene.cameras[camIndex], im = photos[cam.name];
    if (im && im.complete && im.naturalWidth) {
      const f = pr.fit;
      ctx.globalAlpha = 0.75;
      ctx.drawImage(im, f.ox, f.oy, f.iw * f.k, f.ih * f.k);
      ctx.globalAlpha = 1;
    }
  }
  if (document.getElementById('grid').checked) drawGrid(pr);
  if (document.getElementById('axes').checked) drawAxes(pr);

  const solid = document.getElementById('solid').checked;
  for (const m of scene.meshes || []) if (shown[m.name]) { m.solid = solid; drawMesh(m, pr); }
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
      ctx.fillStyle = sel ? '#facc15' : (touched ? '#ef4444' : '#94a3b8');
      const r = (sel ? 6 : (touched ? 4.5 : 3.5)) * devicePixelRatio * 0.8;
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

  let hud = camIndex >= 0
    ? `погляд камерою ${scene.cameras[camIndex].name}\nфокус ${scene.cameras[camIndex].focal_px.toFixed(0)} px`
    : `вільний огляд\n${scene.frame}, мм`;
  const rs = refStats();
  if (rs) hud += `\n\nпроти еталона:\nсереднє ${rs.mean.toFixed(2)} мм, макс ${rs.max.toFixed(2)} мм\nв допуску 2мм: ${rs.pct.toFixed(0)}%`;
  HUD.textContent = hud;
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
});
addEventListener('mouseup', e => {
  // Клик почти без движения мыши - выбор точки, а не вращение обзора.
  if (drag && Math.hypot(e.clientX - drag.x0, e.clientY - drag.y0) < 4) {
    trySelectPoint(e, e.shiftKey);
  }
  drag = null;
});

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

// Обычный клик - тонкая правка одной точки (сбрасывает групповой выбор).
// Shift+клик - копится в группу для комплексного сдвига (buildGroupEditor).
function trySelectPoint(e, shift) {
  if (!scene) return;
  const hit = findPointAt(e);
  if (shift) {
    if (!hit) return;
    const i = group_sel.findIndex(g => g.cidx === hit.cidx && g.pidx === hit.pidx);
    if (i >= 0) group_sel.splice(i, 1); else group_sel.push(hit);
    sel_point = null;
    document.getElementById('point').hidden = true;
    buildGroupEditor();
  } else {
    sel_point = hit;
    group_sel = [];              // группа возвращается к "вся линия", не прячется
    buildPointEditor();
    buildGroupEditor();
  }
  draw();
}

function buildPointEditor() {
  const box = document.getElementById('point');
  if (!sel_point) { box.hidden = true; return; }
  box.hidden = false;
  const c = scene.curves[sel_point.cidx], pi = sel_point.pidx;
  const id = c.ids ? c.ids[pi] : pi;
  const touched = c.touched && c.touched[pi];
  document.getElementById('ptitle').textContent =
    `#${id}${touched ? ' (торкнута)' : ' (розрахункова)'}`;
  const ctl = document.getElementById('pointctl');
  ctl.innerHTML = '';
  const labels = ['X', 'Y', 'Z'];
  for (let i = 0; i < 3; i++) {
    const row = document.createElement('div');
    row.className = 'prow';
    row.innerHTML = `<b>${labels[i]}</b><button>−</button><input><button>+</button>`;
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
cv.addEventListener('wheel', e => {
  e.preventDefault();
  if (camIndex >= 0) {
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
    draw();
    return;
  }
  view.dist *= Math.exp(e.deltaY * 0.0012);
  draw();
}, { passive: false });
addEventListener('resize', draw);

// ---------------------------------------------------------------- загрузка
function layerRow(name, color, key) {
  const l = document.createElement('label');
  l.innerHTML = `<input type="checkbox" checked><span class="sw" style="background:${color}"></span>${name}`;
  l.querySelector('input').onchange = e => { shown[key] = e.target.checked; draw(); };
  shown[key] = true;
  return l;
}

async function loadScene(name) {
  scene = await (await fetch('/api/scene/' + name)).json();
  sceneName = name;
  scene.curves = scene.curves || []; scene.points = scene.points || [];
  scene.meshes = scene.meshes || []; scene.cameras = scene.cameras || [];

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
    if (c.editable && c.axes) layers.appendChild(layerRow('шлях сопла (живий)', '#93c5fd', 'nozzle:' + c.name));
  }
  for (const s of scene.points) layers.appendChild(layerRow(s.name, s.color, s.name));
  for (const m of scene.meshes) {
    layers.appendChild(layerRow(m.name, m.color, m.name));
    if (m.rim) layers.appendChild(layerRow('кромка моделі', '#f97316', 'rim:' + m.name));
  }
  for (const c of scene.cameras) layers.appendChild(layerRow('камера ' + c.name, '#38bdf8', 'cam:' + c.name));

  const cams = document.getElementById('cams'); cams.innerHTML = '';
  scene.cameras.forEach((cam, i) => {
    const b = document.createElement('button');
    b.textContent = 'Погляд камерою ' + cam.name;
    b.onclick = () => {
      camIndex = camIndex === i ? -1 : i;
      camZoom = 1; camPanX = 0; camPanY = 0;
      [...cams.children].forEach((x, j) => x.classList.toggle('on', j === camIndex));
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
  buildGroupEditor();
  draw();
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
  if (!scene.meshes.length) { box.hidden = true; return; }
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

function buildGroupEditor() {
  const box = document.getElementById('group');
  const ci = activeCurveIndex();
  if (ci < 0) { box.hidden = true; return; }
  box.hidden = false;
  const pts = activePoints();
  const whole = group_sel.length === 0;
  document.getElementById('gtitle').textContent =
    whole ? `уся лінія (${pts.length})` : `вибрано ${pts.length} із ${scene.curves[ci].points.length}`;

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
  const rotRows = [['пов X', [1,0,0]], ['пов Y', [0,1,0]], ['пов Z', [0,0,1]]];
  for (const [label, axis, i] of rotRows.map((r, i) => [...r, i])) {
    const row = document.createElement('div');
    row.className = 'prow';
    row.innerHTML = `<b>${label}</b><button>−</button><input><button>+</button>`;
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
    row.innerHTML = `<b>${label}</b><button>−</button><input><button>+</button>`;
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

  document.getElementById('gselall').onclick = () => { group_sel = []; buildGroupEditor(); draw(); };
  document.getElementById('gselvis').onclick = () => {
    const pr = projector();
    const near = nearSideMask(c, pr);
    group_sel = c.points.map((_, pi) => pi)
      .filter(pi => camIndex < 0 || near[pi])
      .map(pi => ({ cidx: ci, pidx: pi }));
    sel_point = null;
    document.getElementById('point').hidden = true;
    buildGroupEditor(); draw();
  };
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
  };
  document.getElementById('gclear').onclick = () => {
    group_sel = []; buildGroupEditor(); draw();
  };
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

document.getElementById('reset').onclick = () => {
  camIndex = -1;
  camZoom = 1; camPanX = 0; camPanY = 0;
  [...document.getElementById('cams').children].forEach(x => x.classList.remove('on'));
  if (scene) { view.target = scene._center.slice(); view.yaw = 0.9; view.pitch = 0.5; }
  draw();
};
for (const id of ['grid', 'axes', 'photo', 'solid'])
  document.getElementById(id).onchange = draw;

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

async function refreshWizard() {
  const name = currentTargetName();
  document.getElementById('w1mark').textContent = name || '';
  const w2 = document.getElementById('w2mark'), w3 = document.getElementById('w3mark'),
        w4 = document.getElementById('w4mark');
  if (!name) { w2.textContent = w3.textContent = w4.textContent = ''; return; }

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

  const allMarks = st.marks.back && st.marks.left;
  const ms = document.getElementById('markstatus');
  ms.innerHTML = ['back', 'left']
    .map(v => `<div>${st.marks[v] ? '✓' : '✗'} розмітка ${v}</div>`).join('')
    + (allMarks ? '' : '<div style="margin-top:6px;color:#7c8aa0">'
      + 'розмітки лінії згину бракує - поки що її можна зробити тільки старим '
      + 'інструментом (service_3030/app.py, порт 3030)</div>');
  w3.className = 'wmark ' + (allMarks ? 'ok' : 'bad');
  w3.textContent = allMarks ? 'є' : 'немає';

  const genBtn = document.getElementById('dogenerate');
  genBtn.disabled = !(allPhotos && allMarks);
  genBtn.title = genBtn.disabled ? 'бракує фото або розмітки лінії згину' : '';

  w4.textContent = st.calculated ? '' : 'ще не порахована';
}
document.getElementById('rawname').oninput = refreshWizard;

document.getElementById('dogenerate').onclick = async () => {
  const name = currentTargetName();
  if (!name) return;
  const msg = document.getElementById('genmsg');
  msg.textContent = 'рахую...';
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
  sel.onchange = () => { loadScene(sel.value); refreshWizard(); };
  if (list.length) { await loadScene(list[0].name); wizExpand(4); }
  else { HUD.textContent = 'немає жодної сцени в data/scenes'; wizExpand(1); }
  await refreshWizard();
})();
