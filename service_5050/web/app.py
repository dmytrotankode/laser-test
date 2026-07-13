from flask import Flask, render_template, jsonify, send_from_directory, request
import subprocess
import os
import json

app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RESULTS_BASE_DIR = os.path.join(BASE_DIR, 'results')
INPUT_DIR = os.path.join(BASE_DIR, 'input')
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')
RESULTS_FORM2_BASE_DIR = os.path.join(BASE_DIR, 'results_form2')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start')
def start_page():
    return render_template('start.html')

@app.route('/form2')
def form2_page():
    return render_template('form2.html')

@app.route('/vis/step13')
def vis_step13():
    return render_template('step13_vis.html')

@app.route('/files/<session_id>/<path:filename>')
def serve_file(session_id, filename):
    session_dir = os.path.join(RESULTS_BASE_DIR, session_id)
    if os.path.exists(os.path.join(session_dir, filename)):
        return send_from_directory(session_dir, filename)
    elif os.path.exists(os.path.join(INPUT_DIR, filename)):
        return send_from_directory(INPUT_DIR, filename)
    elif os.path.exists(os.path.join(INPUT_DIR, 'model_3d', filename)):
        return send_from_directory(os.path.join(INPUT_DIR, 'model_3d'), filename)
    return "File not found", 404

@app.route('/api/log')
def get_log():
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'error': 'No session_id provided'}), 400
        
    log_path = os.path.join(RESULTS_BASE_DIR, session_id, f'log_{session_id}.txt')
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            return jsonify({'log': f.read()})
    return jsonify({'log': ''})

def run_script(script_name, session_id, extra_args=[]):
    if not session_id:
        return {'success': False, 'stdout': '', 'stderr': 'Missing session_id'}
        
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    args = ['--session', session_id] + extra_args
    try:
        result = subprocess.run(['python', script_path] + args, capture_output=True, text=True, cwd=SCRIPTS_DIR)
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
    except Exception as e:
        return {'success': False, 'stdout': '', 'stderr': str(e)}

@app.route('/api/step01')
def api_step01():
    session_id = request.args.get('session_id')
    res = run_script('step01_parse_ls.py', session_id)
    data = {}
    if res['success']:
        try:
            with open(os.path.join(RESULTS_BASE_DIR, session_id, 'step01_ls_points.json'), 'r') as f:
                data = json.load(f)
        except Exception: pass
    return jsonify({'result': res, 'data': f"Parsed {len(data)} points." if data else ""})

@app.route('/api/step02')
def api_step02():
    session_id = request.args.get('session_id')
    res = run_script('step02_align_3d_to_ls.py', session_id)
    data = {}
    if res['success']:
        try:
            with open(os.path.join(RESULTS_BASE_DIR, session_id, 'step02_alignment.json'), 'r') as f:
                data = json.load(f)
        except Exception: pass
    return jsonify({'result': res, 'data': data, 'image': f'/files/{session_id}/step02_alignment_plot.png'})

@app.route('/api/step03')
def api_step03():
    session_id = request.args.get('session_id')
    res = run_script('step03_freeze_space.py', session_id)
    data = {}
    if res['success']:
        try:
            with open(os.path.join(RESULTS_BASE_DIR, session_id, 'step03_freeze_space.json'), 'r') as f:
                data = json.load(f)
        except Exception: pass
    return jsonify({'result': res, 'data': data})

@app.route('/api/step04')
def api_step04():
    session_id = request.args.get('session_id')
    res = run_script('step04_segment.py', session_id, ['--mode', 'etalon'])
    return jsonify({'result': res, 'images': [
        f'/files/{session_id}/step_etalon_masks/rgba_back.png',
        f'/files/{session_id}/step_etalon_masks/rgba_left.png',
        f'/files/{session_id}/step_etalon_masks/rgba_top.png',
        f'/files/{session_id}/step_etalon_masks/solid_back.png',
        f'/files/{session_id}/step_etalon_masks/solid_left.png',
        f'/files/{session_id}/step_etalon_masks/solid_top.png'
    ]})

