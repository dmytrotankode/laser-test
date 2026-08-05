let currentSessionId = null;
let pollingIntervals = {};

window.addEventListener('DOMContentLoaded', () => {
    fetch('/api/latest_session')
        .then(r => r.json())
        .then(d => {
            if (d.session_id) {
                setSession(d.session_id);
            }
        })
        .catch(e => console.error(e));
});

function startNewSession() {
    const sel = document.getElementById('variant-select');
    const val = sel ? sel.value : 'default';
    fetch(`/api/start_session?variant=${val}`)
        .then(r => r.json())
        .then(d => {
            setSession(d.session_id);
            alert("Створено нову сесію: " + d.session_id + " (Варіант: " + val + ")");
        });
}

function setSession(sid) {
    currentSessionId = sid;
    document.getElementById('current-session-display').innerText = "Сесія: " + sid;
    // Fetch current variant for session
    fetch(`/api/get_variant?session_id=${sid}`)
        .then(r => r.json())
        .then(d => {
            const sel = document.getElementById('variant-select');
            if (sel && d.variant) sel.value = d.variant;
        })
        .catch(e => console.error(e));
    // Reset statuses
    for (let i = 1; i <= 5; i++) {
        updateStatusBadge(i, 'idle', 'Очікування');
        document.getElementById(`vis-step${i}`).innerHTML = `<span style="color:var(--text-muted);">Очікування виконання етапу</span>`;
    }
}

function onVariantChange() {
    const val = document.getElementById('variant-select').value;
    if (!currentSessionId) {
        startNewSession();
        return;
    }
    fetch('/api/set_variant', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: currentSessionId, variant: val })
    })
    .then(r => r.json())
    .then(d => {
        alert("Варіант для сесії " + currentSessionId + " змінено на: " + d.variant + "\nТепер натисніть 'Виконати' в Етапах 3, 4 та 5!");
    });
}

function updateStatusBadge(stepNum, statusClass, text) {
    const badge = document.getElementById(`status-step${stepNum}`);
    if (!badge) return;
    badge.className = `status-badge status-${statusClass}`;
    badge.innerText = text;
}

function runStep(stepNum) {
    if (!currentSessionId) {
        alert("Спочатку почніть або оберіть сесію!");
        return;
    }
    const stepStr = `step0${stepNum}`;
    updateStatusBadge(stepNum, 'running', 'Виконується...');
    
    if (pollingIntervals[stepNum]) clearInterval(pollingIntervals[stepNum]);
    
    fetch(`/api/${stepStr}?session_id=${currentSessionId}&action=start`)
        .then(r => r.json())
        .then(d => {
            if (d.status === 'started') {
                pollingIntervals[stepNum] = setInterval(() => pollStep(stepNum), 1000);
            } else {
                updateStatusBadge(stepNum, 'idle', 'Помилка старту');
            }
        })
        .catch(e => {
            updateStatusBadge(stepNum, 'idle', 'Помилка запиту');
            console.error(e);
        });
}

function pollStep(stepNum) {
    const stepStr = `step0${stepNum}`;
    fetch(`/api/${stepStr}?session_id=${currentSessionId}`)
        .then(r => r.json())
        .then(d => {
            if (d.status === 'done') {
                clearInterval(pollingIntervals[stepNum]);
                updateStatusBadge(stepNum, 'done', 'Готово ✓');
                renderStepResult(stepNum, d.data);
            } else if (d.status === 'error') {
                clearInterval(pollingIntervals[stepNum]);
                updateStatusBadge(stepNum, 'idle', 'Помилка');
                alert(`Помилка в Етапі ${stepNum}:\n` + d.message);
            }
        })
        .catch(e => console.error(e));
}

function renderStepResult(stepNum, data) {
    const visContainer = document.getElementById(`vis-step${stepNum}`);
    visContainer.innerHTML = "";
    
    if (stepNum >= 1 && stepNum <= 4) {
        if (data.vis_image) {
            const img = document.createElement('img');
            img.src = data.vis_image + "?t=" + new Date().getTime();
            img.className = "vis-img";
            visContainer.appendChild(img);
        }
        if (data.caption) {
            const cap = document.createElement('div');
            cap.className = "vis-caption";
            cap.innerHTML = `💡 <b>Пояснення візуалізації Етапу ${stepNum}:</b><br>${data.caption}`;
            visContainer.appendChild(cap);
        }
    } else if (stepNum === 5) {
        renderStep5Scene(visContainer, data);
    }
}

