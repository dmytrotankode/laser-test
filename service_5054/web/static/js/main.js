let currentSessionId = null;
let stepPollInterval = null;
let step00GlobalData = null;
let step02GlobalData = null;

async function startSession() {
    const res = await fetch('/api/start_session');
    const data = await res.json();
    currentSessionId = data.session_id;
    
    document.getElementById('session-label').innerText = `Сесія: ${currentSessionId}`;
    document.getElementById('session-label').style.color = '#00d2ff';
    // Clear zones
    clearStepData('00');
    
    // Enable Step 0
    document.getElementById('btn-run-00').disabled = false;
    document.getElementById('card-00').classList.add('active');
}

function markStepDone(stepId) {
    let btn = document.getElementById(`btn-run-${stepId}`);
    if (!btn && stepId === '03') btn = document.getElementById('btn-step03');
    if (btn) {
        btn.innerText = `Перерахувати (Крок ${parseInt(stepId)})`;
        btn.style.background = "#4CAF50";
        btn.disabled = false;
        btn.classList.add('recalc-btn');
    }
    
    // Enable NEXT step
    const nextStepStr = String(parseInt(stepId) + 1).padStart(2, '0');
    let nextBtn = document.getElementById(`btn-run-${nextStepStr}`);
    let nextCard = document.getElementById(`card-${nextStepStr}`);
    
    // Fallback for cached old index.html
    if (!nextBtn && nextStepStr === '03') {
        nextBtn = document.getElementById('btn-step03');
        nextCard = document.getElementById('card-step03');
    }
    
    if (nextBtn && !nextBtn.classList.contains('recalc-btn')) {
        nextBtn.disabled = false;
        if (nextCard) nextCard.classList.add('active');
    }
}

async function resumeSession() {
    try {
        const res = await fetch('/api/latest_session');
        const data = await res.json();
        if (data && data.session_id) {
            currentSessionId = data.session_id;
            document.getElementById('session-label').innerText = `Сесія: ${currentSessionId}`;
            document.getElementById('session-label').style.color = '#00d2ff';
            
            // Clear zones
            document.getElementById('visualizations').innerHTML = '';
            document.getElementById('metrics-table').innerHTML = '';
            
            const steps = ['00', '01', '02', '03', '04', '05', '06'];
            let lastDone = null;
            
            for (const step of steps) {
                try {
                    const stepRes = await fetch(`/api/step${step}?session_id=${currentSessionId}&action=poll`);
                    if (!stepRes.ok) break;
                    const stepData = await stepRes.json();
                    
                    if (stepData.status === 'done' || stepData.data) {
                        const parsedData = stepData.data || stepData;
                        // call corresponding handler dynamically
                        window[`handleStep${step}Result`](parsedData);
                        markStepDone(step);
                        lastDone = step;
                    } else {
                        // this step is not done, break the chain
                        break;
                    }
                } catch (e) {
                    console.log(`Step ${step} not completed`, e);
                    break;
                }
            }
            
            if (lastDone === null) {
                document.getElementById('btn-run-00').disabled = false;
                document.getElementById('card-00').classList.add('active');
            }
        } else {
            document.getElementById('btn-run-00').disabled = false;
            document.getElementById('card-00').classList.add('active');
        }
    } catch (e) {
        console.error("Failed to resume session", e);
        document.getElementById('btn-run-00').disabled = false;
        document.getElementById('card-00').classList.add('active');
    }
}

// Call on startup
document.addEventListener('DOMContentLoaded', () => {
    resumeSession();
});

function addMetricGroup(title, stepId = '00') {
    const table = document.getElementById('metrics-table');
    const tr = document.createElement('tr');
    tr.style.backgroundColor = '#1f1f1f';
    tr.setAttribute('data-step', stepId);
    tr.innerHTML = `<th colspan="2" style="text-align:center; padding:5px; border-bottom:1px solid #444; color:#00d2ff; font-weight:600;">${title}</th>`;
    table.appendChild(tr);
}

function addMetric(key, value, stepId = '00') {
    const table = document.getElementById('metrics-table');
    const tr = document.createElement('tr');
    tr.setAttribute('data-step', stepId);
    tr.innerHTML = `<td><strong>${key}</strong></td><td>${value}</td>`;
    table.appendChild(tr);
}

function createVisualizationBlock(id, title, stepId = '00') {
    const visZone = document.getElementById('visualizations');
    const panel = document.createElement('div');
    panel.className = 'vis-panel';
    panel.setAttribute('data-step', stepId);
    panel.innerHTML = `
        <h3>${title}</h3>
        <div id="${id}" class="canvas-container"></div>
    `;
    visZone.appendChild(panel);
    return document.getElementById(id);
}

function clearStepData(fromStepId) {
    const steps = ['00', '01', '02', '03', '04', '05', '06'];
    const startIndex = steps.indexOf(fromStepId);
    if (startIndex === -1) return;
    
    for (let i = startIndex; i < steps.length; i++) {
        const step = steps[i];
        document.querySelectorAll(`[data-step="${step}"]`).forEach(el => el.remove());
        
        // Reset button states for cleared steps
        const btn = document.getElementById(`btn-run-${step}`);
        if (btn) {
            btn.disabled = true;
            btn.innerText = `Виконати етап ${parseInt(step)}`;
            btn.classList.remove('recalc-btn');
            btn.style.background = ""; // reset background
            document.getElementById(`card-${step}`).classList.remove('active');
            const statusLabel = document.getElementById(`status-${step}`);
            if (statusLabel) statusLabel.innerHTML = '';
        }
    }
}

