let currentSessionId = null;
let stepPollInterval = null;

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

function initThreeScene(container, pointSets, stlOptions = null) {
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x222222);
    
    // Add ambient light
    const ambientLight = new THREE.AmbientLight(0x404040); // soft white light
    scene.add(ambientLight);
    
    // Add directional light for the STL
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
    directionalLight.position.set(1, 1, 1).normalize();
    scene.add(directionalLight);

    const camera = new THREE.PerspectiveCamera(45, container.clientWidth / 300, 0.1, 10000);
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
            scene.add(lineObj);
        } else {
            const material = new THREE.PointsMaterial({ color: pa.color, size: pa.size || 2 });
            const pointsObj = new THREE.Points(geometry, material);
            scene.add(pointsObj);
        }
    });

    if (stlOptions) {
        const loader = new THREE.STLLoader();
        loader.load(stlOptions.url, function (geom) {
            const mat = new THREE.MeshPhongMaterial({ color: stlOptions.color || 0x888888, specular: 0x111111, shininess: 50, transparent: true, opacity: stlOptions.opacity || 0.9 });
            const mesh = new THREE.Mesh(geom, mat);
            
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

    if (allPoints.length > 0) {
        center.divideScalar(totalPoints);
        controls.target.copy(center);
        camera.position.set(center.x, center.y - 400, center.z + 200);
    } else {
        camera.position.set(0, -400, 200);
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
    // 1) Write paths and metrics
    addMetric("Шлях до еталонного LS", data.ls_path);
    addMetric("Кут різака (X/Вниз)", data.tilt_down_deg + " градусів");
    addMetric("Кут різака (Y/Поворот)", data.yaw_ccw_deg + " градусів");
    addMetric("Відступ різака", data.offset_mm + " мм");
    addMetric("Загальна кількість точок (Оригінал)", data.original_points.length);
    addMetric("Точок контуру (Відфільтровано)", data.contour_points.length);
    
    // 2) Visualization 1: Original LS centered
    const visCont = createVisualizationBlock('vis-01-contour', 'Еталонний LS (X, Y, Z)');
    initThreeScene(visCont, [
        { points: data.contour_points, color: 0x00d2ff, size: 2, isLine: true }
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
    addMetric("Шлях до 3D моделі", data.model_path);
    addMetric("Зсув X, Y, Z (мм)", `${data.tx.toFixed(2)}, ${data.ty.toFixed(2)}, ${data.tz.toFixed(2)}`);
    addMetric("Поворот X, Y, Z (град)", `${data.rx.toFixed(2)}, ${data.ry.toFixed(2)}, ${data.rz.toFixed(2)}`);
    addMetric("Масштаб", data.scale.toFixed(4));
    addMetric("Відхилення (Cost)", data.cost.toFixed(4));
    
    const visCont = createVisualizationBlock('vis-02-align', 'Суміщення 3D-моделі з точками обрізки');
    
    // We render the contour and rim points, but skip the full stl_mesh points
    initThreeScene(visCont, [
        { points: data.ls_contour, color: 0x00d2ff, size: 2, isLine: true },
        { points: data.contact_points, color: 0xff0000, size: 4, isLine: true },
        { points: data.stl_rim, color: 0x00ff00, size: 3, isLine: false } // Green points, NOT lines
    ], {
        url: `/files/model_3d/helmet_ref.stl`,
        tx: data.tx, ty: data.ty, tz: data.tz,
        rx: data.rx, ry: data.ry, rz: data.rz,
        scale: data.scale,
        color: 0x888888,
        opacity: 0.9 // Made it more opaque
    });
}
