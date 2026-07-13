// form2.js – Handles Form 2 UI interactions
(() => {
  const sessionInput = document.getElementById('session-id');
  const pipelineDiv = document.getElementById('pipeline');
  const sessionBadge = document.getElementById('session-badge');
  const startCalcBtn = document.getElementById('start-calc-btn');
  const visualizeBtn = document.getElementById('visualize-btn');
  const globalLog = document.getElementById('global-log');

  // UUID v4 generator (RFC‑4122)
  const generateUuid = () => (
    ([1e7]+-1e3+-4e3+-8e3+-1e11)
      .replace(/[018]/g, c => (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c/4).toString(16))
  );

  // Initialize session on page load
  const sid = generateUuid();
  sessionInput.value = sid;
  sessionBadge.textContent = sid;
  pipelineDiv.classList.remove('hidden');

  const log = (msg) => {
    const ts = new Date().toISOString();
    globalLog.textContent += `[${ts}] ${msg}\n`;
    globalLog.scrollTop = globalLog.scrollHeight;
  };

  log(`Session "${sid}" started`);

  // Mapping of step keys to Ukrainian step names
  const stepNames = {
    step01: 'Парсинг LS',
    step02: 'Вирівнювання 3D',
    step03: 'Заморожування простору',
    step04: 'Сегментація еталону',
    step05: 'Проєкція еталону',
    step06: 'Розміщення проєкції',
    step07: 'Підгонка еталону',
    step08: 'Сегментація поточної моделі',
    step09: 'Підгонка поточної позиції',
    step10: 'Текстурне підгонка',
    step11: 'Контурна підгонка',
    step11b: 'Нейромережева 3D реконструкція шолома',
    step12: 'Аналіз результатів',
    step13: 'Генерація LS та візуалізація'
  };

  // Function to add metric entry to sidebar
  const addMetric = (stepKey, status, info = '') => {
    const panel = document.getElementById('metrics-panel');
    if (panel.classList.contains('hidden')) panel.classList.remove('hidden');
    const li = document.createElement('li');
    li.textContent = `${stepNames[stepKey] || stepKey} – ${status}` + (info ? ` (${info})` : '');
    document.getElementById('metrics-list').appendChild(li);
  };

  const startCalculation = async () => {
    const steps = [
      'step01', 'step02', 'step03', 'step04', 'step05', 'step06',
      'step07', 'step08', 'step09', 'step10', 'step11', 'step11b', 'step12', 'step13'
    ];
    for (const step of steps) {
      log(`Running ${step} (${stepNames[step]})…`);
      try {
        const res = await fetch(`/api/${step}?session_id=${encodeURIComponent(sid)}`);
        const json = await res.json();
        if (json.result && json.result.success) {
          log(`${step} (${stepNames[step]}) completed successfully`);
          // Extract specific indicators if returned in json.data or json.metrics
          let details = '';
          if (step === 'step01') {
            if (json.data) details = json.data;
          } else if (step === 'step02') {
            if (json.data && json.data.rx !== undefined) {
              details = `Зсув: [X:${json.data.tx.toFixed(1)}, Y:${json.data.ty.toFixed(1)}, Z:${json.data.tz.toFixed(1)}] мм; Поворот: [X:${json.data.rx.toFixed(1)}°, Y:${json.data.ry.toFixed(1)}°, Z:${json.data.rz.toFixed(1)}°]; Масштаб: ${json.data.scale.toFixed(4)}`;
            }
          } else if (step === 'step03') {
            if (json.data && json.data.remaining_points !== undefined) {
              details = `Точок після фільтрації: ${json.data.remaining_points} (відкинуто ${json.data.points_dropped})`;
            }
          } else if (step === 'step04') {
            details = `Створено маски проекцій для камер`;
          } else if (step === 'step05') {
            details = `Згенеровано рендери проекцій`;
          } else if (step === 'step06') {
            if (json.data) {
              details = `Розміщено проекцій: ${json.data.placements_count !== undefined ? json.data.placements_count : (Array.isArray(json.data) ? json.data.length : 'OK')}`;
            }
          } else if (step === 'step07') {
            if (json.data && json.data.delta_translation) {
              const dt = json.data.delta_translation;
              details = `Зсув еталону: [X:${dt[0].toFixed(2)}, Y:${dt[1].toFixed(2)}, Z:${dt[2].toFixed(2)}] мм`;
            }
          } else if (step === 'step08') {
            details = `Сегментовано маски поточної моделі`;
          } else if (step === 'step09') {
            if (json.data && json.data.metrics) {
              const m = json.data.metrics;
              details = `Зсув: [H:${m.shift_horizontal_mm}мм, V:${m.shift_vertical_mm}мм, D:${m.shift_depth_mm}мм]; Нахил: [P:${m.tilt_pitch_deg}°, R:${m.tilt_roll_deg}°, Y:${m.tilt_yaw_deg}°]`;
            }
          } else if (step === 'step10' || step === 'step11' || step === 'step11b') {
            if (json.data && json.data.metrics) {
              const m = json.data.metrics;
              details = `Зсув: [H:${m.shift_horizontal_mm}мм, V:${m.shift_vertical_mm}мм, D:${m.shift_depth_mm}мм]; Нахил: [P:${m.tilt_pitch_deg}°, R:${m.tilt_roll_deg}°, Y:${m.tilt_yaw_deg}°]`;
            } else if (json.data && json.data.delta_translation) {
              const dt = json.data.delta_translation;
              details = `Зсув: [X:${dt[0].toFixed(2)}, Y:${dt[1].toFixed(2)}, Z:${dt[2].toFixed(2)}]`;
            }
          } else if (step === 'step12') {
            if (json.data && json.data.metrics) {
              const m = json.data.metrics;
              details = `Фінал зсув: [H:${m.shift_horizontal_mm}мм, V:${m.shift_vertical_mm}мм, D:${m.shift_depth_mm}мм]; Нахил: [P:${m.tilt_pitch_deg}°, R:${m.tilt_roll_deg}°, Y:${m.tilt_yaw_deg}°]`;
            } else if (json.data && json.data.delta_translation) {
              const dt = json.data.delta_translation;
              details = `Фінал зсув: [X:${dt[0].toFixed(1)}, Y:${dt[1].toFixed(1)}, Z:${dt[2].toFixed(1)}]`;
            }
          } else if (step === 'step13') {
            details = `Згенеровано та збережено скоригований FANUC .LS файл`;
          }
          addMetric(step, '✅', details);
        } else {
          const errMsg = json.result?.stderr || 'unknown';
          log(`${step} (${stepNames[step]}) completed with errors: ${errMsg}`);
          addMetric(step, '❌', errMsg);
        }
      } catch (e) {
        log(`Error calling ${step}: ${e.message}`);
        addMetric(step, '❌', e.message);
        break;
      }
    }
    // After all steps are done, fetch detailed metrics
    fetchMetrics();
    // Enable visualization button
    visualizeBtn.disabled = false;
  };

  // Function to fetch and display step13 metrics
  const fetchMetrics = async () => {
    try {
      // 1. Fetch step02 alignment for Etalon 3D helmet
      const s02Res = await fetch(`/api/step02?session_id=${encodeURIComponent(sid)}`);
      const s02Json = await s02Res.json();
      const etModel = s02Json.data || {};

      // 2. Fetch step07 fit etalon for Etalon Rim / Cutting line
      const s07Res = await fetch(`/api/step07?session_id=${encodeURIComponent(sid)}`);
      const s07Json = await s07Res.json();
      const etRim = s07Json.data || {};

      // 3. Fetch step12 final pose for Current (helmet, cutting line, center & deviations)
      const s12Res = await fetch(`/api/step12?session_id=${encodeURIComponent(sid)}`);
      const s12Json = await s12Res.json();
      const curData = s12Json.data || {};

      // 4. Fetch center points computed at step13
      const s13Res = await fetch(`/api/step13_visualisation_data?session_id=${encodeURIComponent(sid)}`);
      const s13Json = await s13Res.json();
      const s13Metrics = s13Json.metrics || {};

      const detailedPanel = document.getElementById('detailed-panel');
      const contentDiv = document.getElementById('detailed-report-content');
      
      if (detailedPanel && contentDiv) {
        detailedPanel.classList.remove('hidden');

        // Extract translation, rotation, scale
        const etModelTx = etModel.tx !== undefined ? etModel.tx.toFixed(2) : '0.00';
        const etModelTy = etModel.ty !== undefined ? etModel.ty.toFixed(2) : '0.00';
        const etModelTz = etModel.tz !== undefined ? etModel.tz.toFixed(2) : '0.00';
        const etModelRx = etModel.rx !== undefined ? etModel.rx.toFixed(2) : '0.00';
        const etModelRy = etModel.ry !== undefined ? etModel.ry.toFixed(2) : '0.00';
        const etModelRz = etModel.rz !== undefined ? etModel.rz.toFixed(2) : '0.00';
        const etModelScale = etModel.scale !== undefined ? etModel.scale.toFixed(4) : '1.0000';

        // Etalon Rim
        const etRimTx = etRim.delta_translation ? etRim.delta_translation[0].toFixed(2) : '0.00';
        const etRimTy = etRim.delta_translation ? etRim.delta_translation[1].toFixed(2) : '0.00';
        const etRimTz = etRim.delta_translation ? etRim.delta_translation[2].toFixed(2) : '0.00';
        const etRimRot = etRim.delta_rotvec ? etRim.delta_rotvec.map(v => (v * 180 / Math.PI).toFixed(2)) : ['0.00', '0.00', '0.00'];

        // Center points
        const cE_x = s13Metrics.etalon_center ? s13Metrics.etalon_center.x.toFixed(2) : '0.00';
        const cE_y = s13Metrics.etalon_center ? s13Metrics.etalon_center.y.toFixed(2) : '0.00';
        const cE_z = s13Metrics.etalon_center ? s13Metrics.etalon_center.z.toFixed(2) : '0.00';

        const cC_x = s13Metrics.current_center ? s13Metrics.current_center.x.toFixed(2) : '0.00';
        const cC_y = s13Metrics.current_center ? s13Metrics.current_center.y.toFixed(2) : '0.00';
        const cC_z = s13Metrics.current_center ? s13Metrics.current_center.z.toFixed(2) : '0.00';

        // Current parameters (Shifted by final values)
        const finalT = curData.delta_translation || [0,0,0];
        const finalRot = curData.delta_rotvec || [0,0,0];
        const finalRotDeg = finalRot.map(v => (v * 180 / Math.PI).toFixed(2));

        const curModelTx = (parseFloat(etModelTx) + finalT[0]).toFixed(2);
        const curModelTy = (parseFloat(etModelTy) + finalT[1]).toFixed(2);
        const curModelTz = (parseFloat(etModelTz) + finalT[2]).toFixed(2);

        const dev = curData.metrics || {};
        const devH = dev.shift_horizontal_mm !== undefined ? dev.shift_horizontal_mm.toFixed(2) : '0.00';
        const devV = dev.shift_vertical_mm !== undefined ? dev.shift_vertical_mm.toFixed(2) : '0.00';
        const devD = dev.shift_depth_mm !== undefined ? dev.shift_depth_mm.toFixed(2) : '0.00';
        const devP = dev.tilt_pitch_deg !== undefined ? dev.tilt_pitch_deg.toFixed(2) : '0.00';
        const devR = dev.tilt_roll_deg !== undefined ? dev.tilt_roll_deg.toFixed(2) : '0.00';
        const devY = dev.tilt_yaw_deg !== undefined ? dev.tilt_yaw_deg.toFixed(2) : '0.00';

        contentDiv.innerHTML = `
          <div style="margin-bottom:0.8rem; border-bottom:1px solid #333; padding-bottom:0.4rem;">
            <b style="color:#00d2ff; text-transform:uppercase; font-size:0.85rem;">Еталонні:</b>
            <div style="margin-top:0.3rem;">
              <b>1. 3D шолом еталона:</b><br/>
              &nbsp;&nbsp;Зсув: [X: ${etModelTx}, Y: ${etModelTy}, Z: ${etModelTz}] мм<br/>
              &nbsp;&nbsp;Поворот: [X: ${etModelRx}°, Y: ${etModelRy}°, Z: ${etModelRz}°]<br/>
              &nbsp;&nbsp;Масштаб: ${etModelScale}
            </div>
            <div style="margin-top:0.3rem;">
              <b>2. Лінія обрізки еталона:</b><br/>
              &nbsp;&nbsp;Зсув: [X: ${etRimTx}, Y: ${etRimTy}, Z: ${etRimTz}] мм<br/>
              &nbsp;&nbsp;Поворот: [X: ${etRimRot[0]}°, Y: ${etRimRot[1]}°, Z: ${etRimRot[2]}°]<br/>
              &nbsp;&nbsp;Масштаб: 1.0000
            </div>
            <div style="margin-top:0.3rem;">
              <b>3. Центр еталона Cᴇ:</b><br/>
              &nbsp;&nbsp;[X: ${cE_x}, Y: ${cE_y}, Z: ${cE_z}] мм
            </div>
          </div>

          <div style="margin-bottom:0.8rem; border-bottom:1px solid #333; padding-bottom:0.4rem;">
            <b style="color:#ffb700; text-transform:uppercase; font-size:0.85rem;">Поточні:</b>
            <div style="margin-top:0.3rem;">
              <b>1. 3D шолом поточний:</b><br/>
              &nbsp;&nbsp;Зсув: [X: ${curModelTx}, Y: ${curModelTy}, Z: ${curModelTz}] мм<br/>
              &nbsp;&nbsp;Поворот: [X: ${(parseFloat(etModelRx) + parseFloat(finalRotDeg[0])).toFixed(2)}°, Y: ${(parseFloat(etModelRy) + parseFloat(finalRotDeg[1])).toFixed(2)}°, Z: ${(parseFloat(etModelRz) + parseFloat(finalRotDeg[2])).toFixed(2)}°]<br/>
              &nbsp;&nbsp;Масштаб: ${etModelScale}
            </div>
            <div style="margin-top:0.3rem;">
              <b>2. Лінія обрізки поточної моделі:</b><br/>
              &nbsp;&nbsp;Зсув: [X: ${(parseFloat(etRimTx) + finalT[0]).toFixed(2)}, Y: ${(parseFloat(etRimTy) + finalT[1]).toFixed(2)}, Z: ${(parseFloat(etRimTz) + finalT[2]).toFixed(2)}] мм<br/>
              &nbsp;&nbsp;Поворот: [X: ${(parseFloat(etRimRot[0]) + parseFloat(finalRotDeg[0])).toFixed(2)}°, Y: ${(parseFloat(etRimRot[1]) + parseFloat(finalRotDeg[1])).toFixed(2)}°, Z: ${(parseFloat(etRimRot[2]) + parseFloat(finalRotDeg[2])).toFixed(2)}°]
            </div>
            <div style="margin-top:0.3rem;">
              <b>3. Центр поточного шолома Cᴄ:</b><br/>
              &nbsp;&nbsp;[X: ${cC_x}, Y: ${cC_y}, Z: ${cC_z}] мм
            </div>
            <div style="margin-top:0.3rem;">
              <b>4. Вектори трансформації:</b><br/>
              &nbsp;&nbsp;Зсув: [${finalT.map(v=>v.toFixed(2)).join(', ')}] мм<br/>
              &nbsp;&nbsp;Ротація: [${finalRot.map(v=>v.toFixed(4)).join(', ')}] рад<br/>
              &nbsp;&nbsp;Кут: [${finalRotDeg.join('°, ')}°]
            </div>
          </div>

          <div>
            <b style="color:#00ff66; text-transform:uppercase; font-size:0.85rem;">Розраховані відхилення:</b>
            <table style="width:100%; font-size:0.8rem; margin-top:0.3rem; border-collapse:collapse;">
              <tr><td style="padding:2px 0;">↔ Горизонталь</td><td style="text-align:right; font-weight:bold; color:#fff;">${devH} мм</td></tr>
              <tr><td style="padding:2px 0;">↕ Вертикаль</td><td style="text-align:right; font-weight:bold; color:#fff;">${devV} мм</td></tr>
              <tr><td style="padding:2px 0;">⟷ Глибина</td><td style="text-align:right; font-weight:bold; color:#fff;">${devD} мм</td></tr>
              <tr><td style="padding:2px 0;">↻ Нахил вперед/назад</td><td style="text-align:right; font-weight:bold; color:#fff;">${devP}°</td></tr>
              <tr><td style="padding:2px 0;">↻ Нахил вліво/вправо</td><td style="text-align:right; font-weight:bold; color:#fff;">${devR}°</td></tr>
              <tr><td style="padding:2px 0;">↻ Поворот осі</td><td style="text-align:right; font-weight:bold; color:#fff;">${devY}°</td></tr>
            </table>
          </div>
        `;
      }
    } catch (e) {
      console.error('Failed to fetch metrics', e);
    }
  };

  // Original log line end
  log('All steps finished – you can now visualise the result');
  visualizeBtn.disabled = false;

  // Removed simulated timeout – real API workflow handles calculation
  // Visualization will be opened via the Visualize button

  // Add handler for Visualize button
  visualizeBtn.addEventListener('click', () => {
    const url = `/vis/step13?session_id=${encodeURIComponent(sid)}`;
    window.open(url, '_blank');
  });

  startCalcBtn.addEventListener('click', () => {
    startCalculation();
  });
})();