function initThreeScene(container, pointSets, stlOptions = null, sceneOptions = {}) {
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x222222);
    
    // Add ambient light
    const ambientLight = new THREE.AmbientLight(0x606060); // Brighter ambient
    scene.add(ambientLight);
    
    // Add directional lights from multiple angles unless custom lights are provided
    if (sceneOptions.customLights && sceneOptions.customLights.length > 0) {
        sceneOptions.customLights.forEach(l => {
            const dirLight = new THREE.DirectionalLight(l.color || 0xffffff, l.intensity);
            dirLight.position.set(l.dir[0], l.dir[1], l.dir[2]).normalize();
            scene.add(dirLight);
        });
    } else {
        const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.6);
        dirLight1.position.set(1, 1, 1).normalize();
        scene.add(dirLight1);

        const dirLight2 = new THREE.DirectionalLight(0xffffff, 0.6);
        dirLight2.position.set(-1, 1, -1).normalize();
        scene.add(dirLight2);

        const dirLight3 = new THREE.DirectionalLight(0xffffff, 0.4);
        dirLight3.position.set(0, -1, 1).normalize();
        scene.add(dirLight3);
    }

    const targetAspect = 4096 / 3000;
    const viewerHeight = Math.round(container.clientWidth / targetAspect);
    const camera = new THREE.PerspectiveCamera(7.811, targetAspect, 0.1, 10000);
    camera.up.set(0, 0, -1); // Z is down in robot space, so -Z is UP on screen
    const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true, alpha: true });
    renderer.setSize(container.clientWidth, viewerHeight);
    container.appendChild(renderer.domElement);

    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    
    let center = new THREE.Vector3(0, 0, 0);
    let totalPoints = 0;
    let allPoints = [];
    
    pointSets.forEach(pa => {
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(pa.points.length * 3);
        for(let i=0; i<pa.points.length; i++) {
            positions[i*3] = pa.points[i].x;
            positions[i*3+1] = pa.points[i].y;
            positions[i*3+2] = pa.points[i].z;
            
            center.x += pa.points[i].x;
            center.y += pa.points[i].y;
            center.z += pa.points[i].z;
            totalPoints++;
            allPoints.push(pa.points[i]);
        }
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        
        if (pa.isLine) {
            const lineMat = new THREE.LineBasicMaterial({ color: pa.color });
            const lineObj = new THREE.Line(geometry, lineMat);
            if (pa.name) lineObj.name = pa.name;
            scene.add(lineObj);
        } else {
            const material = new THREE.PointsMaterial({ color: pa.color, size: pa.size || 2 });
            const pointsObj = new THREE.Points(geometry, material);
            if (pa.name) pointsObj.name = pa.name;
            scene.add(pointsObj);
        }
    });

    if (stlOptions) {
        const loader = new THREE.STLLoader();
        loader.load(stlOptions.url, function (geom) {
            const mat = new THREE.MeshPhongMaterial({ color: stlOptions.color || 0x888888, specular: 0x111111, shininess: 50, transparent: true, opacity: stlOptions.opacity || 0.9, side: stlOptions.side || THREE.FrontSide });
            const mesh = new THREE.Mesh(geom, mat);
            mesh.name = 'stl_mesh';
            
            // set transform
            mesh.position.set(stlOptions.tx, stlOptions.ty, stlOptions.tz);
            // Euler rotation in THREE defaults to XYZ, my python Rz @ Ry @ Rx means ZYX.
            mesh.rotation.set(
                THREE.MathUtils.degToRad(stlOptions.rx),
                THREE.MathUtils.degToRad(stlOptions.ry),
                THREE.MathUtils.degToRad(stlOptions.rz),
                'ZYX'
            );
            mesh.scale.set(stlOptions.scale, stlOptions.scale, stlOptions.scale);
            
            const box = new THREE.Box3().setFromObject(mesh);
            const center = box.getCenter(new THREE.Vector3());
            container.stlCenter = [center.x, center.y, center.z];
            
            scene.add(mesh);
            if (stlOptions.onLoad) stlOptions.onLoad(container, scene, camera, renderer, controls);
        });
    }
    
    // Draw optional camera positions
    if (sceneOptions.cameras && sceneOptions.cameras.length > 0) {
        sceneOptions.cameras.forEach(c => {
            const camGeom = new THREE.ConeGeometry(50, 100, 4);
            const camMat = new THREE.MeshBasicMaterial({ color: 0xffff00, wireframe: true });
            const camMesh = new THREE.Mesh(camGeom, camMat);
            camMesh.position.set(c.pos[0], c.pos[1], c.pos[2]);
            const lookAt = c.look_at ? new THREE.Vector3(c.look_at[0], c.look_at[1], c.look_at[2]) : new THREE.Vector3(0, 0, 85);
            camMesh.lookAt(lookAt);
            scene.add(camMesh);
            
            if (c.look_at) {
                const lineGeom = new THREE.BufferGeometry().setFromPoints([
                    new THREE.Vector3(c.pos[0], c.pos[1], c.pos[2]),
                    lookAt
                ]);
                const lineMat = new THREE.LineBasicMaterial({ color: 0x00ffff, opacity: 0.6, transparent: true });
                const line = new THREE.Line(lineGeom, lineMat);
                scene.add(line);
            }
        });
    }

    container.setCameraView = function(pos, look_at, up_vector, f_px) {
        camera.position.set(pos[0], pos[1], pos[2]);
        controls.target.set(look_at[0], look_at[1], look_at[2]);
        if (up_vector) {
            camera.up.set(up_vector[0], up_vector[1], up_vector[2]);
        }
        if (f_px) {
            camera.fov = 2 * Math.atan(3000 / (2 * f_px)) * 180 / Math.PI;
            camera.updateProjectionMatrix();
        }
        camera.lookAt(look_at[0], look_at[1], look_at[2]);
        controls.update();
    };

    container.toggleObject = function(name, visible) {
        const obj = scene.getObjectByName(name);
        if (obj) obj.visible = visible;
    };

    if (allPoints.length > 0) {
        center.divideScalar(totalPoints);
        controls.target.copy(center);
        camera.position.set(center.x + 1500, center.y + 1500, center.z + 1500);
    } else {
        camera.position.set(1500, 1500, 1500);
    }
    
    controls.update();
    
    function animate() {
        requestAnimationFrame(animate);
        controls.update();
        renderer.render(scene, camera);
    }
    animate();
}

