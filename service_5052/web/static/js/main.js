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

function initThreeScene(container, pointsArrays) {
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1e1e1e);
    
    // Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 10000);
    
    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    container.appendChild(renderer.domElement);
    
    // Controls
    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    
    // Add points
    // pointsArrays is an array of objects: { points: [...], color: 0xff0000, size: 2 }
    
    let center = new THREE.Vector3(0, 0, 0);
    let totalPoints = 0;
    
    pointsArrays.forEach(pa => {
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
        }
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        const material = new THREE.PointsMaterial({ color: pa.color, size: pa.size || 2 });
        const pointsObj = new THREE.Points(geometry, material);
        scene.add(pointsObj);
        
        // Add line connecting points
        const lineMat = new THREE.LineBasicMaterial({ color: pa.color, transparent: true, opacity: 0.5 });
        const lineObj = new THREE.Line(geometry, lineMat);
        scene.add(lineObj);
    });
    
    if (totalPoints > 0) {
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
    const vis1Cont = createVisualizationBlock('vis-01-original', 'Еталонний LS (Оригінал)');
    initThreeScene(vis1Cont, [
        { points: data.original_points, color: 0x888888, size: 2 }
    ]);
    
    // 3) Visualization 2: LS Contour + Offset Contact Points
    const vis2Cont = createVisualizationBlock('vis-01-offset', 'Лінія обрізки (Contact Points)');
    initThreeScene(vis2Cont, [
        { points: data.contour_points, color: 0x00d2ff, size: 2 }, // Cyan for original contour
        { points: data.contact_points, color: 0xff0000, size: 3 }  // Red for actual trim line (offset)
    ]);
}
