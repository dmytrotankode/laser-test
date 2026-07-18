let currentSessionId = null;
let stepPollInterval = null;
let step02GlobalData = null;

async function startSession() {
    const res = await fetch('/api/start_session');
    const data = await res.json();
    currentSessionId = data.session_id;
    
    document.getElementById('session-label').innerText = `Сесія: ${currentSessionId}`;
    document.getElementById('session-label').style.color = '#00d2ff';
    
    // Enable Step 1
    document.getElementById('btn-run-01').disabled = false;
    document.getElementById('card-01').classList.add('active');
    
    // Enable Step 2 initially disabled until Step 1 completes
    document.getElementById('btn-run-02').disabled = true;
    document.getElementById('card-02').classList.remove('active');
    
    // Clear zones
    document.getElementById('visualizations').innerHTML = '';
    document.getElementById('metrics-table').innerHTML = '';
}

function addMetricGroup(title) {
    const table = document.getElementById('metrics-table');
    const tr = document.createElement('tr');
    tr.style.backgroundColor = '#1f1f1f';
    tr.innerHTML = `<th colspan="2" style="text-align:center; padding:5px; border-bottom:1px solid #444; color:#00d2ff; font-weight:600;">${title}</th>`;
    table.appendChild(tr);
}

function addMetric(key, value) {
    const table = document.getElementById('metrics-table');
    const tr = document.createElement('tr');
    tr.innerHTML = `<td><strong>${key}</strong></td><td>${value}</td>`;
    table.appendChild(tr);
}

function createVisualizationBlock(id, title) {
    const visZone = document.getElementById('visualizations');
    const panel = document.createElement('div');
    panel.className = 'vis-panel';
    panel.innerHTML = `
        <h3>${title}</h3>
        <div id="${id}" class="canvas-container"></div>
    `;
    visZone.appendChild(panel);
    return document.getElementById(id);
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

    const camera = new THREE.PerspectiveCamera(45, container.clientWidth / 300, 0.1, 10000);
    camera.up.set(0, 0, -1); // Z is down in robot space, so -Z is UP on screen
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, 300);
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
            
            scene.add(mesh);
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

    container.setCameraView = function(pos, look_at, up_vector) {
        camera.position.set(pos[0], pos[1], pos[2]);
        controls.target.set(look_at[0], look_at[1], look_at[2]);
        if (up_vector) {
            camera.up.set(up_vector[0], up_vector[1], up_vector[2]);
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
        camera.position.set(center.x + 800, center.y + 800, center.z - 800);
    } else {
        camera.position.set(800, 800, -800);
    }
    
    controls.update();
    
    function animate() {
        requestAnimationFrame(animate);
        controls.update();
        renderer.render(scene, camera);
    }
    animate();
}

