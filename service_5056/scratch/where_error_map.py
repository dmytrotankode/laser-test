"""Карта ошибки по контуру сверху + профиль высоты, чтобы опознать перед/зад."""
import os
import sys
import numpy as np
import cv2

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import lsgeom     # noqa: E402
import dataset    # noqa: E402
import fit_model as fm   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

raw = np.load(os.path.join(BASE, 'results', '_where_error.npy'), allow_pickle=True).item()
ALL = dataset.TRAIN + dataset.HELDOUT

# усредняем ошибку по углу: у вариантов разная нумерация, общая координата — угол
grid = np.arange(0, 360, 2.0)
acc = []
for v in ALL:
    r = raw[v]
    o = np.argsort(r['ang'])
    acc.append(np.interp(grid, r['ang'][o], r['err'][o], period=360))
err_mean = np.mean(acc, axis=0)
err_held = np.mean([acc[ALL.index(v)] for v in dataset.HELDOUT], axis=0)

G = fm.contour(fm.ANCHOR)
c = G.mean(0)
ga = (np.degrees(np.arctan2(G[:, 1] - c[1], G[:, 0] - c[0])) + 360) % 360
gz = np.interp(grid, np.sort(ga), G[np.argsort(ga), 2], period=360)

print("Профиль высоты Z контура (мм) — низ = вырез, верх = самая высокая кромка:")
lo, hi = int(grid[gz.argmin()]), int(grid[gz.argmax()])
print(f"  самая НИЗКАЯ точка кромки: {gz.min():.0f} мм на угле {lo}°")
print(f"  самая ВЫСОКАЯ точка кромки: {gz.max():.0f} мм на угле {hi}°")
for a in (0, 45, 90, 135, 180, 225, 270, 315):
    print(f"    {a:>3}°  Z={np.interp(a, grid, gz):7.1f}  ошибка {np.interp(a, grid, err_mean):.2f} мм")

# главная ось контура в XY = ось перед-зад
XY = G[:, :2] - c[:2]
w, V = np.linalg.eigh(XY.T @ XY)
long_ax = V[:, np.argmax(w)]
la = (np.degrees(np.arctan2(long_ax[1], long_ax[0])) + 360) % 360
ext = XY @ long_ax
print(f"\nДлинная ось контура (перед-зад) вдоль {la:.0f}° / {(la+180)%360:.0f}°, "
      f"длина {ext.max()-ext.min():.0f} мм")
short_ax = V[:, np.argmin(w)]
exs = XY @ short_ax
print(f"Короткая ось (лево-право) {(np.degrees(np.arctan2(short_ax[1],short_ax[0]))+360)%360:.0f}°, "
      f"ширина {exs.max()-exs.min():.0f} мм")

# --- картинка ---
S, PAD = 3.0, 90
mn, mx = G[:, :2].min(0), G[:, :2].max(0)
Wd = int((mx[0]-mn[0])*S) + 2*PAD
Ht = int((mx[1]-mn[1])*S) + 2*PAD
img = np.full((Ht, Wd, 3), 22, np.uint8)


def px(p):
    return (int((p[0]-mn[0])*S)+PAD, Ht-(int((p[1]-mn[1])*S)+PAD))


ei = np.interp(ga, grid, err_mean)
vmin, vmax = err_mean.min(), err_mean.max()
for i in range(len(G)):
    t = (ei[i]-vmin)/(vmax-vmin+1e-9)
    col = (int(255*(1-t)), int(90+60*(1-t)), int(60+195*t))    # синий -> красный
    cv2.circle(img, px(G[i, :2]), 7, col, -1)
    j = (i+1) % len(G)
    cv2.line(img, px(G[i, :2]), px(G[j, :2]), (70, 70, 70), 1)

# длинная ось
p1 = c[:2] + long_ax*ext.max()
p2 = c[:2] + long_ax*ext.min()
cv2.line(img, px(p1), px(p2), (120, 200, 120), 2)
for a in (0, 90, 180, 270):
    d = np.array([np.cos(np.radians(a)), np.sin(np.radians(a))])
    q = c[:2] + d*(np.abs(XY).max()*1.12)
    cv2.putText(img, f"{a}", px(q), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 150, 150), 2)

k = int(np.argmax([np.degrees(np.arccos(np.clip(
    ((G[i]-G[i-1])@(G[(i+1) % len(G)]-G[i]))/(np.linalg.norm(G[i]-G[i-1])*np.linalg.norm(G[(i+1) % len(G)]-G[i])), -1, 1)))
    for i in range(len(G))]))
cv2.circle(img, px(G[k, :2]), 14, (0, 255, 255), 2)
cv2.putText(img, "rezkiy povorot", (px(G[k, :2])[0]+16, px(G[k, :2])[1]),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
zk = int(gz.argmin())
d = np.array([np.cos(np.radians(grid[zk])), np.sin(np.radians(grid[zk]))])
cv2.putText(img, "nizhe vsego (vyrez)", px(c[:2]+d*np.abs(XY).max()*0.75),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 0), 2)
cv2.putText(img, f"oshibka: siniy {vmin:.1f} -> krasnyy {vmax:.1f} mm (srednee po 16)",
            (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (220, 220, 220), 2)
cv2.putText(img, "vid sverhu, koordinaty stanka XY",
            (12, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (150, 150, 150), 1)

p = os.path.join(BASE, 'results', 'where_error_map.png')
cv2.imwrite(p, img)
print(f"\nкарта: {p}")
