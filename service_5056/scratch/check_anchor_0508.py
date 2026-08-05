"""Q11 задним числом: сдвинулась ли съёмочная установка между 27-30.07 и 05.08?

Шлем из съёмки 05.08 — тот же физический экземпляр, что и v1..v16. Значит его можно
использовать как якорь. Тем же способом, что и для шлемов с форм (§4b): раскладываем
отклонение на объяснимое позой и поперечное. Поперечное для ТОГО ЖЕ шлема обязано
быть на уровне шума метода; если оно велико — уехала установка.
"""
import os, sys, json
import numpy as np
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import features, dataset
from step03_segment_monochrome import segment_image
import cv2

MODEL = json.load(open(os.path.join(BASE,'input','model_pose.json'), encoding='utf-8'))
SCALE = np.array(MODEL['knn_scale'], float)

def measure(d):
    prof=[]
    for name, is_top in features.VIEWS:
        mask,_,_,_,_ = segment_image(os.path.join(d, f'{name}.png'), is_top)
        M = cv2.moments(mask); cx, cy = M['m10']/M['m00'], M['m01']/M['m00']
        c = max(cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0],
                key=cv2.contourArea)[:,0,:].astype(float)
        ang = np.arctan2(c[:,1]-cy, c[:,0]-cx); rad = np.hypot(c[:,0]-cx, c[:,1]-cy)
        o = np.argsort(ang); grid = np.linspace(-np.pi, np.pi, features.N_BINS, endpoint=False)
        prof.append([cx, cy] + list(np.interp(grid, ang[o], rad[o], period=2*np.pi)))
    return np.array([x for row in prof for x in row], float)

LIB = dataset.ALL
F = features.load(LIB)
X = np.array([features.vec(F[v],'prof')/SCALE for v in LIB])
mu = X.mean(0); _,_,Vt = np.linalg.svd(X-mu, full_matrices=False); P = Vt[:6]

def orth(y):
    r = y - mu
    return float(np.linalg.norm(r - P.T @ (P @ r)))

floor=[]
for i,v in enumerate(LIB):
    rest = np.delete(X,i,axis=0); m2 = rest.mean(0)
    _,_,V2 = np.linalg.svd(rest-m2, full_matrices=False); P2=V2[:6]
    r = X[i]-m2; floor.append(float(np.linalg.norm(r - P2.T @ (P2 @ r))))

y = measure(os.path.join(BASE,'input','photos_current'))/SCALE
print(f"шум метода (тот же шлем, LOO по 16 архивным): среднее {np.mean(floor):.1f}, макс {max(floor):.1f}")
print(f"съёмка 05.08, тот же физический шлем        : {orth(y):.1f}")
print()
forms = json.load(open(os.path.join(BASE,'results','_forms_features.json'), encoding='utf-8'))
for n in sorted(forms):
    print(f"  для сравнения, {n:<10} (другие шлемы, 03.08): {orth(features.vec(forms[n],'prof')/SCALE):.1f}")
