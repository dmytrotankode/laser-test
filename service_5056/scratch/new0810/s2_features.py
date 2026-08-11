"""Шаг 1b: штатная сегментация наборов 10.08 и расстояние до библиотеки.

Пайплайн не запускается и ничего не подбирается - считается ровно та величина,
по которой step04 выбирает опору, чтобы увидеть, лежат ли новые съёмки в
диапазоне библиотеки. Веса, пороги и библиотека берутся из model_pose.json как
есть, ни одна константа не пересчитывается.

Код признаков НЕ копируется: берётся step04.build_feature_vector - тот самый,
который работает в эксплуатации. Копия кода признаков уже однажды потребовала
побайтовой сверки с features.py, и повторять это незачем.

Маски сохраняются картинками: заказчик дважды находил артефакты глазами там, где
цифры выглядели правдоподобно.
"""
import os
import sys
import json
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
from step03_segment_monochrome import segment_image   # noqa: E402
from step04_fit_3d_pose import build_feature_vector   # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DATA = os.path.join(BASE, 'results', '_new0810')
OUTJSON = os.path.join(HERE, 's2_features.json')

# Опознано глазами по s1_contact.png. Порядок съёмки РАЗНЫЙ в трёх группах и ни в
# одной, кроме v20, не совпадает с архивным 1=back,2=left,3=top.
VIEWS_OF = {
    'v20': {'back': 'shot1', 'left': 'shot2', 'top': 'shot3'},
    'v21': {'top': 'shot1', 'left': 'shot2', 'back': 'shot3'},
    'v22': {'left': 'shot1', 'top': 'shot2', 'back': 'shot3'},
    'v23': {'left': 'shot1', 'top': 'shot2', 'back': 'shot3'},
    'v24': {'top': 'shot1', 'left': 'shot2', 'back': 'shot3'},
    'v25': {'top': 'shot1', 'left': 'shot2', 'back': 'shot3'},
}
IS_TOP = {'back': False, 'left': False, 'top': True}

MODEL = json.load(open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8'))
LIB = MODEL['library']
SCALE = np.array(MODEL['knn_scale'])
THR = MODEL['out_of_range_threshold']

feats = {}
if os.path.exists(OUTJSON):
    feats = {k: np.array(v) for k, v in json.load(open(OUTJSON)).items()}

for var, views in VIEWS_OF.items():
    if var in feats:
        continue
    masks = {}
    for view, shot in views.items():
        src = os.path.join(DATA, var, f'{shot}.png')
        m, _, _, _, backend = segment_image(src, IS_TOP[view])
        assert backend != 'otsu', f'{var}/{view}: сегментация ушла на Otsu'
        cv2.imwrite(os.path.join(DATA, var, f'mask_{view}.png'), m)
        masks[view] = m
        print(f'  {var}/{view} <- {shot}  ({backend})', flush=True)
    feats[var] = build_feature_vector(masks, 'prof')

json.dump({k: list(map(float, v)) for k, v in feats.items()},
          open(OUTJSON, 'w'), indent=1)

print()
print("Расстояние до библиотеки (та же формула, что в step04)")
print(f"порог out_of_range = {THR:.2f}")
print("=" * 72)
print(f"{'вариант':<9}{'ближайший':>11}{'дистанция':>11}{'2-й':>8}{'дист':>8}"
      f"{'вне диапазона':>16}")
print("-" * 72)

rows = {}
for var, f in feats.items():
    d = {v: float(np.linalg.norm((f - np.array(e['feat'])) / SCALE))
         for v, e in LIB.items()}
    rk = sorted(d.items(), key=lambda kv: kv[1])
    rows[var] = d
    flag = 'ДА' if rk[0][1] > THR else 'нет'
    print(f"{var:<9}{rk[0][0]:>11}{rk[0][1]:>11.2f}{rk[1][0]:>8}{rk[1][1]:>8.2f}"
          f"{flag:>16}")

print()
print("Внутренняя структура библиотеки для сравнения:")
lv = list(LIB)
inner = []
for i, a in enumerate(lv):
    for b in lv[i + 1:]:
        inner.append(np.linalg.norm(
            (np.array(LIB[a]['feat']) - np.array(LIB[b]['feat'])) / SCALE))
inner = np.array(inner)
nn = [min(np.linalg.norm((np.array(LIB[a]['feat']) - np.array(LIB[b]['feat'])) / SCALE)
          for b in lv if b != a) for a in lv]
print(f"  все пары внутри библиотеки: {inner.min():.2f} - {inner.max():.2f}")
print(f"  расстояние до СВОЕГО ближайшего: {min(nn):.2f} - {max(nn):.2f}")

print()
print("Общая ли часть отклонения у всех шести (признак сдвига съёмочной установки):")
D = np.array([feats[v] for v in VIEWS_OF])
L = np.array([LIB[v]['feat'] for v in lv])
centre = L.mean(0)
off = (D - centre) / SCALE
common = off.mean(0)
print(f"  норма общего смещения всех шести от центра библиотеки: "
      f"{np.linalg.norm(common):.2f}")
print(f"  норма индивидуальной части: "
      f"{', '.join(f'{v}={np.linalg.norm(o - common):.2f}' for v, o in zip(VIEWS_OF, off))}")
print(f"  для сравнения, разброс самой библиотеки вокруг центра: "
      f"{np.linalg.norm((L - centre) / SCALE, axis=1).mean():.2f}")