// --- STEP 0 ---
async function runStep00() {
    if (!currentSessionId) return;
    
    const btn = document.getElementById('btn-run-00');
    if (btn.classList.contains('recalc-btn')) {
        clearStepData('00');
    }
    btn.disabled = true;
    btn.innerText = "Обробка...";
    const warning = document.getElementById('step00-warning');
    if (warning) warning.style.display = 'block';
    
    await fetch(`/api/step00?session_id=${currentSessionId}&action=start`);
    
    stepPollInterval = setInterval(async () => {
        const res = await fetch(`/api/step00?session_id=${currentSessionId}&action=poll`);
        const result = await res.json();
        
        if (result.status === 'done' || result.data) { // sometimes it returns data directly if it was fast enough or format changed
            clearInterval(stepPollInterval);
            if (warning) warning.style.display = 'none';
            btn.innerText = "Виконано";
            btn.style.background = "#4CAF50";
            
            step00GlobalData = result.data || result; // store optics
            handleStep00Result(step00GlobalData);
            markStepDone('00');
            
        } else if (result.status === 'error') {
            clearInterval(stepPollInterval);
            if (warning) warning.style.display = 'none';
            btn.innerText = "Помилка";
            btn.style.background = "#f44336";
            alert("Помилка: " + result.message);
        }
    }, 1000);
}

function handleStep00Result(data) {
    step00GlobalData = data;
    addMetricGroup('Етап 0: Аналіз фото еталона', '00');
    ['Сзади', 'Слева', 'Сверху'].forEach(cam => {
        if (!data[cam]) return;
        addMetric(`${cam} (f_px)`, data[cam].f_px.toFixed(1), '00');
        addMetric(`${cam} (Зміщення X)`, data[cam].look_at_offset_x_mm.toFixed(1) + " мм", '00');
        addMetric(`${cam} (Зміщення Y)`, data[cam].look_at_offset_y_mm.toFixed(1) + " мм", '00');
    });
}

// --- STEP 1 ---
async function runStep01() {
    if (!currentSessionId) return;
    
    const btn = document.getElementById('btn-run-01');
    if (btn.classList.contains('recalc-btn')) {
        clearStepData('01');
    }
    btn.disabled = true;
    btn.innerText = "Обробка...";
    
    // Start step
    await fetch(`/api/step01?session_id=${currentSessionId}&action=start`);
    
    // Poll
    stepPollInterval = setInterval(async () => {
        const res = await fetch(`/api/step01?session_id=${currentSessionId}&action=poll`);
        const result = await res.json();
        
        if (result.status === 'done' || result.data) {
            clearInterval(stepPollInterval);
            btn.innerText = "Виконано";
            btn.style.background = "#4CAF50";
            
            // Render UI
            handleStep01Result(result.data || result);
            markStepDone('01');
            
        } else if (result.status === 'error') {
            clearInterval(stepPollInterval);
            btn.innerText = "Помилка";
            btn.style.background = "#f44336";
            console.error(result.message);
            alert("Помилка: " + result.message);
        }
    }, 1000);
}

function handleStep01Result(data) {
    addMetricGroup('Етап 1: Контури та обрізка', '01');
    addMetric('Вихідний файл оброблених LS', data.ls_path, '01');
    addMetric('Нахил еталона (X/вниз)', data.tilt_down_deg + " градусів", '01');
    addMetric('Нахил еталона (Y/проти_год)', data.yaw_ccw_deg + " градусів", '01');
    addMetric("Зміщення еталона", data.offset_mm + " мм", '01');
    addMetric("Кількість вихідних точок (відфільтровано)", data.original_points.length, '01');
    addMetric("Лінія обрізки (інтерпольована)", data.contour_points.length, '01');

    const visCont = createVisualizationBlock('vis-01-contour', 'Точки LS (X, Y, Z)', '01');
    initThreeScene(visCont, [
        { points: data.original_points, color: 0x00d2ff, size: 2.0 },
        { points: data.contour_points, color: 0xff0000, size: 4.0 }
    ]);
    
    const vis2Cont = createVisualizationBlock('vis-01-offset', 'Зона обрізки (Contact Points)', '01');
    initThreeScene(vis2Cont, [
        { points: data.contact_points, color: 0x00ff00, size: 3.0 }
    ]);
}

async function runStep02() {
    if (!currentSessionId) return;
    
    const btn = document.getElementById('btn-run-02');
    if (btn.classList.contains('recalc-btn')) {
        clearStepData('02');
    }
    btn.disabled = true;
    btn.innerText = "Обробка...";
    
    await fetch(`/api/step02?session_id=${currentSessionId}&action=start`);
    
    let poll = setInterval(async () => {
        const res = await fetch(`/api/step02?session_id=${currentSessionId}&action=poll`);
        const result = await res.json();
        
        if (result.status === 'done') {
            clearInterval(poll);
            btn.innerText = "Виконано";
            btn.style.background = "#4CAF50";
            handleStep02Result(result.data);
            markStepDone('02');
        } else if (result.status === 'error') {
            clearInterval(poll);
            btn.innerText = "Помилка";
            btn.style.background = "#f44336";
            console.error(result.message);
            alert("Помилка: " + result.message);
        }
    }, 1000);
}