@app.route('/api/step05')
def api_step05():
    session_id = request.args.get('session_id')
    res = run_script('step05_project.py', session_id)
    return jsonify({'result': res, 'images': [
        f'/files/{session_id}/step_etalon_projected/rgba_back.png',
        f'/files/{session_id}/step_etalon_projected/rgba_left.png',
        f'/files/{session_id}/step_etalon_projected/rgba_top.png'
    ]})

@app.route('/api/step06')
def api_step06():
    session_id = request.args.get('session_id')
    res = run_script('step06_place_projected.py', session_id)
    data = {}
    if res['success']:
        try:
            with open(os.path.join(RESULTS_BASE_DIR, session_id, 'step06_projected_placements.json'), 'r') as f:
                data = json.load(f)
        except Exception: pass
    return jsonify({'result': res, 'data': data})

@app.route('/api/step07')
def api_step07():
    session_id = request.args.get('session_id')
    res = run_script('step07_fit_etalon.py', session_id)
    data = {}
    if res['success']:
        try:
            with open(os.path.join(RESULTS_BASE_DIR, session_id, 'step07_etalon_fit.json'), 'r') as f:
                data = json.load(f)
        except Exception: pass
    return jsonify({'result': res, 'data': data, 'images': [
        f'/files/{session_id}/step07_etalon_overlap/overlap_back.png',
        f'/files/{session_id}/step07_etalon_overlap/overlap_left.png',
        f'/files/{session_id}/step07_etalon_overlap/overlap_top.png'
    ]})




@app.route('/api/step08')
def api_step08():
    session_id = request.args.get('session_id')
    res = run_script('step04_segment.py', session_id, ['--mode', 'current'])
    return jsonify({'result': res, 'images': [
        f'/files/{session_id}/step_current_masks/rgba_back.png',
        f'/files/{session_id}/step_current_masks/rgba_left.png',
        f'/files/{session_id}/step_current_masks/rgba_top.png',
        f'/files/{session_id}/step_current_masks/solid_back.png',
        f'/files/{session_id}/step_current_masks/solid_left.png',
        f'/files/{session_id}/step_current_masks/solid_top.png'
    ]})

@app.route('/api/step09')
def api_step09():
    session_id = request.args.get('session_id')
    res = run_script('step08_fit_pose.py', session_id)
    data = {}
    if res['success']:
        try:
            with open(os.path.join(RESULTS_BASE_DIR, session_id, 'step08_current_pose_fit.json'), 'r') as f:
                data = json.load(f)
        except Exception: pass
    return jsonify({'result': res, 'data': data, 'images': [
        f'/files/{session_id}/step08_current_overlap/overlap_back.png',
        f'/files/{session_id}/step08_current_overlap/overlap_left.png',
        f'/files/{session_id}/step08_current_overlap/overlap_top.png'
    ]})

@app.route('/api/step10')
def api_step10():
    session_id = request.args.get('session_id')
    res = run_script('step09b_texture_fit.py', session_id)
    data = {}
    if res['success']:
        try:
            with open(os.path.join(RESULTS_BASE_DIR, session_id, 'step09b_current_pose_fit.json'), 'r') as f:
                data = json.load(f)
        except Exception: pass
    return jsonify({'result': res, 'data': data, 'images': [
        f'/files/{session_id}/step09b_current_overlap/overlap_back.png',
        f'/files/{session_id}/step09b_current_overlap/overlap_left.png',
        f'/files/{session_id}/step09b_current_overlap/overlap_top.png'
    ]})

@app.route('/api/step11')
def api_step11():
    session_id = request.args.get('session_id')
    res = run_script('step09c_contour_fit.py', session_id)
    data = {}
    if res['success']:
        try:
            with open(os.path.join(RESULTS_BASE_DIR, session_id, 'step09c_current_pose_fit.json'), 'r') as f:
                data = json.load(f)
        except Exception: pass
    return jsonify({'result': res, 'data': data, 'images': [
        f'/files/{session_id}/step09c_current_overlap/overlap_back.png',
        f'/files/{session_id}/step09c_current_overlap/overlap_left.png',
        f'/files/{session_id}/step09c_current_overlap/overlap_top.png'
    ]})

