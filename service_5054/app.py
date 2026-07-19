import os
import time
import json
import subprocess
import threading
from flask import Flask, render_template, jsonify, request, send_from_directory, make_response
from flask_cors import CORS

app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
INPUT_DIR = os.path.join(BASE_DIR, 'input')

os.makedirs(RESULTS_DIR, exist_ok=True)

@app.route('/')
def index():
    response = make_response(render_template('index.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/files/<session_id>/<path:filename>')
def serve_results(session_id, filename):
    return send_from_directory(os.path.join(RESULTS_DIR, session_id), filename)

@app.route('/input/<path:filename>')
def serve_inputs(filename):
    return send_from_directory(INPUT_DIR, filename)

@app.route('/files/model_3d/<filename>')
def serve_model(filename):
    return send_from_directory(os.path.join(INPUT_DIR, 'model_3d'), filename)

@app.route('/api/start_session')
def start_session():
    session_id = f"run_{time.strftime('%Y%m%d_%H%M%S')}"
    session_path = os.path.join(RESULTS_DIR, session_id)
    os.makedirs(session_path, exist_ok=True)
    return jsonify({"session_id": session_id})

@app.route('/api/latest_session')
def latest_session():
    try:
        runs = sorted([d for d in os.listdir(RESULTS_DIR) if d.startswith('run_')])
        if runs:
            return jsonify({"session_id": runs[-1]})
    except Exception:
        pass
    return jsonify({"session_id": None})

def run_script_async(script_name, session_id):
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    def worker():
        try:
            # We pass session_id to the script
            subprocess.run(["python", script_path, "--session", session_id], cwd=BASE_DIR, check=True)
            # Write a done marker
            with open(os.path.join(RESULTS_DIR, session_id, f"{script_name}.done"), 'w') as f:
                f.write("done")
        except Exception as e:
            with open(os.path.join(RESULTS_DIR, session_id, f"{script_name}.error"), 'w') as f:
                f.write(str(e))
    threading.Thread(target=worker).start()

def generic_step_api(step_script, session_id, action, result_filename):
    if not session_id:
        return jsonify({"error": "No session_id"}), 400
        
    done_file = os.path.join(RESULTS_DIR, session_id, f"{step_script}.done")
    error_file = os.path.join(RESULTS_DIR, session_id, f"{step_script}.error")
    result_file = os.path.join(RESULTS_DIR, session_id, result_filename)
    
    if action == 'start':
        if os.path.exists(done_file): os.remove(done_file)
        if os.path.exists(error_file): os.remove(error_file)
        if os.path.exists(result_file): os.remove(result_file)
        run_script_async(step_script, session_id)
        return jsonify({"status": "started"})
        
    if os.path.exists(error_file):
        with open(error_file, 'r') as f: err = f.read()
        return jsonify({"status": "error", "message": err})
        
    if os.path.exists(done_file) and os.path.exists(result_file):
        with open(result_file, 'r') as f:
            data = json.load(f)
        return jsonify({"status": "done", "data": data})
        
    return jsonify({"status": "running"})

@app.route('/api/step00')
def api_step00():
    return generic_step_api("step00_analyze_cameras.py", request.args.get('session_id'), request.args.get('action'), "step00_cameras.json")

@app.route('/api/step01')
def api_step01():
    return generic_step_api("step01_create_etalon_trim.py", request.args.get('session_id'), request.args.get('action'), "step01_result.json")

@app.route('/api/step02')
def api_step02():
    return generic_step_api("step02_align_3d_to_trim.py", request.args.get('session_id'), request.args.get('action'), "step02_result.json")

@app.route('/api/step03')
def api_step03():
    return generic_step_api("step03_segment.py", request.args.get('session_id'), request.args.get('action'), "step03_result.json")

@app.route('/api/step04')
def api_step04():
    return generic_step_api("step04_fit_masks.py", request.args.get('session_id'), request.args.get('action'), "step04_result.json")

import base64

@app.route('/api/save_screenshot', methods=['POST'])
def save_screenshot():
    data = request.json
    session_id = data.get('session_id')
    filename = data.get('filename')
    image_data = data.get('image_data')
    
    if not session_id or not filename or not image_data:
        return jsonify({"error": "Missing parameters"}), 400
        
    try:
        header, encoded = image_data.split(",", 1)
        binary_data = base64.b64decode(encoded)
        
        filepath = os.path.join(RESULTS_DIR, session_id, filename)
        with open(filepath, 'wb') as f:
            f.write(binary_data)
            
        return jsonify({"status": "success", "path": filepath})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Service 5054...")
    app.run(host='0.0.0.0', port=5054, debug=False)
