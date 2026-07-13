import os
import sys
import json
import importlib

def check_package(package_name):
    try:
        importlib.import_module(package_name)
        print(f"[OK] Package '{package_name}' is installed.")
        return True
    except ImportError:
        print(f"[FAIL] Package '{package_name}' is MISSING.")
        return False

def check_file(file_path, description):
    if os.path.exists(file_path):
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        print(f"[OK] {description} found: {file_path} ({size_mb:.2f} MB)")
        return True
    else:
        print(f"[FAIL] {description} NOT FOUND: {file_path}")
        return False

def main():
    print("=== STEP 00: ENVIRONMENT CHECK ===")
    
    # Check packages
    print("\n--- Checking Python Packages ---")
    packages = ['numpy', 'scipy', 'cv2', 'rembg', 'trimesh', 'stl', 'matplotlib']
    all_packages_ok = all(check_package(pkg) for pkg in packages)
    
    # Load config
    config_path = os.path.join(os.path.dirname(__file__), '..', 'pipeline_config.json')
    if not os.path.exists(config_path):
        print(f"\n[FAIL] Config file NOT FOUND: {config_path}")
        sys.exit(1)
        
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    base_dir = os.path.join(os.path.dirname(__file__), '..')
    
    # Check inputs
    print("\n--- Checking Input Files ---")
    all_files_ok = True
    
    ls_path = os.path.join(base_dir, config['paths']['ls_file'])
    all_files_ok &= check_file(ls_path, "LS Program File")
    
    model_step_path = os.path.join(base_dir, config['paths']['model_step'])
    model_stl_path = os.path.join(base_dir, config['paths']['model_stl'])
    
    if os.path.exists(model_stl_path):
        check_file(model_stl_path, "3D Model (STL)")
    elif os.path.exists(model_step_path):
        print(f"[WARNING] STL model not found, but STEP is present: {model_step_path}")
        print("          You might need to convert STEP to STL first.")
    else:
        print("[FAIL] No 3D model found (neither STEP nor STL).")
        all_files_ok = False

    etalon_dir = os.path.join(base_dir, config['paths']['photos_etalon'])
    for cam, info in config['cameras'].items():
        if cam.startswith('_'): continue
        img_path = os.path.join(etalon_dir, info['file'])
        all_files_ok &= check_file(img_path, f"Etalon Photo ({cam})")
        
    current_dir = os.path.join(base_dir, config['paths']['photos_current'])
    for cam, info in config['cameras'].items():
        if cam.startswith('_'): continue
        img_path = os.path.join(current_dir, info['file'])
        all_files_ok &= check_file(img_path, f"Current Photo ({cam})")

    # Final verdict
    print("\n--- Result ---")
    if all_packages_ok and all_files_ok:
        print("Environment is READY. You can proceed to STEP 01.")
        sys.exit(0)
    else:
        print("Environment is NOT READY. Please fix the issues above.")
        sys.exit(1)

if __name__ == '__main__':
    main()
