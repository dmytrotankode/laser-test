import json
import numpy as np
import os

def get_rotation_matrix(rx, ry, rz):
    rx, ry, rz = np.radians(rx), np.radians(ry), np.radians(rz)
    Rx = np.array([[1, 0, 0], [0, np.cos(rx), -np.sin(rx)], [0, np.sin(rx), np.cos(rx)]])
    Ry = np.array([[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]])
    Rz = np.array([[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx

with open('results/run_20260717_211332/step02_result.json', 'r') as f:
    step02 = json.load(f)
tx, ty, tz = step02['tx'], step02['ty'], step02['tz']
rx, ry, rz = step02['rx'], step02['ry'], step02['rz']
R_align = get_rotation_matrix(rx, ry, rz)
t_align = np.array([tx, ty, tz])

with open('results/run_20260717_211332/step06_result.json', 'r') as f:
    step06 = json.load(f)

for cam, info in step06['cameras'].items():
    pos = np.array(info['pos'])
    look = np.array(info['look_at'])
    up = np.array(info['up_vector'])
    
    world_pos = R_align @ pos + t_align
    world_look = R_align @ look + t_align
    world_up = R_align @ up
    
    print(f"{cam}:")
    print(f"  world_pos: {world_pos}")
    print(f"  world_look: {world_look}")
    print(f"  world_up: {world_up}")
