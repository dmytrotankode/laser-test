import os
import time
import json
import subprocess
import threading
from flask import Flask, render_template, jsonify, request, send_from_directory
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
    return render_template('index.html')

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
    return generic_step_api("step04_project.py", request.args.get('session_id'), request.args.get('action'), "step04_result.json")

if __name__ == '__main__':
    print("Starting Service 5054...")
    app.run(host='0.0.0.0', port=5054, debug=False)
