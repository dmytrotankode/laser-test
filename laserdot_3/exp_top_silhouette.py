"""Чи «бачить» контур згори помилку пози, яку не бачать back+left (14.10).

Для наборів 05.10 (у сервісі nabir-1005-001/002, правильні .LS відомі):
  * силует шолома на фото top (rembg, pipeline/segmentation - той самий, що в Методі 1);
  * 3D-модель шолома (data/model_3d/helmet_ref.stl) у трьох позах:
      nominal - номінальна CAD-поза нової розстановки (як чернетка розмітки),
      truth   - номінальна, переміщена так, як TOR_XL_1010_1 переходить у правильне кільце,
      method3 - так само, але в кільце, яке видав Метод 3 на реальній розмітці;
  * для кожної пози - розбіжність контуру проекції моделі з контуром фото, мм на деталі:
      mesh - повний силует моделі (нахил врахований сам собою),
      rim  - лише нижній край моделі (так робить Метод 1; при нахилі може бути не те).
Якщо truth помітно ближча за method3 - контур згори здатен підказати правильну позу.

    python exp_top_silhouette.py
"""
import os
import sys

import cv2
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

BASE = os.path.dirname(os.path.abspath(__file__))
S21 = os.path.join(BASE, '..', 'service_2021')
sys.path.insert(0, S21)
import ls_points  # noqa: E402
from pipeline import contour_fit, camera_model as CM, cad_placement, mesh_rim, segmentation  # noqa: E402

THR = int(os.environ.get('TOP_THR', 60))
cams = contour_fit.marker_cams(os.path.join(S21, 'calib', 'cameras', 'marker_2026-09-30'))
R0, t0 = cad_placement.load('rig_2026-09-30')
TRI = mesh_rim.load_stl(os.path.join(S21, 'data', 'model_3d', 'helmet_ref.stl'))
RIM = mesh_rim.mesh_rim(os.path.join(S21, 'data', 'model_3d', 'helmet_ref.stl'))


def ring(p):
    return np.array([q[2] for q in ls_points.read_ring(p)])


REF = ring(os.path.join(BASE, 'TOR_XL_1010_1.LS'))
C0 = REF.mean(0)


def dense(R, n=3000):
    Q = np.r_[R, R[:1]]
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
    t = np.linspace(0, d[-1], n, endpoint=False)
    return np.c_[[np.interp(t, d, Q[:, i]) for i in range(3)]].T


def pose_to(target):
    """Поворот+зсув+масштаб навколо C0, що переводить REF у target (3D, з кількох стартів)."""
    tree = cKDTree(dense(target))
    best = None
    for yaw in np.radians(np.arange(-20, 21, 10)):
        x0 = np.r_[0, 0, yaw, target.mean(0) - C0, 0]
        r = least_squares(lambda p: tree.query(apply(p, REF))[0], x0)
        if best is None or r.cost < best.cost:
            best = r
    return best.x


def apply(p, X):
    R = cv2.Rodrigues(np.asarray(p[:3], float))[0]
    return (X - C0) @ R.T * np.exp(p[6]) + C0 + p[3:6]


def model_contour(p, kind):
    pc, f = cams['top']
    if kind == 'rim':
        W = apply(p, RIM @ R0.T + t0)
        uv, z = CM.project(W, pc[:3], pc[3:6], f)
        return np.r_[uv, uv[:1]], float(np.median(z)) / f
    W = apply(p, TRI.reshape(-1, 3) @ R0.T + t0)
    uv, z = CM.project(W, pc[:3], pc[3:6], f)
    m = np.zeros((3000, 4096), np.uint8)
    cv2.fillPoly(m, list(np.round(uv.reshape(-1, 3, 2)).astype(np.int32)), 1)
    c = max(cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)
    return c[:, 0, :].astype(float), float(np.median(z)) / f


def photo_contour(path):
    """Згори шолом яскравий на темному тлі - низький поріг THR (Оцу різав сам шолом по відблиску) + найбільша зв'язна
    область + відкриття (прибрати волокна юбки). rembg тут захоплював шматок фону
    збоку (перевірено на nabir-1005-001), тому не він."""
    g = cv2.GaussianBlur(cv2.imread(path, 0), (0, 0), 3)
    m = (g > THR).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41)))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    m = (lab == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))).astype(np.uint8)
    c = max(cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)
    m = cv2.drawContours(np.zeros_like(m), [c], -1, 1, -1)       # без дірок
    c = max(cv2.findContours((m > 0).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0],
            key=cv2.contourArea)
    return c[:, 0, :].astype(float), m


def contour_gap(a, b, mm):
    """Симетрична відстань між двома замкненими контурами, мм: середня і 90 %."""
    da = cKDTree(b).query(a)[0]
    db = cKDTree(a).query(b)[0]
    d = np.r_[da, db] * mm
    return np.median(d), np.percentile(d, 90)


if __name__ == '__main__':
    out_dir = os.path.join(BASE, 'out_top_silhouette')
    os.makedirs(out_dir, exist_ok=True)
    for n in ('nabir-1005-001', 'nabir-1005-002'):
        truth = ring(os.path.join(S21, 'archive', n, 'ground_truth.ls'))
        m3 = ring(os.path.join(S21, 'data', 'generated', f'{n}_method3.LS'))
        poses = {'nominal': np.zeros(7), 'truth': pose_to(truth), 'method3': pose_to(m3)}
        pc_, mask = photo_contour(os.path.join(S21, 'archive', n, 'top.png'))
        img = cv2.cvtColor(cv2.imread(os.path.join(S21, 'archive', n, 'top.png'), 0), cv2.COLOR_GRAY2BGR)
        cv2.polylines(img, [pc_.astype(np.int32)], True, (255, 255, 255), 3)
        print(f'=== {n}')
        for name, p in poses.items():
            d3 = cKDTree(dense(truth)).query(apply(p, REF))[0]
            row = [f'кільце від правди: {d3.mean():.2f} мм']
            for kind in ('mesh', 'rim'):
                mc, mm = model_contour(p, kind)
                g, g90 = contour_gap(pc_, contour_fit.resample(mc, 2000), mm)
                row.append(f'{kind}: медіана {g:.2f} (90% {g90:.2f})')
                if kind == 'mesh':
                    col = {'nominal': (128, 128, 128), 'truth': (0, 220, 0), 'method3': (0, 0, 255)}[name]
                    cv2.polylines(img, [mc.astype(np.int32)], True, col, 3)
            print(f'  {name:8s}: ' + ', '.join(row))
        cv2.imwrite(os.path.join(out_dir, f'{n}_top.jpg'), cv2.resize(img, (1365, 1000)))
