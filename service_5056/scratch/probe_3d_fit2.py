"""Повторная, более честная подгонка CAD-меша к записанной линии реза.

Первая версия стартовала из одного положения и могла застрять. Здесь много
стартов: развороты вокруг вертикали через 20 градусов плюс переворот, из каждого
ICP, берётся лучший. Если и так остаток велик — вывод настоящий.
"""
import os, sys
import numpy as np
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import lsgeom
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation as R

anchor = lsgeom.load(os.path.join(BASE,'input','archive','v1','ground_truth.ls'))
REF,_ = lsgeom.cut_surface(anchor, lsgeom.NOMINAL_STANDOFF)
def cutline(v):
    p = lsgeom.load(os.path.join(BASE,'input','archive',v,'ground_truth.ls'))
    so,_ = lsgeom.fit_standoff(p, REF)
    return lsgeom.cut_surface(p, so)[0]

d = np.fromfile(os.path.join(BASE,'input','model_3d','helmet_ref.stl'), dtype=np.uint8)
n = int(np.frombuffer(d[80:84], dtype='<u4')[0])
tri = np.frombuffer(d[84:84+n*50].reshape(n,50)[:,12:48].tobytes(), dtype='<f4').reshape(n,3,3).astype(float)
pts=[tri.reshape(-1,3), tri.mean(1)]
for a,b in ((0,1),(1,2),(2,0)): pts.append((tri[:,a]+tri[:,b])/2)
CLOUD = np.unique(np.vstack(pts).round(2), axis=0)

def icp_from(C0, P, iters=60):
    C = C0.copy()
    for _ in range(iters):
        j = cKDTree(C).query(P)[1]
        Rm,t = lsgeom.kabsch(C[j], P)
        C = C @ Rm.T + t
    return cKDTree(C).query(P)[0], C

print("Много стартов: разворот вокруг вертикали 0..340 через 20 гр., прямо и вверх ногами\n")
for v in ('v1','v13'):
    P = cutline(v)
    best=None
    base = CLOUD - CLOUD.mean(0)
    for flip in (0,180):
        for yaw in range(0,360,20):
            M = R.from_euler('ZX',[yaw,flip],degrees=True).apply(base) + P.mean(0)
            dist,_ = icp_from(M,P)
            if best is None or dist.mean()<best[0]:
                best=(float(dist.mean()), float(np.percentile(dist,90)), float(dist.max()), yaw, flip)
    print(f"{v}: лучший остаток {best[0]:.2f} сред / {best[1]:.2f} p90 / {best[2]:.2f} макс "
          f"(старт yaw={best[3]}, flip={best[4]})")

# для сравнения: насколько хорошо ложится сама линия реза на линию реза другого варианта
P1, P2 = cutline('v1'), cutline('v13')
Rm,t = lsgeom.icp(P1,P2)
e = lsgeom.curve_distance(P1@Rm.T+t, P2)
print(f"\nдля сравнения, v1 к v13 (одна и та же деталь): {e.mean():.2f} сред / {e.max():.2f} макс")