function handleStep02Result(data) {
    step02GlobalData = data;
    addMetricGroup('Етап 2: 3D Вирівнювання', '02');
    addMetric("Шлях до 3D моделі", data.model_path, '02');
    addMetric("Зсув X, Y, Z (мм)", `${data.tx.toFixed(2)}, ${data.ty.toFixed(2)}, ${data.tz.toFixed(2)}`, '02');
    addMetric("Обертання X, Y, Z (градуси)", `${data.rx.toFixed(2)}, ${data.ry.toFixed(2)}, ${data.rz.toFixed(2)}`, '02');
    addMetric("Масштаб", data.scale.toFixed(4), '02');
    addMetric("Похибка (Cost)", data.cost.toFixed(4), '02');
    
    // Virtual camera data for 2D mapping
    addMetric("Камера ззаду (віртуальна)", `Pos: (${(data.tx + 450).toFixed(0)}, ${data.ty.toFixed(0)}, ${data.tz.toFixed(0)}), Up: (0, 0, -1)`, '02');
    addMetric("Камера зліва (віртуальна)", `Pos: (${data.tx.toFixed(0)}, ${(data.ty + 450).toFixed(0)}, ${data.tz.toFixed(0)}), Up: (0, 0, -1)`, '02');
    addMetric("Камера зверху (віртуальна)", `Pos: (${data.tx.toFixed(0)}, ${data.ty.toFixed(0)}, ${(data.tz - 450).toFixed(0)}), Up: (0, -1, 0)`, '02');

    const visCont = createVisualizationBlock('vis-02-align', 'Суміщення 3D-моделі з точками обрізки', '02');
    
    // We render the contour and rim points, but skip the full stl_mesh points
    initThreeScene(visCont, [
        { points: data.ls_contour, color: 0x00d2ff, size: 2, isLine: true, name: 'ls_contour' },
        { points: data.contact_points, color: 0xff0000, size: 4, isLine: true, name: 'trim_line' },
        { points: data.stl_rim, color: 0x00ff00, size: 3, isLine: false, name: 'stl_rim' } // Green points, NOT lines
    ], {
        url: `/files/model_3d/helmet_ref.stl`,
        tx: data.tx, ty: data.ty, tz: data.tz,
        rx: data.rx, ry: data.ry, rz: data.rz,
        scale: data.scale,
        color: 0x888888,
        opacity: 1.0,
        side: THREE.DoubleSide,
        onLoad: (container, scene, camera, renderer, controls) => {
            const oldVisibles = [];
            scene.children.forEach(c => {
                oldVisibles.push(c.visible);
                if (c.name !== 'stl_mesh' && c.type !== 'AmbientLight' && c.type !== 'DirectionalLight') {
                    c.visible = false;
                }
            });

            const oldPos = camera.position.clone();
            const oldTarget = controls.target.clone();
            const oldUp = camera.up.clone();

            const cx = container.stlCenter[0];
            const cy = container.stlCenter[1];
            const cz = container.stlCenter[2];

            const views = [
                { name: 'Сзади', pos: [cx + 2500, cy, cz], up: [0, 0, -1] },
                { name: 'Слева', pos: [cx, cy + 1650, cz], up: [0, 0, -1] },
                { name: 'Сверху', pos: [cx, cy, cz + 2000], up: [0, 1, 0] }
            ];

            const panel = document.createElement('div');
            panel.className = 'vis-panel';
            panel.innerHTML = `<h3>Скріншоти 3D моделі</h3><div style="display:flex; justify-content:space-around;"></div>`;
            const row = panel.querySelector('div');

            const panelMasks = document.createElement('div');
            panelMasks.className = 'vis-panel';
            panelMasks.innerHTML = `<h3>Маски 3D моделі</h3><div style="display:flex; justify-content:space-around;"></div>`;
            const rowMasks = panelMasks.querySelector('div');

            const oldBg = scene.background;
            scene.background = null;
            renderer.setClearColor(0x000000, 0);
            
            // Temporarily set high resolution for screenshots (match 4096x3000 photos exactly)
            const renderWidth = 4096;
            const renderHeight = 3000;
            const oldWidth = container.clientWidth;
            const oldHeight = Math.round(oldWidth / (4096/3000));
            
            renderer.setSize(renderWidth, renderHeight);
            camera.aspect = renderWidth / renderHeight;
            camera.updateProjectionMatrix();

            views.forEach(v => {
                let look_at = [cx, cy, cz];
                let f_px = null;
                if (step00GlobalData && step00GlobalData[v.name]) {
                    f_px = step00GlobalData[v.name].f_px;
                    const dx = step00GlobalData[v.name].look_at_offset_x_mm;
                    const dy = step00GlobalData[v.name].look_at_offset_y_mm;
                    if (v.name === 'Сзади') {
                        look_at[1] -= dx; look_at[2] += dy;
                    } else if (v.name === 'Слева') {
                        look_at[0] += dx; look_at[2] += dy;
                    } else if (v.name === 'Сверху') {
                        look_at[0] -= dx; look_at[1] -= dy;
                    }
                }
                
                container.setCameraView(v.pos, look_at, v.up, f_px);
                renderer.render(scene, camera);
                const dataURL = renderer.domElement.toDataURL('image/png');
                
                const canvas = document.createElement('canvas');
                canvas.width = renderWidth;
                canvas.height = renderHeight;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(renderer.domElement, 0, 0);
                const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                const px = imgData.data;
                for (let i = 0; i < px.length; i += 4) {
                    if (px[i+3] > 0) {
                        px[i] = 255; px[i+1] = 255; px[i+2] = 255; px[i+3] = 255;
                    }
                }
                ctx.putImageData(imgData, 0, 0);
                const maskURL = canvas.toDataURL('image/png');

                fetch('/api/save_screenshot', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: currentSessionId, filename: `model_shot_${v.name}.png`, image_data: dataURL })
                });
                
                fetch('/api/save_screenshot', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: currentSessionId, filename: `model_mask_${v.name}.png`, image_data: maskURL })
                });

                addMetric(`Скріншот (${v.name})`, `/files/${currentSessionId}/model_shot_${v.name}.png`, '02');
                addMetric(`Маска (${v.name})`, `/files/${currentSessionId}/model_mask_${v.name}.png`, '02');
                
                // Add screenshot to panel
                const imgCont = document.createElement('div');
                imgCont.style.width = '30%';
                imgCont.style.textAlign = 'center';
                
                const img = document.createElement('img');
                img.src = dataURL;
                img.style.width = '100%';
                img.style.marginBottom = '5px';
                img.style.background = '#000';
                
                const label = document.createElement('div');
                label.innerText = v.name;
                label.style.fontSize = '0.9rem';
                label.style.color = '#ccc';
                
                imgCont.appendChild(img);
                imgCont.appendChild(label);
                row.appendChild(imgCont);

                // Add mask to panel
                const maskCont = document.createElement('div');
                maskCont.style.width = '30%';
                maskCont.style.textAlign = 'center';
                
                const maskImg = document.createElement('img');
                maskImg.src = maskURL;
                maskImg.style.width = '100%';
                maskImg.style.marginBottom = '5px';
                maskImg.style.background = '#222';
                
                const maskLabel = document.createElement('div');
                maskLabel.innerText = v.name;
                maskLabel.style.fontSize = '0.9rem';
                maskLabel.style.color = '#ccc';
                
                maskCont.appendChild(maskImg);
                maskCont.appendChild(maskLabel);
                rowMasks.appendChild(maskCont);
            });

            // Restore renderer size for the UI
            renderer.setSize(oldWidth, oldHeight);
            camera.aspect = oldWidth / oldHeight;
            camera.updateProjectionMatrix();

            scene.background = oldBg;
            
            scene.children.forEach((c, i) => {
                c.visible = oldVisibles[i];
            });

            container.setCameraView([cx + 450, cy, cz], [cx, cy, cz], [0, 0, -1]);
            renderer.render(scene, camera);

            // Append panels AFTER the vis-02-align block
            container.parentNode.insertBefore(panelMasks, container.nextSibling);
            container.parentNode.insertBefore(panel, container.nextSibling);
        }
    });
    
    const toggleRow = document.createElement('div');
    toggleRow.style.display = 'flex';
    toggleRow.style.gap = '15px';
    toggleRow.style.marginBottom = '10px';
    toggleRow.style.justifyContent = 'center';
    toggleRow.style.fontSize = '0.9rem';

    // LS Contour
    const lblLs = document.createElement('label');
    lblLs.style.cursor = 'pointer';
    lblLs.innerHTML = `<input type="checkbox" checked> LS точки`;
    lblLs.querySelector('input').onchange = (e) => {
        if (visCont.toggleObject) visCont.toggleObject('ls_contour', e.target.checked);
    };
    toggleRow.appendChild(lblLs);

    // Trim Line
    const lblTrim = document.createElement('label');
    lblTrim.style.cursor = 'pointer';
    lblTrim.innerHTML = `<input type="checkbox" checked> Лінія обрізки`;
    lblTrim.querySelector('input').onchange = (e) => {
        if (visCont.toggleObject) visCont.toggleObject('trim_line', e.target.checked);
    };
    toggleRow.appendChild(lblTrim);

    // STL Rim
    const lblRim = document.createElement('label');
    lblRim.style.cursor = 'pointer';
    lblRim.innerHTML = `<input type="checkbox" checked> STL край`;
    lblRim.querySelector('input').onchange = (e) => {
        if (visCont.toggleObject) visCont.toggleObject('stl_rim', e.target.checked);
    };
    toggleRow.appendChild(lblRim);
    
    // STL Mesh (Helmet)
    const lblMesh = document.createElement('label');
    lblMesh.style.cursor = 'pointer';
    lblMesh.innerHTML = `<input type="checkbox" checked> 3D Шолом`;
    lblMesh.querySelector('input').onchange = (e) => {
        if (visCont.toggleObject) visCont.toggleObject('stl_mesh', e.target.checked);
    };
    toggleRow.appendChild(lblMesh);

    visCont.insertBefore(toggleRow, visCont.children[1]); // Insert under the title
    
    const btnRow = document.createElement('div');
    btnRow.style.display = 'flex';
    btnRow.style.gap = '10px';
    btnRow.style.marginBottom = '10px';
    btnRow.style.justifyContent = 'center';
    
    const cx = visCont.stlCenter ? visCont.stlCenter[0] : data.tx;
    const cy = visCont.stlCenter ? visCont.stlCenter[1] : data.ty;
    const cz = visCont.stlCenter ? visCont.stlCenter[2] : data.tz;
    
    function getOptics(name, cx, cy, cz) {
        let look_at = [cx, cy, cz];
        let f_px = null;
        if (step00GlobalData && step00GlobalData[name]) {
            f_px = step00GlobalData[name].f_px;
            const dx = step00GlobalData[name].look_at_offset_x_mm;
            const dy = step00GlobalData[name].look_at_offset_y_mm;
            if (name === 'Сзади') {
                look_at[1] -= dx;
                look_at[2] += dy;
            } else if (name === 'Слева') {
                look_at[0] += dx;
                look_at[2] += dy;
            } else if (name === 'Сверху') {
                look_at[0] -= dx;
                look_at[1] -= dy;
            }
        }
        return { look_at, f_px };
    }

    // Сзади (Back)
    const btnBack = document.createElement('button');
    btnBack.innerText = 'Сзади (Back)';
    btnBack.onclick = () => {
        const opt = getOptics('Сзади', cx, cy, cz);
        if (visCont.setCameraView) visCont.setCameraView([cx + 2500, cy, cz], opt.look_at, [0, 0, -1], opt.f_px);
    };
    btnRow.appendChild(btnBack);
    
    // Слева (Left)
    const btnLeft = document.createElement('button');
    btnLeft.innerText = 'Слева (Left)';
    btnLeft.onclick = () => {
        const opt = getOptics('Слева', cx, cy, cz);
        if (visCont.setCameraView) visCont.setCameraView([cx, cy + 1650, cz], opt.look_at, [0, 0, -1], opt.f_px);
    };
    btnRow.appendChild(btnLeft);
    
    // Сверху (Top)
    const btnTop = document.createElement('button');
    btnTop.innerText = 'Сверху (Top)';
    btnTop.onclick = () => {
        const opt = getOptics('Сверху', cx, cy, cz);
        if (visCont.setCameraView) visCont.setCameraView([cx, cy, cz + 2000], opt.look_at, [0, 1, 0], opt.f_px);
    };
    btnRow.appendChild(btnTop);
    
    visCont.insertBefore(btnRow, visCont.children[1]); // Insert under the title
    
    // Default to Back view
    btnBack.click();
}

