"""Чи збігається лінія згину з краєм шолома на фото згори (14.10).

Для кожної точки правильного кільця (проекція в top) шукаємо вздовж нормалі до кривої
місце найрізкішого перепаду яскравості (край шолома на фото) в межах ±60 px (~±5 мм).
Відстань від проекції лінії до краю - мм на деталі, по секторах навколо шолома.
Якщо мала й стабільна - край на фото згори можна брати як «розмітку згори» автоматично.

    python exp_top_edge.py
"""
import os
import sys

import cv2
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import exp_top_silhouette as T  # noqa: E402
from pipeline import camera_model as CM  # noqa: E402

pc, f = T.cams['top']


def edge_offsets(img, uv, R=60):
    g = cv2.GaussianBlur(img.astype(np.float32), (0, 0), 2.0)
    gx, gy = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    c = uv.mean(0)
    out = []
    for i, p in enumerate(uv):
        t = uv[(i + 1) % len(uv)] - uv[i - 1]
        nrm = np.array([-t[1], t[0]]) / (np.linalg.norm(t) + 1e-9)
        if nrm @ (p - c) < 0:
            nrm = -nrm                                    # назовні від центру
        s = np.arange(-R, R + 1)
        q = p + s[:, None] * nrm
        x, y = np.clip(q[:, 0], 0, 4095).astype(int), np.clip(q[:, 1], 0, 2999).astype(int)
        grad = -(gx[y, x] * nrm[0] + gy[y, x] * nrm[1])    # світле всередині -> темне назовні
        out.append(s[int(np.argmax(grad))])
    return np.array(out, float)


if __name__ == '__main__':
    for n in ('nabir-1005-001', 'nabir-1005-002'):
        truth = T.ring(os.path.join(T.S21, 'archive', n, 'ground_truth.ls'))
        uv, z = CM.project(truth, pc[:3], pc[3:6], f)
        mm = float(np.median(z)) / f
        img = cv2.imread(os.path.join(T.S21, 'archive', n, 'top.png'), 0)
        off = edge_offsets(img, uv) * mm                     # + = край далі назовні, ніж лінія
        c0 = truth.mean(0)
        ang = np.degrees(np.arctan2(truth[:, 1] - c0[1], truth[:, 0] - c0[0]))
        secs = ' '.join(f'{lo:+d}:{off[(ang >= lo) & (ang < lo + 45)].mean():+.1f}' for lo in range(-180, 180, 45))
        print(f'{n}: край відносно лінії згину/різу (мм, + = назовні): середнє {off.mean():+.2f}, розкид (σ) {off.std():.2f}, '
              f'|макс| {np.abs(off).max():.2f} | по секторах: {secs}')