@app.route('/api/step11b')
def api_step11b():
    session_id = request.args.get('session_id')
    res = run_script('step09d_ai_reconstruct_fit.py', session_id)
    data = {}
    if res['success']:
        try:
            with open(os.path.join(RESULTS_BASE_DIR, session_id, 'step09d_ai_reconstruct_fit.json'), 'r') as f:
                data = json.load(f)
        except Exception: pass
    return jsonify({'result': res, 'data': data})

@app.route('/api/step12')
def api_step12():
    session_id = request.args.get('session_id')
    res = run_script('step10_analyze_results.py', session_id)
    data = {}
    if res['success']:
        try:
            with open(os.path.join(RESULTS_BASE_DIR, session_id, 'step10_final_pose.json'), 'r') as f:
                data = json.load(f)
        except Exception: pass
    return jsonify({'result': res, 'data': data})

@app.route('/api/step12_metrics')
def api_step12_metrics():
    session_id = request.args.get('session_id')
    # Attempt to read the final pose file (step10_final_pose.json) which should contain the needed centers
    metrics = {}
    try:
        with open(os.path.join(RESULTS_BASE_DIR, session_id, 'step10_final_pose.json'), 'r') as f:
            data = json.load(f)
            # Expect fields 'etalon_center' and 'current_center' as dicts with x,y,z
            if 'etalon_center' in data and 'current_center' in data:
                metrics['etalon_center'] = data['etalon_center']
                metrics['current_center'] = data['current_center']
            else:
                # Fallback: compute from LS files if not present
                def load_ls(path):
                    pts = []
                    import re
                    pattern = re.compile(r'P\[\d+\]\{[^}]*X\s*=\s*([-\d.]+)[^}]*Y\s*=\s*([-\d.]+)[^}]*Z\s*=\s*([-\d.]+)', re.IGNORECASE)
                    with open(path, 'r', errors='replace') as f2:
                        content = f2.read()
                    for m in pattern.finditer(content):
                        pts.append({'x': float(m.group(1)), 'y': float(m.group(2)), 'z': float(m.group(3))})
                    return pts
                # original LS path from config
                config_path = os.path.join(BASE_DIR, 'pipeline_config.json')
                with open(config_path, 'r') as cfg_f:
                    cfg = json.load(cfg_f)
                orig_ls_path = os.path.join(BASE_DIR, cfg['paths']['ls_file'])
                orig_pts = load_ls(orig_ls_path)
                def centroid(pts):
                    if not pts: return {'x':0, 'y':0, 'z':0}
                    cx = sum(p['x'] for p in pts) / len(pts)
                    cy = sum(p['y'] for p in pts) / len(pts)
                    cz = sum(p['z'] for p in pts) / len(pts)
                    return {'x': cx, 'y': cy, 'z': cz}
                ce = centroid(orig_pts)
                metrics['etalon_center'] = ce
                
                # Compute current_center using delta_translation instead of reading corrected LS
                t = data.get('delta_translation', [0,0,0])
                metrics['current_center'] = {
                    'x': ce['x'] + t[0],
                    'y': ce['y'] + t[1],
                    'z': ce['z'] + t[2]
                }
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify(metrics)

