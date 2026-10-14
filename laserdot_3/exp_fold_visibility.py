"""Чи ВИДНО лінію згину з кожної камери, чи її закриває сам шолом (14.10).

Лінія згину ~ правильне кільце різу (зазор ~2 мм не важливий для видимості). Для кожної
точки кільця - промінь до камери; якщо він перетинає 3D-модель шолома (helmet_ref.stl у
правильній позі цього шолома) - точку не видно. Плюс кут, під яким камера дивиться на
поверхню біля точки: при дуже косому погляді лінію на фото не розгледіти.
Камери: back, left, top (реальні) і right (уявна - дзеркало left на протилежний бік).

    python exp_fold_visibility.py
"""
import os
import sys

import cv2
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import exp_top_silhouette as T  # noqa: E402


def right_cam():
    pc, f = T.cams['left']
    c = T.REF.mean(0)
    R = cv2.Rodrigues(pc[:3])[0]
    M, D = np.diag([1.0, -1.0, 1.0]), np.diag([-1.0, 1.0, 1.0])
    return np.r_[cv2.Rodrigues(D @ R @ M)[0].ravel(), M @ (pc[3:6] - c) + c], f


def occluded(P, C, tri, eps=20.0):
    """Möller-Trumbore: чи перетинає відрізок P->C якийсь трикутник далі ніж eps від P.
    eps=20 мм: точка лежить на стінці самої моделі (і модель не точно збігається з
    шоломом), тож перетини поруч із точкою - це її власна стінка, а не купол, що
    закриває огляд (з eps=1.5 «закритими» виходили 50-80 % - помилка вимірника)."""
    v0, v1, v2 = tri[:, 0], tri[:, 1], tri[:, 2]
    e1, e2 = v1 - v0, v2 - v0
    out = np.zeros(len(P), bool)
    for i, p in enumerate(P):
        d = C - p
        L = np.linalg.norm(d)
        d = d / L
        h = np.cross(d, e2)
        a = (e1 * h).sum(1)
        ok = np.abs(a) > 1e-9
        fa = np.where(ok, 1.0 / np.where(ok, a, 1), 0)
        s = p - v0
        u = fa * (s * h).sum(1)
        q = np.cross(s, e1)
        v = fa * (q * d).sum(1)
        t = fa * (e2 * q).sum(1)
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > eps) & (t < L)
        out[i] = hit.any()
    return out


if __name__ == '__main__':
    cams = dict(T.cams, right=right_cam())
    for n in ('nabir-1005-001', 'nabir-1005-002'):
        truth = T.ring(os.path.join(T.S21, 'archive', n, 'ground_truth.ls'))
        p = T.pose_to(truth)
        tri = T.apply(p, T.TRI.reshape(-1, 3) @ T.R0.T + T.t0).reshape(-1, 3, 3)
        # нормаль поверхні біля точки - найближчий трикутник моделі
        cent = tri.mean(1)
        nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
        from scipy.spatial import cKDTree
        _, j = cKDTree(cent).query(truth)
        c0 = truth.mean(0)
        ang = np.degrees(np.arctan2(truth[:, 1] - c0[1], truth[:, 0] - c0[0]))
        print(f'=== {n} (точок кільця {len(truth)})')
        for w in ('back', 'left', 'top', 'right'):
            pc, f = cams[w]
            C = pc[3:6]
            occ = occluded(truth, C, tri)
            view = (C - truth) / np.linalg.norm(C - truth, axis=1, keepdims=True)
            cosang = np.abs((view * nrm[j]).sum(1))           # 1 = дивимось прямо, 0 = по дотичній
            good = ~occ
            secs = []
            for lo in range(-180, 180, 45):
                k = (ang >= lo) & (ang < lo + 45)
                secs.append(f'{lo:+d}:{good[k].mean()*100:3.0f}%')
            print(f'  {w:5s}: видно {good.mean()*100:3.0f}% кільця (закрито куполом {occ.mean()*100:3.0f}%) | по секторах: ' + ' '.join(secs))