// --- STEP 3 ---
async function runStep03() {
    if (!currentSessionId) return;
    
    let btn = document.getElementById('btn-run-03');
    if (!btn) btn = document.getElementById('btn-step03');
    if (btn.classList.contains('recalc-btn')) {
        clearStepData('03');
    }
    btn.disabled = true;
    btn.innerText = "Обробка...";
    
    await fetch(`/api/step03?session_id=${currentSessionId}&action=start`);
    
    let poll = setInterval(async () => {
        const res = await fetch(`/api/step03?session_id=${currentSessionId}&action=poll`);
        const result = await res.json();
        
        if (result.status === 'done') {
            clearInterval(poll);
            btn.innerText = "Виконано";
            btn.style.background = "#4CAF50";
            handleStep03Result(result.data);
            markStepDone('03');
        } else if (result.status === 'error') {
            clearInterval(poll);
            btn.innerText = "Помилка";
            btn.style.background = "#f44336";
            alert("Помилка: " + result.message);
        }
    }, 1000);
}

function handleStep03Result(data) {
    addMetricGroup('Етап 3: Сегментація зображень', '03');
    const visZone = document.getElementById('visualizations');
    
    const panelOriginal = document.createElement('div');
    panelOriginal.className = 'vis-panel';
    panelOriginal.innerHTML = `<h3>Оригінальні фото еталона</h3><div style="display:flex; justify-content:space-around;"></div>`;
    const rowOriginal = panelOriginal.querySelector('div');
    
    const panelCropped = document.createElement('div');
    panelCropped.className = 'vis-panel';
    panelCropped.innerHTML = `<h3>Обрізані фото еталона</h3><div style="display:flex; justify-content:space-around;"></div>`;
    const rowCropped = panelCropped.querySelector('div');
    
    const panelMasks = document.createElement('div');
    panelMasks.className = 'vis-panel';
    panelMasks.innerHTML = `<h3>Однотонні маски еталона</h3><div style="display:flex; justify-content:space-around;"></div>`;
    const rowMasks = panelMasks.querySelector('div');
    
    const panelOverlay = document.createElement('div');
    panelOverlay.className = 'vis-panel';
    panelOverlay.innerHTML = `<h3>Накладення маски на оригінал</h3><div style="display:flex; justify-content:space-around;"></div>`;
    const rowOverlay = panelOverlay.querySelector('div');
    
    for (const [cam, info] of Object.entries(data)) {
        addMetric(`Маска ${cam} (напівпрозора)`, info.rgba_path, '03');
        addMetric(`Маска ${cam} (суцільна)`, info.solid_path, '03');
        
        // Add to original UI
        const img0 = document.createElement('img');
        img0.src = `/input/photos_etalon/${cam}.png`;
        img0.style.width = "30%";
        img0.title = cam;
        rowOriginal.appendChild(img0);
        
        // Add to cropped UI
        const img1 = document.createElement('img');
        img1.src = `/files/${currentSessionId}/${info.rgba_file}?t=${Date.now()}`;
        img1.style.width = "30%";
        img1.title = cam;
        rowCropped.appendChild(img1);
        
        // Add to masks UI
        const img2 = document.createElement('img');
        img2.src = `/files/${currentSessionId}/${info.solid_file}?t=${Date.now()}`;
        img2.style.width = "30%";
        img2.title = cam;
        rowMasks.appendChild(img2);
        
        // Add to overlay UI
        const overlayCont = document.createElement('div');
        overlayCont.style.position = 'relative';
        overlayCont.style.width = '30%';
        overlayCont.title = cam;
        
        const imgBg = document.createElement('img');
        imgBg.src = `/input/photos_etalon/${cam}.png`;
        imgBg.style.width = '100%';
        imgBg.style.display = 'block';
        
        const imgFg = document.createElement('img');
        imgFg.src = `/files/${currentSessionId}/${info.solid_file}?t=${Date.now()}`;
        imgFg.style.position = 'absolute';
        imgFg.style.top = '0';
        imgFg.style.left = '0';
        imgFg.style.width = '100%';
        imgFg.style.height = '100%';
        imgFg.style.opacity = '0.5';
        
        overlayCont.appendChild(imgBg);
        overlayCont.appendChild(imgFg);
        rowOverlay.appendChild(overlayCont);
    }
    
    visZone.appendChild(panelOriginal);
    visZone.appendChild(panelCropped);
    visZone.appendChild(panelMasks);
    visZone.appendChild(panelOverlay);
    
    // Enable Step 4
    document.getElementById('btn-run-04').disabled = false;
    document.getElementById('card-04').classList.add('active');
}