async function runStep01() {
    if (!currentSessionId) return;
    
    const btn = document.getElementById('btn-run-01');
    btn.disabled = true;
    btn.innerText = "Обробка...";
    
    // Start step
    await fetch(`/api/step01?session_id=${currentSessionId}&action=start`);
    
    // Poll
    stepPollInterval = setInterval(async () => {
        const res = await fetch(`/api/step01?session_id=${currentSessionId}&action=poll`);
        const result = await res.json();
        
        if (result.status === 'done') {
            clearInterval(stepPollInterval);
            btn.innerText = "Виконано";
            btn.style.background = "#4CAF50";
            
            // Render UI
            handleStep01Result(result.data);
            
            // Enable Step 2
            document.getElementById('btn-run-02').disabled = false;
            document.getElementById('card-02').classList.add('active');
            
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
    addMetricGroup('Крок 1: Еталон та різак');
    addMetric('Шлях до еталонного LS', data.ls_path);
    addMetric('Кут різака (X/Вниз)', data.tilt_down_deg + " градусів");
    addMetric('Кут різака (Y/Поворот)', data.yaw_ccw_deg + " градусів");
    addMetric("Відступ різака", data.offset_mm + " мм");
    addMetric("Загальна кількість точок (Оригінал)", data.original_points.length);
    addMetric("Точок контуру (Відфільтровано)", data.contour_points.length);
    
    // 2) Visualization 1: Original LS centered
    const visCont = createVisualizationBlock('vis-01-contour', 'Еталонний LS (X, Y, Z)');
    initThreeScene(visCont, [
        { points: data.original_points, color: 0x888888, size: 2, isLine: true }
    ]);
    
    // 3) Visualization 2: LS Contour + Offset Contact Points
    const vis2Cont = createVisualizationBlock('vis-01-offset', 'Лінія обрізки (Contact Points)');
    initThreeScene(vis2Cont, [
        { points: data.contour_points, color: 0x00d2ff, size: 2, isLine: true }, // Cyan for original contour
        { points: data.contact_points, color: 0xff0000, size: 3, isLine: true }  // Red for actual trim line (offset)
    ]);
}

async function runStep02() {
    if (!currentSessionId) return;
    
    const btn = document.getElementById('btn-run-02');
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
    addMetricGroup('Крок 2: 3D суміщення');
    addMetric("Шлях до 3D моделі", data.model_path);
    addMetric("Зсув X, Y, Z (мм)", `${data.tx.toFixed(2)}, ${data.ty.toFixed(2)}, ${data.tz.toFixed(2)}`);
    addMetric("Поворот X, Y, Z (град)", `${data.rx.toFixed(2)}, ${data.ry.toFixed(2)}, ${data.rz.toFixed(2)}`);
    addMetric("Масштаб", data.scale.toFixed(4));
    addMetric("Відхилення (Cost)", data.cost.toFixed(4));
    
    step02GlobalData = data; // Save for later steps!
    
    const visCont = createVisualizationBlock('vis-02-align', 'Суміщення 3D-моделі з точками обрізки');
    
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
        side: THREE.DoubleSide
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
    
    // Сзади (Back)
    const btnBack = document.createElement('button');
    btnBack.innerText = 'Сзади (Back)';
    btnBack.onclick = () => {
        // Assuming +X is left
        if (visCont.setCameraView) visCont.setCameraView([data.tx + 800, data.ty, data.tz], [data.tx, data.ty, data.tz], [0, 0, -1]);
    };
    btnRow.appendChild(btnBack);
    
    // Слева (Left)
    const btnLeft = document.createElement('button');
    btnLeft.innerText = 'Слева (Left)';
    btnLeft.onclick = () => {
        // If Y is forward, then back is +Y or -Y? Assuming +Y is back.
        if (visCont.setCameraView) visCont.setCameraView([data.tx, data.ty + 800, data.tz], [data.tx, data.ty, data.tz], [0, 0, -1]);
    };
    btnRow.appendChild(btnLeft);
    
    // Сверху (Top)
    const btnTop = document.createElement('button');
    btnTop.innerText = 'Сверху (Top)';
    btnTop.onclick = () => {
        if (visCont.setCameraView) visCont.setCameraView([data.tx, data.ty, data.tz - 800], [data.tx, data.ty, data.tz], [0, -1, 0]);
    };
    btnRow.appendChild(btnTop);
    
    visCont.insertBefore(btnRow, visCont.children[1]); // Insert under the title
    
    // Default to Back view
    btnBack.click();
    
    // Enable Step 3
    document.getElementById('btn-step03').disabled = false;
    document.getElementById('card-step03').classList.add('active');
}

// --- STEP 3 ---
async function runStep03() {
    if (!currentSessionId) return;
    
    const btn = document.getElementById('btn-step03');
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
            // Last step in service 5054
        } else if (result.status === 'error') {
            clearInterval(poll);
            btn.innerText = "Помилка";
            btn.style.background = "#f44336";
            alert("Помилка: " + result.message);
        }
    }, 1000);
}

function handleStep03Result(data) {
    addMetricGroup('Крок 3: Сегментація фотографій');
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
        addMetric(`Фото ${cam} (Обрізане)`, info.rgba_path);
        addMetric(`Фото ${cam} (Маска)`, info.solid_path);
        
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
        const isRunning = [1,2,3].some(i => {
            const btn = document.getElementById(i < 3 ? 'btn-run-0' + i : 'btn-step0' + i);
            return btn && btn.innerText.includes('Обробка');
        });
        
        if (isRunning) return; // Wait for current step to finish
        
        // Find next step to run
        for (let i = 1; i <= 3; i++) {
            const btn = document.getElementById(i < 3 ? 'btn-run-0' + i : 'btn-step0' + i);
            if (btn && !btn.disabled && btn.innerText.includes('Виконати')) {
                btn.click();
                return;
            }
        }
        
        // Check if all done
        const allDone = [1,2,3].every(i => {
            const btn = document.getElementById(i < 3 ? 'btn-run-0' + i : 'btn-step0' + i);
            return btn && (btn.innerText.includes('Виконано') || btn.innerText.includes('Готово'));
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
