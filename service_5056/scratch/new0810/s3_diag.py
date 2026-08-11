"""Шаг 1c: ЧЕМ именно новые съёмки отличаются от библиотеки.

Дистанция k-NN - одно число на 150 признаков, и по нему нельзя отличить
"шлем стоит иначе" от "камера видит иначе". Здесь она раскладывается на части,
у каждой из которых свой физический смысл:

  cx, cy        где силуэт в кадре. Сдвиг риги или подъём шлема двигают это;
  средний радиус  размер силуэта. Меняется от дистанции камеры и от того,
                сколько необрезанного кевлара попало в контур;
  форма         профиль после деления на свой средний радиус - то, что не
                объясняется ни сдвигом, ни масштабом.

Заказчик утверждает: камеры закреплены жёстко, фокус откалиброван, но при
перезапуске подстраивается экспозиция. Отсюда прямая проверка яркости кадров:
если сегментация поехала от экспозиции, силуэт "распухнет" или "похудеет"
одинаково по всем шести, а центр останется на месте.
"""
import os
import sys
import json
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MODEL = json.load(open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8'))
LIB = MODEL['library']
NEW = {k: np.array(v) for k, v in
       json.load(open(os.path.join(HERE, 's2_features.json'))).items()}
VIEWS = ('back', 'left', 'top')


def parts(vec):
    """{вид: (cx, cy, радиусы)}"""
    out = {}
    for i, v in enumerate(VIEWS):
        blk = vec[i * 50:(i + 1) * 50]
        out[v] = (blk[0], blk[1], blk[2:])
    return out


libp = {k: parts(np.array(e['feat'])) for k, e in LIB.items()}
newp = {k: parts(v) for k, v in NEW.items()}

print()
print("ШАГ 1c. Из чего складывается отклонение новых съёмок")
print("=" * 78)

for view in VIEWS:
    cx = np.array([libp[k][view][0] for k in libp])
    cy = np.array([libp[k][view][1] for k in libp])
    rr = np.array([libp[k][view][2].mean() for k in libp])
    print(f"\n--- {view} ---")
    print(f"библиотека (14):  cx {cx.mean():8.1f} ±{cx.std():5.1f}   "
          f"cy {cy.mean():8.1f} ±{cy.std():5.1f}   радиус {rr.mean():7.1f} ±{rr.std():5.1f}")
    print(f"{'':<6}{'cx':>10}{'откл σ':>9}{'cy':>10}{'откл σ':>9}"
          f"{'радиус':>10}{'откл σ':>9}")
    for k in newp:
        a, b, r = newp[k][view]
        r = r.mean()
        print(f"{k:<6}{a:>10.1f}{(a - cx.mean()) / cx.std():>9.1f}"
              f"{b:>10.1f}{(b - cy.mean()) / cy.std():>9.1f}"
              f"{r:>10.1f}{(r - rr.mean()) / rr.std():>9.1f}")

print()
print("Форма профиля после снятия масштаба (то, что не объясняется ни сдвигом,")
print("ни размером). Мера - средняя разница нормированных радиусов, %:")
print("-" * 78)
print(f"{'':<6}" + "".join(f"{v:>10}" for v in VIEWS))
for k in newp:
    row = ""
    for view in VIEWS:
        r = newp[k][view][2]
        rn = r / r.mean()
        d = [np.abs(rn - libp[o][view][2] / libp[o][view][2].mean()).mean() * 100
             for o in libp]
        row += f"{min(d):>10.2f}"
    print(f"{k:<6}{row}")

ctl = {}
for view in VIEWS:
    d = []
    ks = list(libp)
    for i, a in enumerate(ks):
        ra = libp[a][view][2] / libp[a][view][2].mean()
        for b in ks[i + 1:]:
            rb = libp[b][view][2] / libp[b][view][2].mean()
            d.append(np.abs(ra - rb).mean() * 100)
    ctl[view] = (np.min(d), np.mean(d), np.max(d))
print(f"{'контр.':<6}" + "".join(f"{ctl[v][1]:>10.2f}" for v in VIEWS)
      + "   <- среднее внутри библиотеки (тот же шлем)")
print(f"{'':<6}" + "".join(f"{ctl[v][2]:>10.2f}" for v in VIEWS)
      + "   <- худшая пара внутри библиотеки")

print()
print("Яркость кадров: подстройка экспозиции при перезапуске камер?")
print("-" * 78)
print(f"{'':<8}{'вид':<7}{'медиана':>9}{'p99':>7}{'доля >200':>11}")
for var in ('v1', 'v8', 'v13'):
    for view in VIEWS:
        p = os.path.join(BASE, 'input', 'archive', var, f'{view}.png')
        g = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
        print(f"{var:<8}{view:<7}{np.median(g):>9.0f}{np.percentile(g, 99):>7.0f}"
              f"{(g > 200).mean() * 100:>10.1f}%")
print("-" * 78)
for var in newp:
    for view in VIEWS:
        p = os.path.join(BASE, 'results', '_new0810', var, f'mask_{view}.png')
        shots = json.load(open(os.path.join(HERE, 's2_views.json'))) \
            if os.path.exists(os.path.join(HERE, 's2_views.json')) else None
        src = os.path.join(BASE, 'results', '_new0810', var,
                           {'v20': {'back': 'shot1', 'left': 'shot2', 'top': 'shot3'},
                            'v21': {'top': 'shot1', 'left': 'shot2', 'back': 'shot3'},
                            'v22': {'left': 'shot1', 'top': 'shot2', 'back': 'shot3'},
                            'v23': {'left': 'shot1', 'top': 'shot2', 'back': 'shot3'},
                            'v24': {'top': 'shot1', 'left': 'shot2', 'back': 'shot3'},
                            'v25': {'top': 'shot1', 'left': 'shot2', 'back': 'shot3'},
                            }[var][view] + '.png')
        g = cv2.imread(src, cv2.IMREAD_GRAYSCALE)
        print(f"{var:<8}{view:<7}{np.median(g):>9.0f}{np.percentile(g, 99):>7.0f}"
              f"{(g > 200).mean() * 100:>10.1f}%")