async function runStep04() {
    const btn = document.getElementById('btn-run-04');
    if (btn.classList.contains('recalc-btn')) {
        clearStepData('04');
    }
    btn.innerText = 'Обробка...';
    btn.disabled = true;

    try {
        const res = await fetch(`/api/step04?session_id=${currentSessionId}&action=start`);
        const data = await res.json();
        pollStep04();
    } catch (e) {
        console.error(e);
        btn.innerText = 'Помилка';
        btn.style.background = '#d9534f';
    }
}

async function pollStep04() {
    try {
        const res = await fetch(`/api/step04?session_id=${currentSessionId}&action=poll`);
        const data = await res.json();
        
        if (data.status === 'done') {
            const btn = document.getElementById('btn-run-04');
            btn.innerText = 'Виконано';
            btn.style.background = '#5cb85c';
            handleStep04Result(data.data || data);
            markStepDone('04');
        } else if (data.status === 'error') {
            const btn = document.getElementById('btn-run-04');
            btn.innerText = 'Помилка';
            btn.style.background = '#d9534f';
            console.error(data.message);
        } else {
            setTimeout(pollStep04, 1000);
        }
    } catch (e) {
        console.error("Poll Step 4 Error:", e);
        const btn = document.getElementById('btn-run-04');
        btn.innerText = 'Помилка';
        btn.style.background = '#d9534f';
    }
}

function handleStep04Result(data) {
    addMetricGroup('Етап 4: Суміщення масок (2D Fit)', '04');
    const visZone = document.getElementById('visualizations');
    
    const panel = document.createElement('div');
    panel.className = 'vis-panel';
    panel.setAttribute('data-step', '04');
    panel.innerHTML = `<h3>Накладення масок 3D-моделі на маски еталона (2D Fit)</h3><div style="display:flex; justify-content:space-around;"></div>`;
    const row = panel.querySelector('div');
    
    const order = ['Сзади', 'Слева', 'Сверху'];
    for (const cam of order) {
        if (!data[cam]) continue;
        const info = data[cam];
        addMetric(`Зсув ${cam} (X, Y)`, `dx: ${info.du.toFixed(2)}px, dy: ${info.dv.toFixed(2)}px`, '04');
        addMetric(`Масштаб ${cam}`, info.scale.toFixed(3), '04');
        addMetric(`Поворот ${cam}`, `${info.rot.toFixed(2)}°`, '04');
        
        const cont = document.createElement('div');
        cont.style.width = '30%';
        cont.style.textAlign = 'center';
        
        const img = document.createElement('img');
        img.src = `${info.overlap_path}?t=${Date.now()}`;
        img.style.width = '100%';
        img.style.marginBottom = '5px';
        img.style.background = '#222';
        img.style.cursor = 'pointer';
        
        const captionText = `${cam} | Зсув: dx=${info.du.toFixed(1)} dy=${info.dv.toFixed(1)} | Масштаб: ${info.scale.toFixed(3)} | Поворот: ${info.rot.toFixed(1)}°`;
        
        img.onclick = () => {
            openModal(img.src, captionText);
        };
        
        const label = document.createElement('div');
        label.innerText = cam;
        label.style.fontSize = '0.9rem';
        label.style.color = '#ccc';
        
        cont.appendChild(img);
        cont.appendChild(label);
        row.appendChild(cont);
    }
    
    visZone.appendChild(panel);
}