@app.route('/api/step13')
def api_step13():
    session_id = request.args.get('session_id')
    res = run_script('step09_generate_ls.py', session_id)
    # After LS generation, gather visualization metrics
    metrics = {}
    try:
        # Load final pose metrics (step 12)
        with open(os.path.join(RESULTS_BASE_DIR, session_id, 'step10_final_pose.json'), 'r') as f:
            final_pose = json.load(f)
            metrics['delta_translation'] = final_pose.get('delta_translation')
            metrics['delta_rotvec'] = final_pose.get('delta_rotvec')
            metrics['metrics'] = final_pose.get('metrics')
    except Exception:
        final_pose = {}
    # Compute centroids for etalon (original LS) and corrected LS
    def load_ls(path):
        pts = []
        import re
        pattern = re.compile(r'P\[\d+\]\{[^}]*X\s*=\s*([-\d.]+)[^}]*Y\s*=\s*([-\d.]+)[^}]*Z\s*=\s*([-\d.]+)', re.IGNORECASE)
        with open(path, 'r', errors='replace') as f:
            for line in f:
                m = pattern.search(line)
                if m:
                    pts.append({'x': float(m.group(1)), 'y': float(m.group(2)), 'z': float(m.group(3))})
        return pts
    try:
        # original LS path from config
        config_path = os.path.join(BASE_DIR, 'pipeline_config.json')
        with open(config_path, 'r') as f:
            cfg = json.load(f)
        orig_ls_path = os.path.join(BASE_DIR, cfg['paths']['ls_file'])
        orig_pts = load_ls(orig_ls_path)
        corr_ls_path = os.path.join(RESULTS_BASE_DIR, session_id, 'TORXL_corrected.ls')
        corr_pts = load_ls(corr_ls_path)
        def centroid(pts):
            cx = sum(p['x'] for p in pts) / len(pts)
            cy = sum(p['y'] for p in pts) / len(pts)
            cz = sum(p['z'] for p in pts) / len(pts)
            return {'x': cx, 'y': cy, 'z': cz}
        etalon_center = centroid(orig_pts)
        current_center = centroid(corr_pts)
        metrics['etalon_center'] = etalon_center
        metrics['current_center'] = current_center
    except Exception:
        pass
    # Save metrics to JSON for later analysis
    try:
        with open(os.path.join(RESULTS_BASE_DIR, session_id, 'step13_visualization.json'), 'w') as f:
            json.dump(metrics, f, indent=2)
    except Exception:
        pass
    return jsonify({'result': res, 'file': f'/files/{session_id}/TORXL_corrected.ls', 'vis_metrics': f'/files/{session_id}/step13_visualization.json'})

@app.route('/api/ls_as_json')
def ls_as_json():
    """Parse a FANUC .ls file and return its XYZ points as JSON for 3D visualization."""
    import re
    session_id = request.args.get('session_id')
    ls_type = request.args.get('type', 'original')  # 'original' or 'corrected'
    if not session_id:
        return jsonify({'error': 'No session_id provided'}), 400

    if ls_type == 'corrected':
        ls_path = os.path.join(RESULTS_BASE_DIR, session_id, 'TORXL_corrected.ls')
    else:
        # Try to find original LS file from config
        config_path = os.path.join(BASE_DIR, 'pipeline_config.json')
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            ls_path = os.path.join(BASE_DIR, config['paths']['ls_file'])
        except Exception:
            return jsonify({'error': 'Config not found'}), 500

    if not os.path.exists(ls_path):
        return jsonify({'error': f'LS file not found: {ls_path}'}), 404

    pattern = re.compile(
        r'P\[\d+\]\{[^}]*X\s*=\s*([-\d.]+)[^}]*Y\s*=\s*([-\d.]+)[^}]*Z\s*=\s*([-\d.]+)',
        re.IGNORECASE
    )
    points = []
    with open(ls_path, 'r', errors='replace') as f:
        content = f.read()
    for m in pattern.finditer(content):
        points.append({'x': float(m.group(1)), 'y': float(m.group(2)), 'z': float(m.group(3))})

    return jsonify(points)

@app.route('/api/step13_visualisation_data')
def step13_visualisation_data():
    """Return original and corrected LS points plus step13 metrics for 3D visualisation."""
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'error': 'No session_id provided'}), 400
    # Load original LS points
    config_path = os.path.join(BASE_DIR, 'pipeline_config.json')
    try:
        with open(config_path, 'r') as f:
            cfg = json.load(f)
        orig_ls_path = os.path.join(BASE_DIR, cfg['paths']['ls_file'])
    except Exception:
        return jsonify({'error': 'Config not found'}), 500
    # Load corrected LS points
    corrected_ls_path = os.path.join(RESULTS_BASE_DIR, session_id, 'TORXL_corrected.ls')
    import re
    pattern = re.compile(r'P\[\d+\]\{[^}]*X\s*=\s*([-\d.]+)[^}]*Y\s*=\s*([-\d.]+)[^}]*Z\s*=\s*([-\d.]+)', re.IGNORECASE)
    def load_pts(path):
        pts = []
        if not os.path.exists(path):
            return pts
        with open(path, 'r', errors='replace') as f:
            content = f.read()
        for m in pattern.finditer(content):
            pts.append({'x': float(m.group(1)), 'y': float(m.group(2)), 'z': float(m.group(3))})
        return pts
    orig_pts = load_pts(orig_ls_path)
    corr_pts = load_pts(corrected_ls_path)
    # Load metrics if available
    metrics = {}
    vis_metrics_path = os.path.join(RESULTS_BASE_DIR, session_id, 'step13_visualization.json')
    if os.path.exists(vis_metrics_path):
        try:
            with open(vis_metrics_path, 'r') as f:
                metrics = json.load(f)
        except Exception:
            pass
    return jsonify({'original_points': orig_pts, 'corrected_points': corr_pts, 'metrics': metrics})


