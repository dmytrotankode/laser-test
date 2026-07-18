import json
import numpy as np

# Simulate Step 5 data for BACK camera
# scale = 0.95, du = -2.25, dv = -8.95
pos = np.array([0, 2500, 0], dtype=float)
look = np.array([0, 0, 0], dtype=float)
up = np.array([0, 0, 1], dtype=float)

Z = look - pos
Z_dist = np.linalg.norm(Z)
Z_cam = Z / Z_dist

X_cam = np.cross(Z_cam, up)
X_cam = X_cam / np.linalg.norm(X_cam)
Y_cam = np.cross(Z_cam, X_cam)

focal = 1024.0
du = -2.25
dv = -8.95
scale = 0.9500

dp_lateral = (du * Z_dist / focal) * X_cam + (dv * Z_dist / focal) * Y_cam
dp_z = Z_dist * (scale - 1) * Z_cam

new_pos = pos - dp_lateral - dp_z
new_look = look - dp_lateral

dist = np.linalg.norm(new_pos - new_look)

print("BACK camera:")
print(f"new_pos: {new_pos}")
print(f"new_look: {new_look}")
print(f"dist: {dist}")
