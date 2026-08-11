"""Шаг B0: видит ли силуэт то же движение шлема, что известно из линий реза.

В подгонках A3/A5 меш стоял неподвижно, а двигалась камера. Значит разница
найденных камер между вариантами - это и есть движение шлема, только с обратным
знаком. Это движение мы уже знаем независимо: метки ICP по линиям реза лежат в
input/model_pose.json (pose_vs_anchor).

Два источника не связаны ничем: один смотрит на фотографии, другой на
записанные программы робота. Если они сойдутся - цепочка «фото -> геометрия ->
координаты станка» подтверждена целиком, и общую подгонку делать стоит.
Если разойдутся - дальше идти незачем.

Считаем по СДВИГАМ. Поворот в A5 определялся плохо (разброс до 14.6° там, где
шлем шевелился на 5°), поэтому он идёт справочной колонкой, а решение по нему
не принимается.
"""
import os
import sys
import json
import importlib.util
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render as R                                    # noqa: E402
from scipy.spatial.transform import Rotation as Rot   # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

spec = importlib.util.spec_from_file_location('a3mod', os.path.join(HERE, 'a3_bestcase.py'))
src = open(os.path.join(HERE, 'a3_bestcase.py'), encoding='utf-8').read()
src = src.split("store = {}\nif os.path.exists(STORE):")[0]
a3 = importlib.util.module_from_spec(spec)
exec(compile(src, 'a3_bestcase.py', 'exec'), a3.__dict__)
a3.N_RANDOM, a3.N_POLISH, a3.MAXITER = 40, 6, 800

BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
MODEL = json.load(open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8'))
LIB = MODEL['library']

# варианты с наибольшим разбросом поз - чтобы сигнал был выше шума подгонки
VARIANTS = ['v1', 'v8', 'v11', 'v12', 'v16', 'v10']
CACHE = os.path.join(HERE, 'b0_cams.json')

cams = {}
if os.path.exists(CACHE):
    cams = json.load(open(CACHE, encoding='utf-8'))

for view in ('back', 'left', 'top'):
    for v in VARIANTS:
        key = f'{v}_{view}'
        if key in cams:
            continue
        if R.load_mask(v, view, a3.COARSE)[0] is None:
            print(f"  {key}: нет маски, пропуск", flush=True)
            continue
        val, par, _, _ = a3.fit_view(view, v, {})
        cams[key] = {'val': float(val), 'p': [float(x) for x in par]}
        print(f"  {key}: остаток {val * a3.MM_PER_PX:.2f} мм", flush=True)
        json.dump(cams, open(CACHE, 'w', encoding='utf-8'))

print()
print("=" * 74)
print("Движение шлема: по силуэтам против меток ICP")
print("=" * 74)


def cam_pose(v, view):
    """Положение камеры в системе меша -> положение меша в системе камеры."""
    p = np.array(cams[f'{v}_{view}']['p'])
    Rm = Rot.from_rotvec(p[:3])
    dist = np.exp(p[3])
    eye = a3.C - Rm.as_matrix().T @ np.array([0.0, 0.0, dist])
    return Rm, eye


rows = []
for view in ('back', 'left', 'top'):
    if f'v1_{view}' not in cams:
        continue
    R0, e0 = cam_pose('v1', view)
    for v in VARIANTS[1:]:
        if f'{v}_{view}' not in cams:
            continue
        Rv, ev = cam_pose(v, view)
        # камера уехала на (ev - e0) в системе меша; в системе камеры это
        # эквивалентно тому, что меш уехал на обратную величину
        d_cam = R0.as_matrix() @ (e0 - ev)
        rows.append((view, v, d_cam, np.degrees((Rv * R0.inv()).magnitude())))

print()
print("Сдвиг шлема, мм: по фото (в системе камеры) против метки ICP (в системе станка).")
print("Оси у них разные, поэтому сравнивается ВЕЛИЧИНА сдвига, а не покомпонентно.")
print()
print(f"{'вар':<6}{'ICP, мм':>10}{'back':>10}{'left':>10}{'top':>10}{'поворот ICP':>14}")
for v in VARIANTS[1:]:
    icp = np.array(LIB[v]['pose_vs_anchor'][:3]) - np.array(LIB['v1']['pose_vs_anchor'][:3])
    mag = np.linalg.norm(icp)
    got = {}
    for view in ('back', 'left', 'top'):
        m = [r for r in rows if r[0] == view and r[1] == v]
        got[view] = np.linalg.norm(m[0][2][:2]) if m else float('nan')
    ang = np.linalg.norm(np.array(LIB[v]['pose_vs_anchor'][3:]) -
                         np.array(LIB['v1']['pose_vs_anchor'][3:]))
    print(f"{v:<6}{mag:>10.2f}{got['back']:>10.2f}{got['left']:>10.2f}"
          f"{got['top']:>10.2f}{ang:>13.2f}°")

print()
print("Читать так: колонки back/left/top - величина сдвига, увиденная каждой")
print("камерой поперёк своей оси взгляда. Она не обязана точно равняться ICP")
print("(каждая камера видит только две оси из трёх), но обязана РАСТИ ВМЕСТЕ с ней.")
print("Если связи нет вовсе - силуэт не видит движения, и путь закрыт.")
