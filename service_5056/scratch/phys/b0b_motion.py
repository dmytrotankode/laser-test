"""Шаг B0, исправленный: движение шлема берётся из СДВИГА КАДРА, а не из
положения камеры.

Первая версия считала движение по тому, куда уехала камера, и получила 30-1230 мм
вместо 2-4. Причина не в данных: в подгонке есть параметры px, py - сдвиг
картинки в кадре, - и они заведены ровно затем, чтобы впитывать смещение. То
есть сигнал сидит в них, а положение камеры относительно них вырождено и
болтается свободно. Смотреть надо на px, py и на изменение дистанции.

Ничего не подгоняется заново - берутся результаты из b0_cams.json.
"""
import os
import sys
import json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
COARSE = 0.20
LIB = json.load(open(os.path.join(BASE, 'input', 'model_pose.json'),
                     encoding='utf-8'))['library']
cams = json.load(open(os.path.join(HERE, 'b0_cams.json'), encoding='utf-8'))

VARIANTS = ['v1', 'v8', 'v11', 'v12', 'v16', 'v10']
VIEWS = ('back', 'left', 'top')


def lateral_mm(v, view):
    """Положение шлема поперёк оси взгляда, мм, из сдвига кадра."""
    p = np.array(cams[f'{v}_{view}']['p'])
    dist, f = np.exp(p[3]), np.exp(p[4])
    mm_per_px = dist / (f * COARSE)
    return np.array([p[5], p[6]]) * mm_per_px, dist


print("Движение шлема относительно v1: по силуэтам против меток ICP")
print("Каждая камера видит только две оси из трёх, поэтому её число - это")
print("ПРОЕКЦИЯ настоящего сдвига, она обязана быть не больше него и меняться вместе.")
print()
print(f"{'вар':<6}{'ICP полный':>12}" + "".join(f"{v:>10}" for v in VIEWS)
      + f"{'по 3 видам':>13}")
print("-" * 63)

icp_all, seen_all = [], []
for v in VARIANTS[1:]:
    icp = (np.array(LIB[v]['pose_vs_anchor'][:3])
           - np.array(LIB['v1']['pose_vs_anchor'][:3]))
    mag = float(np.linalg.norm(icp))
    per = []
    for view in VIEWS:
        if f'{v}_{view}' not in cams or f'v1_{view}' not in cams:
            per.append(float('nan')); continue
        a, _ = lateral_mm(v, view)
        b, _ = lateral_mm('v1', view)
        per.append(float(np.linalg.norm(a - b)))
    # грубая сводка: каждая камера даёт 2 из 3 осей, вместе они переопределены
    comb = float(np.sqrt(np.nanmean(np.array(per) ** 2) * 1.5))
    icp_all.append(mag); seen_all.append(comb)
    print(f"{v:<6}{mag:>10.2f} мм" + "".join(f"{x:>10.2f}" for x in per)
          + f"{comb:>11.2f} мм")

icp_all, seen_all = np.array(icp_all), np.array(seen_all)
r = np.corrcoef(icp_all, seen_all)[0, 1]
print()
print(f"связь величин (корреляция по 5 вариантам): {r:+.2f}")
print(f"типичный масштаб: ICP {icp_all.mean():.2f} мм, по силуэтам {seen_all.mean():.2f} мм")
print()
print("Порядок величин теперь должен совпадать. Если по силуэтам выходит в разы")
print("больше - подгонка гуляет сильнее, чем движется шлем, и одиночный вид позу")
print("не определяет; это как раз то, что должна вылечить общая подгонка B1.")
