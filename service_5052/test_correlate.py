import cv2
import numpy as np

target = cv2.imread('results/run_20260717_211332/solid_back.png', cv2.IMREAD_GRAYSCALE)
proj = cv2.imread('results/run_20260717_211332/proj_back.png', cv2.IMREAD_GRAYSCALE)

edges1 = cv2.Canny(target, 100, 200)
edges2 = cv2.Canny(proj, 100, 200)

edges1_f = np.float32(edges1)
edges2_f = np.float32(edges2)

(shift_x, shift_y), response = cv2.phaseCorrelate(edges2_f, edges1_f)
print(f"Shift: {shift_x}, {shift_y}, response: {response}")

best_iou = 0
best_dx, best_dy = 0, 0
for dx in range(-20, 21, 5):
    for dy in range(-20, 21, 5):
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        shifted = cv2.warpAffine(proj, M, (target.shape[1], target.shape[0]))
        iou = np.sum((shifted>0) & (target>0)) / max(1, np.sum((shifted>0) | (target>0)))
        if iou > best_iou:
            best_iou = iou
            best_dx, best_dy = dx, dy
print(f"IoU best: {best_dx}, {best_dy}, iou: {best_iou}")