async function runStep05() {
    if (!currentSessionId) return;
    
    let btn = document.getElementById('btn-run-05');
    if (!btn) btn = document.getElementById('btn-step05');
    if (btn && btn.classList.contains('recalc-btn')) {
        clearStepData('05');
    }
    if (btn) {
        btn.disabled = true;
        btn.innerText = "Обробка...";
    }
    
    await fetch(`/api/step05?session_id=${currentSessionId}&action=start`);
    
    let poll = setInterval(async () => {
        const res = await fetch(`/api/step05?session_id=${currentSessionId}&action=poll`);
        const result = await res.json();
        
        if (result.status === 'done') {
            clearInterval(poll);
            if (btn) {
                btn.innerText = "Виконано";
                btn.style.background = "#4CAF50";
            }
            handleStep05Result(result.data);
            markStepDone('05');
        } else if (result.status === 'error') {
            clearInterval(poll);
            if (btn) {
                btn.innerText = "Помилка";
                btn.style.background = "#f44336";
            }
            alert("Помилка: " + result.message);
        }
    }, 1000);
}

function handleStep05Result(data) {
    addMetricGroup('Етап 5: Сегментація поточного шолома', '05');
    const visZone = document.getElementById('visualizations');
    
    const panelOriginal = document.createElement('div');
    panelOriginal.className = 'vis-panel';
    panelOriginal.setAttribute('data-step', '05');
    panelOriginal.innerHTML = `<h3>Оригінальні фото поточного шолома</h3><div style="display:flex; justify-content:space-around;"></div>`;
    const rowOriginal = panelOriginal.querySelector('div');
    
    const panelCropped = document.createElement('div');
    panelCropped.className = 'vis-panel';
    panelCropped.setAttribute('data-step', '05');
    panelCropped.innerHTML = `<h3>Обрізані фото поточного шолома</h3><div style="display:flex; justify-content:space-around;"></div>`;
    const rowCropped = panelCropped.querySelector('div');
    
    const panelMasks = document.createElement('div');
    panelMasks.className = 'vis-panel';
    panelMasks.setAttribute('data-step', '05');
    panelMasks.innerHTML = `<h3>Однотонні маски поточного шолома</h3><div style="display:flex; justify-content:space-around;"></div>`;
    const rowMasks = panelMasks.querySelector('div');
    
    const panelOverlay = document.createElement('div');
    panelOverlay.className = 'vis-panel';
    panelOverlay.setAttribute('data-step', '05');
    panelOverlay.innerHTML = `<h3>Накладення маски на поточний шолом</h3><div style="display:flex; justify-content:space-around;"></div>`;
    const rowOverlay = panelOverlay.querySelector('div');
    
    const cams = [
        { id: "back", label: "Сзади" },
        { id: "left", label: "Слева" },
        { id: "top", label: "Сверху" }
    ];
    
    cams.forEach(cam => {
        if (data[cam.id]) {
            const info = data[cam.id];
            
            addMetric(`${cam.label} вихідне фото`, info.source_path, '05');
            addMetric(`${cam.label} маска (солід)`, info.solid_path, '05');
            addMetric(`${cam.label} вирізане фото`, info.rgba_path, '05');
            
            // Add to original UI
            const img0 = document.createElement('img');
            img0.src = `${info.source_path}?t=${Date.now()}`;
            img0.style.width = "30%";
            img0.title = cam.label;
            img0.style.cursor = 'pointer';
            img0.onclick = () => openModal(img0.src, `${cam.label} (Оригінал)`);
            rowOriginal.appendChild(img0);
            
            // Add to cropped UI
            const img1 = document.createElement('img');
            img1.src = `${info.rgba_path}?t=${Date.now()}`;
            img1.style.width = "30%";
            img1.title = cam.label;
            img1.style.cursor = 'pointer';
            img1.onclick = () => openModal(img1.src, `${cam.label} (Вирізано)`);
            rowCropped.appendChild(img1);
            
            // Add to masks UI
            const img2 = document.createElement('img');
            img2.src = `${info.solid_path}?t=${Date.now()}`;
            img2.style.width = "30%";
            img2.title = cam.label;
            img2.style.cursor = 'pointer';
            img2.onclick = () => openModal(img2.src, `${cam.label} (Маска)`);
            rowMasks.appendChild(img2);
            
            // Add to overlay UI
            const overlayCont = document.createElement('div');
            overlayCont.style.position = 'relative';
            overlayCont.style.width = '30%';
            overlayCont.title = cam.label;
            
            const imgBg = document.createElement('img');
            imgBg.src = `${info.source_path}?t=${Date.now()}`;
            imgBg.style.width = '100%';
            imgBg.style.display = 'block';
            
            const imgFg = document.createElement('img');
            imgFg.src = `${info.solid_path}?t=${Date.now()}`;
            imgFg.style.position = 'absolute';
            imgFg.style.top = '0';
            imgFg.style.left = '0';
            imgFg.style.width = '100%';
            imgFg.style.height = '100%';
            imgFg.style.opacity = '0.5';
            
            overlayCont.appendChild(imgBg);
            overlayCont.appendChild(imgFg);
            rowOverlay.appendChild(overlayCont);
        }
    });
    
    visZone.appendChild(panelOriginal);
    visZone.appendChild(panelCropped);
    visZone.appendChild(panelMasks);
    visZone.appendChild(panelMasks);
    visZone.appendChild(panelOverlay);
}