function renderStep5Scene(container, data) {
    // Create explanatory caption at top
    if (data.caption) {
        const cap = document.createElement('div');
        cap.className = "vis-caption";
        cap.style.marginBottom = "15px";
        cap.innerHTML = `💡 <b>Фінальна 3D-сцена Етапу 5:</b><br>${data.caption}`;
        container.appendChild(cap);
    }
    
    // Create download button for .ls file
    if (data.current_ls_path) {
        const dlBtn = document.createElement('a');
        dlBtn.href = data.current_ls_path;
        dlBtn.download = data.current_ls_file || 'current_helmet.ls';
        dlBtn.innerHTML = "⬇️ Завантажити фінальний файл для робота (" + (data.current_ls_file || "програма") + ")";
        dlBtn.style.display = "inline-block";
        dlBtn.style.padding = "12px 25px";
        dlBtn.style.background = "#10b981";
        dlBtn.style.color = "#fff";
        dlBtn.style.textDecoration = "none";
        dlBtn.style.borderRadius = "8px";
        dlBtn.style.fontWeight = "bold";
        dlBtn.style.boxShadow = "0 4px 12px rgba(16,185,129,0.4)";
        dlBtn.style.marginBottom = "20px";
        container.appendChild(dlBtn);
    }
    
    // Create legend boxes grouped by pairs (helmet + line)
    const legend = document.createElement('div');
    legend.style.display = "flex";
    legend.style.flexWrap = "wrap";
    legend.style.gap = "15px";
    legend.style.marginBottom = "15px";

    const groups = [
        {
            title: "1️⃣ Еталон (CAD)",
            color: "#ef4444",
            items: [
                { name: 'etalon', label: '🟥 Еталонний шолом (Червоний)', color: '#ef4444' },
                { name: 'etalon_ls', label: '🔷 Еталонна лінія LS (Синя - CAD)', color: '#00ffff' }
            ]
        },
        {
            title: "2️⃣ Наш розрахунок з фото",
            color: "#10b981",
            items: [
                { name: 'current', label: '🟩 Поточний шолом (Зелений - зсунутий)', color: '#10b981' },
                { name: 'laser', label: '🤍 Розрахований LS (Білий - розрахунок)', color: '#ffffff' }
            ]
        }
    ];
    if (data.ground_truth_points && data.ground_truth_points.length > 0) {
        groups.push({
            title: "3️⃣ Факт з верстата (Ground Truth)",
            color: "#f59e0b",
            items: [
                { name: 'ground_truth_helmet', label: '🟨 Фактичний шолом з верстата', color: '#f59e0b' },
                { name: 'ground_truth', label: '🟨 Фактична лінія LS з верстата', color: '#f59e0b' }
            ]
        });
    }
    
    const sceneDiv = document.createElement('div');
    sceneDiv.id = "scene-container";
    container.appendChild(legend);
    container.appendChild(sceneDiv);

    // Init Three.js
    const width = sceneDiv.clientWidth || 800;
    const height = 550;
    
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0f1d);
    
    const camera = new THREE.PerspectiveCamera(45, width / height, 1, 5000);
    camera.position.set(0, -500, 300);
    camera.up.set(0, 0, 1);
    
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    sceneDiv.appendChild(renderer.domElement);
    
    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Infinity;
    controls.minPolarAngle = -Infinity;
    
    // Lights
    scene.add(new THREE.AmbientLight(0xffffff, 0.6));
    const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight1.position.set(200, -200, 300);
    scene.add(dirLight1);
    const dirLight2 = new THREE.DirectionalLight(0xffffff, 0.5);
    dirLight2.position.set(-200, 200, -100);
    scene.add(dirLight2);
    
    // Grid
    const grid = new THREE.GridHelper(600, 30, 0x334155, 0x1e293b);
    grid.rotation.x = Math.PI / 2;
    scene.add(grid);

    const objectsMap = {};
    
    groups.forEach(g => {
        const grpDiv = document.createElement('div');
        grpDiv.style.flex = "1";
        grpDiv.style.minWidth = "250px";
        grpDiv.style.background = "rgba(0,0,0,0.45)";
        grpDiv.style.padding = "10px 15px";
        grpDiv.style.borderRadius = "8px";
        grpDiv.style.border = "1px solid rgba(255,255,255,0.08)";
        grpDiv.style.borderLeft = `4px solid ${g.color}`;
        grpDiv.style.display = "flex";
        grpDiv.style.flexDirection = "column";
        grpDiv.style.gap = "8px";

        const titleDiv = document.createElement('div');
        titleDiv.style.fontWeight = "bold";
        titleDiv.style.fontSize = "0.9rem";
        titleDiv.style.color = "#cbd5e1";
        titleDiv.style.marginBottom = "2px";
        titleDiv.textContent = g.title;
        grpDiv.appendChild(titleDiv);
        
        g.items.forEach(it => {
            const lbl = document.createElement('label');
            lbl.style.cursor = "pointer";
            lbl.style.display = "flex";
            lbl.style.alignItems = "center";
            lbl.style.fontSize = "0.9rem";
            lbl.style.color = "#f8fafc";
            
            const cb = document.createElement('input');
            cb.type = "checkbox";
            cb.checked = true;
            cb.style.marginRight = "8px";
            cb.onchange = (e) => {
                if (objectsMap[it.name]) objectsMap[it.name].visible = e.target.checked;
            };
            
            lbl.appendChild(cb);
            lbl.appendChild(document.createTextNode(it.label));
            grpDiv.appendChild(lbl);
        });

        legend.appendChild(grpDiv);
    });
    
    // Load STL & apply positioning
    const loader = new THREE.STLLoader();
    const stlUrl = "/files/model_3d/helmet_ref.stl";
    
    loader.load(stlUrl, (geometry) => {
        geometry.computeVertexNormals();
        
        const s2 = data.step02_data || {};
        const d = data.delta_3d || { x_mm:0, y_mm:0, z_mm:0, roll_deg:0, pitch_deg:0, yaw_deg:0 };
        
        const tx = s2.tx !== undefined && s2.tx !== null ? s2.tx : 1170.98;
        const ty = s2.ty !== undefined && s2.ty !== null ? s2.ty : 785.15;
        const tz = s2.tz !== undefined && s2.tz !== null ? s2.tz : -191.86;
        const rx = THREE.MathUtils.degToRad(s2.rx !== undefined && s2.rx !== null ? s2.rx : 181.89);
        const ry = THREE.MathUtils.degToRad(s2.ry !== undefined && s2.ry !== null ? s2.ry : -2.72);
        const rz = THREE.MathUtils.degToRad(s2.rz !== undefined && s2.rz !== null ? s2.rz : 90.53);
        
        controls.target.set(tx, ty, tz);
        camera.position.set(tx + 500, ty - 500, tz + 350);
        controls.update();
        
        const qEtalon = new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz, 'ZYX'));
        
        // 1. Etalon Mesh (Red)
        const matRed = new THREE.MeshStandardMaterial({ color: 0xef4444, roughness: 0.4, metalness: 0.1, transparent: true, opacity: 0.75 });
        const meshEtalon = new THREE.Mesh(geometry, matRed);
        meshEtalon.position.set(tx, ty, tz);
        meshEtalon.quaternion.copy(qEtalon);
        scene.add(meshEtalon);
        objectsMap['etalon'] = meshEtalon;
        
        // 2. Current Mesh (Green) - Shifted by delta_3d using Quaternions
        const matGreen = new THREE.MeshStandardMaterial({ color: 0x10b981, roughness: 0.3, metalness: 0.2, transparent: true, opacity: 0.85 });
        const meshCurrent = new THREE.Mesh(geometry.clone(), matGreen);
        
        const qDelta = new THREE.Quaternion().setFromEuler(new THREE.Euler(
            THREE.MathUtils.degToRad(d.roll_deg),
            THREE.MathUtils.degToRad(d.pitch_deg),
            THREE.MathUtils.degToRad(d.yaw_deg),
            'ZYX'
        ));
        
        const qFinal = new THREE.Quaternion().multiplyQuaternions(qDelta, qEtalon);
        meshCurrent.quaternion.copy(qFinal);
        meshCurrent.position.set(tx + d.x_mm, ty + d.y_mm, tz + d.z_mm);
        scene.add(meshCurrent);
        objectsMap['current'] = meshCurrent;
        
        // 2.2 Ground Truth Mesh (Yellow/Gold) - Actual physical pose from machine
        if (data.gt_delta_3d) {
            const gtD = data.gt_delta_3d;
            const matYellow = new THREE.MeshStandardMaterial({ color: 0xf59e0b, roughness: 0.3, metalness: 0.2, transparent: true, opacity: 0.75 });
            const meshGT = new THREE.Mesh(geometry.clone(), matYellow);
            
            const qGtDelta = new THREE.Quaternion().setFromEuler(new THREE.Euler(
                THREE.MathUtils.degToRad(gtD.roll_deg),
                THREE.MathUtils.degToRad(gtD.pitch_deg),
                THREE.MathUtils.degToRad(gtD.yaw_deg),
                'ZYX'
            ));
            
            const qGtFinal = new THREE.Quaternion().multiplyQuaternions(qGtDelta, qEtalon);
            meshGT.quaternion.copy(qGtFinal);
            meshGT.position.set(tx + gtD.x_mm, ty + gtD.y_mm, tz + gtD.z_mm);
            scene.add(meshGT);
            objectsMap['ground_truth_helmet'] = meshGT;
        }
        
        // 2.5 Etalon LS Line (Cyan/Blue) sitting on Red Etalon helmet
        if (s2.original_points && s2.original_points.length > 0) {
            const etalonLsGroup = new THREE.Group();
            const pts = [];
            const sphereGeom = new THREE.SphereGeometry(1.5, 8, 8);
            const sphereMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });
            
            s2.original_points.forEach(p => {
                const v = new THREE.Vector3(p.x, p.y, p.z);
                pts.push(v.clone());
                const sp = new THREE.Mesh(sphereGeom, sphereMat);
                sp.position.copy(v);
                etalonLsGroup.add(sp);
            });
            
            const lineGeom = new THREE.BufferGeometry().setFromPoints(pts);
            const lineMat = new THREE.LineBasicMaterial({ color: 0x00ffff, linewidth: 2 });
            const line = new THREE.Line(lineGeom, lineMat);
            etalonLsGroup.add(line);
            scene.add(etalonLsGroup);
            objectsMap['etalon_ls'] = etalonLsGroup;
        }

        // 3. Laser Line (White) from original_points transformed to current helmet
        if (s2.original_points && s2.original_points.length > 0) {
            const laserGroup = new THREE.Group();
            const pts = [];
            const sphereGeom = new THREE.SphereGeometry(1.5, 8, 8);
            const sphereMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
            
            s2.original_points.forEach(p => {
                // Transform point exactly like we did in script
                const v = new THREE.Vector3(p.x - tx, p.y - ty, p.z - tz);
                v.applyQuaternion(qDelta);
                v.x += tx + d.x_mm;
                v.y += ty + d.y_mm;
                v.z += tz + d.z_mm;
                
                pts.push(v.clone());
                const sp = new THREE.Mesh(sphereGeom, sphereMat);
                sp.position.copy(v);
                laserGroup.add(sp);
            });
            
            const lineGeom = new THREE.BufferGeometry().setFromPoints(pts);
            const lineMat = new THREE.LineBasicMaterial({ color: 0xffffff, linewidth: 2 });
            const line = new THREE.Line(lineGeom, lineMat);
            laserGroup.add(line);
            scene.add(laserGroup);
            objectsMap['laser'] = laserGroup;
        }
        
        // 4. Ground Truth LS from Archive (Yellow/Gold - Actual CNC Recording)
        if (data.ground_truth_points && data.ground_truth_points.length > 0) {
            const gtGroup = new THREE.Group();
            const pts = [];
            const sphereGeom = new THREE.SphereGeometry(1.8, 8, 8);
            const sphereMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b });
            
            data.ground_truth_points.forEach(p => {
                const v = new THREE.Vector3(p.x, p.y, p.z);
                pts.push(v.clone());
                const sp = new THREE.Mesh(sphereGeom, sphereMat);
                sp.position.copy(v);
                gtGroup.add(sp);
            });
            
            const lineGeom = new THREE.BufferGeometry().setFromPoints(pts);
            const lineMat = new THREE.LineBasicMaterial({ color: 0xf59e0b, linewidth: 3 });
            const line = new THREE.Line(lineGeom, lineMat);
            gtGroup.add(line);
            
            scene.add(gtGroup);
            objectsMap['ground_truth'] = gtGroup;
        }
        
        controls.target.set(tx, ty, tz);
        camera.position.set(tx, ty - 450, tz + 250);
        controls.update();
        
    }, undefined, (err) => console.error("Error loading STL:", err));
    
    function animate() {
        requestAnimationFrame(animate);
        controls.update();
        renderer.render(scene, camera);
    }
    animate();
}