@app.route('/api/session_state')
def session_state():
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'error': 'No session_id provided'}), 400
        
    session_dir = os.path.join(RESULTS_BASE_DIR, session_id)
    state = {}
    
    def check_file(path):
        return os.path.exists(os.path.join(session_dir, path))
    
    if check_file('step01_ls_points.json'): state['01'] = {'completed': True}
    if check_file('step02_alignment.json'): state['02'] = {'completed': True}
    if check_file('step03_freeze_space.json'): state['03'] = {'completed': True}
    if check_file('step_etalon_masks/rgba_back.png'): state['04'] = {'completed': True, 'images': [f'/files/{session_id}/step_etalon_masks/rgba_{c}.png' for c in ['back','left','top']] + [f'/files/{session_id}/step_etalon_masks/mask_{c}.png' for c in ['back','left','top']]}
    if check_file('step_etalon_projected/rgba_back.png'): state['05'] = {'completed': True, 'images': [f'/files/{session_id}/step_etalon_projected/rgba_{c}.png' for c in ['back','left','top']]}
    if check_file('step06_projected_placements.json'): state['06'] = {'completed': True}
    if check_file('step07_etalon_fit.json'): state['07'] = {'completed': True, 'images': [f'/files/{session_id}/step07_etalon_overlap/overlap_{c}.png' for c in ['back','left','top']]}
    if check_file('step_current_masks/rgba_back.png'): state['08'] = {'completed': True, 'images': [f'/files/{session_id}/step_current_masks/rgba_{c}.png' for c in ['back','left','top']] + [f'/files/{session_id}/step_current_masks/mask_{c}.png' for c in ['back','left','top']]}
    if check_file('step08_current_pose_fit.json'): 
        state['09'] = {'completed': True, 'images': [f'/files/{session_id}/step08_current_overlap/overlap_{c}.png' for c in ['back','left','top']]}
        try:
            with open(os.path.join(session_dir, 'step08_current_pose_fit.json')) as f:
                state['09']['data'] = json.load(f)
        except: pass
    if check_file('step09b_current_pose_fit.json'): 
        state['10'] = {'completed': True, 'images': [f'/files/{session_id}/step09b_current_overlap/overlap_{c}.png' for c in ['back','left','top']]}
        try:
            with open(os.path.join(session_dir, 'step09b_current_pose_fit.json')) as f:
                state['10']['data'] = json.load(f)
        except: pass
    if check_file('step09c_current_pose_fit.json'): 
        state['11'] = {'completed': True, 'images': [f'/files/{session_id}/step09c_current_overlap/overlap_{c}.png' for c in ['back','left','top']]}
        try:
            with open(os.path.join(session_dir, 'step09c_current_pose_fit.json')) as f:
                state['11']['data'] = json.load(f)
        except: pass

    if check_file('step09d_ai_reconstruct_fit.json'): 
        state['11b'] = {'completed': True}
        try:
            with open(os.path.join(session_dir, 'step09d_ai_reconstruct_fit.json')) as f:
                state['11b']['data'] = json.load(f)
        except: pass
        
    if check_file('step10_final_pose.json'): 
        state['12'] = {'completed': True}
        try:
            with open(os.path.join(session_dir, 'step10_final_pose.json')) as f:
                state['12']['data'] = json.load(f)
        except: pass
        
    if check_file('TORXL_corrected.ls'): state['13'] = {'completed': True, 'file': f'/files/{session_id}/TORXL_corrected.ls'}
        
    return jsonify(state)

if __name__ == '__main__':
    app.run(debug=True, port=5050)