async function runStep06() {
    if (!currentSessionId) return;
    
    let btn = document.getElementById('btn-run-06');
    if (!btn) btn = document.getElementById('btn-step06');
    if (btn && btn.classList.contains('recalc-btn')) {
        clearStepData('06');
    }
    if (btn) {
        btn.disabled = true;
        btn.innerText = "Обробка...";
    }
    
    await fetch(`/api/step06?session_id=${currentSessionId}&action=start`);
    
    let poll = setInterval(async () => {
        const res = await fetch(`/api/step06?session_id=${currentSessionId}&action=poll`);
        const result = await res.json();
        
        if (result.status === 'done') {
            clearInterval(poll);
            if (btn) {
                btn.innerText = "Виконано";
                btn.style.background = "#4CAF50";
            }
            handleStep06Result(result.data);
            markStepDone('06');
        } else if (result.status === 'error') {
            clearInterval(poll);
            if (btn) {
                btn.innerText = "Помилка";
                btn.style.background = "#f44336";
            }
            alert("Помилка: " + result.message);
        }
    }, 1000);
}

function handleStep06Result(data) {
    addMetricGroup('Етап 6: 3D-Оптимізація', '06');
    const visZone = document.getElementById('visualizations');
    
    if (data.global_3d) {
        const g = data.global_3d;
        addMetric('Глобальний зсув X', `${g.x_mm.toFixed(2)} мм`, '06');
        addMetric('Глобальний зсув Y', `${g.y_mm.toFixed(2)} мм`, '06');
        addMetric('Глобальний зсув Z', `${g.z_mm.toFixed(2)} мм`, '06');
        addMetric('Глобальний Крен (Roll)', `${g.roll_deg.toFixed(2)}°`, '06');
        addMetric('Глобальний Тангаж (Pitch)', `${g.pitch_deg.toFixed(2)}°`, '06');
        addMetric('Глобальне Рискання (Yaw)', `${g.yaw_deg.toFixed(2)}°`, '06');
        addMetric('Глобальний масштаб', `${g.scale.toFixed(3)}`, '06');
    }
    
    const panel = document.createElement('div');
    panel.className = 'vis-panel';
    panel.setAttribute('data-step', '06');
    panel.innerHTML = `<h3>Фінальне 3D-суміщення (Зелений: шолом, Червоний: CAD)</h3><div style="display:flex; justify-content:space-around;"></div>`;
    
    const row = panel.querySelector('div');
    
    const cams = [
        { id: "back", label: "Сзади" },
        { id: "left", label: "Слева" },
        { id: "top", label: "Сверху" }
    ];
    
    cams.forEach(cam => {
        if (data[cam.id]) {
            const info = data[cam.id];
            
            const cont = document.createElement('div');
            cont.style.width = '30%';
            cont.style.textAlign = 'center';
            
            const img = document.createElement('img');
            img.src = `${info.overlap_path}?t=${Date.now()}`;
            img.style.width = '100%';
            img.style.marginBottom = '5px';
            img.style.background = '#222';
            img.style.cursor = 'pointer';
            
            const captionText = `${cam.label} | dx=${info.du.toFixed(1)} dy=${info.dv.toFixed(1)} rot=${info.rot.toFixed(1)}°`;
            
            img.onclick = () => openModal(img.src, captionText);
            
            const label = document.createElement('div');
            label.innerText = cam.label;
            label.style.fontSize = '0.9rem';
            label.style.color = '#ccc';
            
            cont.appendChild(img);
            cont.appendChild(label);
            row.appendChild(cont);
        }
    });
    
    visZone.appendChild(panel);
}

function openModal(src, caption) {
    const modal = document.getElementById('image-modal');
    const modalImg = document.getElementById('modal-img');
    const modalCaption = document.getElementById('modal-caption');
    
    modalImg.src = src;
    modalCaption.innerText = caption;
    modal.classList.add('active');
}

function closeModal() {
    const modal = document.getElementById('image-modal');
    modal.classList.remove('active');
}

let autoRunInterval = null;

async function startAutoRun() {
    if (autoRunInterval) clearInterval(autoRunInterval);
    
    // Disable auto run button
    const autoBtn = document.getElementById('btn-auto-run');
    if (autoBtn) autoBtn.innerText = 'Авто...';
    
    const runNext = async () => {
        if (!currentSessionId) {
            await startSession();
        }
        
        // Are any steps currently running?
        const isRunning = [0,1,2,3,4,5,6].some(i => {
            const btnId = 'btn-run-0' + i;
            const btn = document.getElementById(btnId);
            return btn && btn.innerText.includes('Обробка');
        });
        
        if (isRunning) return; // Wait for current step to finish
        
        // Find next step to run
        for (let i = 0; i <= 6; i++) {
            let btnId = 'btn-run-0' + i;
            let btn = document.getElementById(btnId);
            
            // Fallback for cached old index.html
            if (!btn && i === 3) btn = document.getElementById('btn-step03');
            if (!btn && i === 5) btn = document.getElementById('btn-step05');
            if (!btn && i === 6) btn = document.getElementById('btn-step06');
            
            // We can run it if it's enabled, NOT running, and NOT a recalc button
            if (btn && !btn.disabled && !btn.classList.contains('recalc-btn') && !btn.innerText.includes('Виконано')) {
                btn.click();
                return;
            }
        }
        
        // Check if all done
        const allDone = [0,1,2,3,4,5,6].every(i => {
            let btnId = 'btn-run-0' + i;
            let btn = document.getElementById(btnId);
            if (!btn && i === 3) btn = document.getElementById('btn-step03');
            if (!btn && i === 5) btn = document.getElementById('btn-step05');
            if (!btn && i === 6) btn = document.getElementById('btn-step06');
            return btn && btn.innerText.includes('Виконано');
        });
        
        if (allDone) {
            clearInterval(autoRunInterval);
            autoRunInterval = null;
            if (autoBtn) autoBtn.innerText = 'Запуск сессии (Авто)';
            console.log('Авто-виконання завершено!');
        }
    };
    
    autoRunInterval = setInterval(runNext, 2000);
    runNext();
}
