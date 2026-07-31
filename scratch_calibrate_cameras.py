import cv2
import cv2.aruco as aruco
import numpy as np
import glob
import os

SQUARES_X, SQUARES_Y = 6, 8
SQUARE_LEN = 27.0  # mm
MARKER_LEN = 20.0  # mm

DICT = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
BOARD = aruco.CharucoBoard((SQUARES_X, SQUARES_Y), SQUARE_LEN, MARKER_LEN, DICT)
DETECTOR_PARAMS = aruco.DetectorParameters()
ARUCO_DETECTOR = aruco.ArucoDetector(DICT, DETECTOR_PARAMS)
CHARUCO_DETECTOR = aruco.CharucoDetector(BOARD)

CAM_NAMES = {
    'DB0973003': 'cam2_side',
    'DB0973004': 'cam1_back',
    'DB0973002': 'cam3_top',
}


def find_images_for_camera(db_code):
    return sorted(glob.glob(f'calib2/**/*{db_code}*.png', recursive=True))


def detect_charuco(img_path):
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    ch_corners, ch_ids, marker_corners, marker_ids = CHARUCO_DETECTOR.detectBoard(img)
    if ch_corners is None or len(ch_corners) < 6:
        return None, None, img.shape
    return ch_corners, ch_ids, img.shape


BOARD_CORNERS_3D = BOARD.getChessboardCorners()  # (N,3) object points for every chessboard corner id


def calibrate_single(db_code):
    files = find_images_for_camera(db_code)
    obj_points, img_points = [], []
    shape = None
    used = 0
    n_corners_used = []
    for f in files:
        cc, ci, shape = detect_charuco(f)
        if cc is not None:
            obj_points.append(BOARD_CORNERS_3D[ci.flatten()])
            img_points.append(cc)
            n_corners_used.append(len(ci))
            used += 1
    if used < 4:
        print(f'{db_code}: only {used}/{len(files)} usable images, skipping calibration')
        return None
    h, w = shape[:2]
    ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(obj_points, img_points, (w, h), None, None)
    print(f'{db_code} ({CAM_NAMES.get(db_code, "?")}): used {used}/{len(files)} images (avg {np.mean(n_corners_used):.0f} corners/img), reprojection RMS error = {ret:.4f} px')
    print(f'  K =\n{K}')
    print(f'  dist = {dist.flatten()}')
    return {'K': K, 'dist': dist, 'rms': ret, 'n_used': used, 'n_total': len(files)}


if __name__ == '__main__':
    results = {}
    for db_code in CAM_NAMES:
        results[db_code] = calibrate_single(db_code)
        print()
