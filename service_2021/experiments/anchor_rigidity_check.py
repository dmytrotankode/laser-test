"""Offline-експеримент (не викликається з app.py, ніде не імпортується) - перевірка
ідеї "точка-якір" ДО того, як чіпати pipeline/contour_fit.py.

Питання: реальна ручна правка лінії (points_original -> points у вже порахованому
scene.json) - це по суті ОДНЕ жорстке тіло (поворот+зсув+масштаб), чи ні?

Якщо так - "якір" не додає нічого нового porівняно з тим, що вже є (поворот/зсув
навколо ЦЕНТРОЇДА, як зараз у axisPad): будь-яку точку можна "закріпити" просто
іншою комбінацією тих самих кнопок, бо це одна й та сама жорстка трансформація,
розкладена інакше. Якір тоді вартий лише всередині ОПТИМІЗАТОРА (щоб сама
автоматична підгонка стартувала ближче), не для ручного редагування.

Якщо ж залишок (те, що жорстка трансформація НЕ пояснює) великий - правка
насправді нежорстка (локальна), і ні якір, ні центроїд її не замінять; тоді
вартий уваги варіант "авто-доведення по кліку в двох ракурсах" (номер 3) або
"вибір підмножини точок" (локальний, а не глобальний інструмент).

Запуск:
    python experiments/anchor_rigidity_check.py [scene_name]
"""
import json
import os
import sys

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
SCENES = os.path.join(BASE, '..', 'data', 'scenes')


def kabsch_with_scale(A, B):
    """Найкраща жорстка трансформація (R, t, s), що переводить A -> B:
    B_fit = s * A @ R.T + t. Стандартний Kabsch + окремо підібраний масштаб.
    """
    ca, cb = A.mean(0), B.mean(0)
    A0, B0 = A - ca, B - cb
    H = A0.T @ B0
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1, 1, d])
    R = Vt.T @ D @ U.T
    s = S.sum() / (A0 ** 2).sum() if d == 1 else (D @ S).sum() / (A0 ** 2).sum()
    t = cb - s * (R @ ca)
    return R, t, s


def check(scene_name):
    path = os.path.join(SCENES, scene_name, 'scene.json')
    with open(path, encoding='utf-8') as f:
        doc = json.load(f)
    c = next(x for x in doc['curves'] if x.get('editable'))
    P0 = np.array(c['points_original'], float)   # розрахункове (до правки)
    P1 = np.array(c['points'], float)             # після ручної правки
    raw = np.linalg.norm(P1 - P0, axis=1)
    if raw.max() < 1e-6:
        print(f'{scene_name}: ручних правок немає (points == points_original) - нема що перевіряти')
        return

    R, t, s = kabsch_with_scale(P0, P1)
    P0_fit = s * P0 @ R.T + t
    residual = np.linalg.norm(P1 - P0_fit, axis=1)

    ang = np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))
    print(f'--- {scene_name} ({len(P0)} точок) ---')
    print(f'сира правка (до/після):        середнє {raw.mean():6.2f} мм, макс {raw.max():6.2f} мм')
    print(f'найкраще жорстке тіло:         поворот {ang:5.1f}°, масштаб {s*100:6.2f}%, зсув {np.linalg.norm(t):6.2f} мм')
    print(f'залишок ПІСЛЯ жорсткого тіла:  середнє {residual.mean():6.2f} мм, макс {residual.max():6.2f} мм '
          f'({100*residual.mean()/raw.mean():.0f}% від сирої правки лишається непоясненим)')
    print()


if __name__ == '__main__':
    names = sys.argv[1:] or [d for d in os.listdir(SCENES)
                              if os.path.exists(os.path.join(SCENES, d, 'scene.json'))]
    for name in names:
        try:
            check(name)
        except Exception as e:
            print(f'{name}: пропущено ({e})')
