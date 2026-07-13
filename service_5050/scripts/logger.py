import os
import datetime

class PipelineLogger:
    def __init__(self, session_id, base_dir, step_name):
        self.session_id = session_id
        self.step_name = step_name
        self.results_dir = os.path.join(base_dir, 'results', session_id)
        os.makedirs(self.results_dir, exist_ok=True)
        self.log_file = os.path.join(self.results_dir, f'log_{session_id}.txt')
        
        self.log(f"\n======================================")
        self.log(f"=== STARTING {step_name} ===")
        self.log(f"======================================")

    def log(self, message):
        # Print to stdout for web UI and console
        print(message)
        # Write to log file
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
