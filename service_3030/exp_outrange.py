"""Приближает ли фиксированная строка отсечки чужие шлемы к библиотеке.

По PLAN.md новые съёмки уходят на 16-55 от библиотеки при внутренних разрывах
под 12 - и виновата длина юбки: правило «58 % высоты силуэта» отмеряет от края
необрезанного кевлара, который гуляет на 27-153 px. Фиксированная строка кадра
от юбки не зависит.

Здесь НИЧЕГО не подгоняется и не обучается - только меряется расстояние в том же
пространстве признаков и по тому же правилу, что в step04: разделить на разброс
по библиотеке и взять ближайшего. Порог out_of_range по определению есть
наибольший разрыв до соседа ВНУТРИ библиотеки, он считается тут же.

Слепые наборы используются только как измеряемые точки; их ошибка не читается,
подгонки на них нет. Пишет только в service_3030.
"""
import os
import sys
import json
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
S5056 = os.path.abspath(os.path.join(BASE, '..', 'service_5056'))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(S5056, 'scripts'))

import dataset                                           # noqa: E402
import exp_cutoff as C                                   # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

RULES = [('58 % высоты силуэта', None, None),
         ('строка кадра 1290 / 1610 (та же высота)', 1290, 1610),
         ('строка кадра 1400 / 1750', 1400, 1750)]


def vec(prof):
    return np.array([x for row in prof for x in row], float)


def main():
    lib = list(dataset.TRAIN)
    outside = list(dataset.BLIND)
    cache = json.load(open(C.CACHE, encoding='utf-8')) if os.path.exists(C.CACHE) else {}

    for label, ab, al in RULES:
        V = {}
        for v in lib + outside:
            key = f'{v}|{ab}|{al}'
            if key not in cache:
                cache[key] = C.measure(v, ab, al)
                json.dump(cache, open(C.CACHE, 'w'))
            V[v] = vec(cache[key])
        L = np.array([V[v] for v in lib])
        scale = L.std(0)
        scale[scale < 1e-9] = 1.0

        def nearest(v, pool):
            return min(float(np.linalg.norm((V[v] - V[u]) / scale)) for u in pool)

        gaps = [nearest(v, [u for u in lib if u != v]) for v in lib]
        thr = max(gaps)
        out = {v: nearest(v, lib) for v in outside}
        print(f'--- {label}')
        print(f'    порог (наибольший разрыв внутри библиотеки): {thr:.1f}')
        print('    ' + '  '.join(f'{v} {out[v]:.1f}' for v in outside))
        print(f'    в среднем до библиотеки {np.mean(list(out.values())):.1f}, '
              f'за порогом {sum(d > thr for d in out.values())} из {len(out)}',
              flush=True)


if __name__ == '__main__':
    main()
