"""Помогает ли линия прессования предсказывать позу в 5056.

Опыт, а не изменение сервиса. Код 5056 отсюда только ЧИТАЕТСЯ и импортируется:
берётся его собственная перекрёстная проверка `fit_model.loo_error`, тот же
подбор соседа, та же метрика по линии реза. Иначе цифру не с чем сравнивать.

Что проверяется: к 150 признакам силуэта добавляются 48 чисел - высота линии
прессования в фиксированных колонках back и left. Если LOO падает, линия несёт
о позе то, чего в очертании нет.

Ограничения, которые здесь соблюдаются намеренно:

* обучающая выборка только dataset.TRAIN, через dataset.guard_training;
  held-out (v6, v13) и слепые (v20-v25) не читаются вообще;
* v2 выпадает: разметки на нём нет. Поэтому ОБА варианта, и базовый и с линией,
  считаются на одном и том же наборе без v2 - иначе сравнивать было бы нельзя;
* ничего не пишется ни в service_5056, ни в модель. Только печать.

    python exp_line_pose.py
"""
import os
import sys
import types
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
S5056 = os.path.abspath(os.path.join(BASE, '..', 'service_5056'))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(S5056, 'scripts'))

import line_features                                    # noqa: E402
import dataset                                          # noqa: E402
import features as feat5056                             # noqa: E402
import fit_model                                        # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

LAMBDAS = (1, 10, 100, 1000)


def make_shim(kind_line='prof_line'):
    """Подменяем features так, чтобы появился признак 'prof' + линия.

    Сам модуль 5056 при этом не меняется: fit_model обращается к нему через имя
    `fit_model.features`, и достаточно подставить объект с теми же двумя
    функциями. Обратно возвращается оригинал в конце работы.
    """
    def vec(entry, kind):
        if kind == kind_line:
            return np.concatenate([feat5056.vec(entry, 'prof'),
                                   np.asarray(entry['line'], float)])
        return feat5056.vec(entry, kind)
    return types.SimpleNamespace(vec=vec, load=feat5056.load)


def main(n_null=0):
    names = [v for v in dataset.guard_training(dataset.TRAIN)]
    dropped = [v for v in names if v == 'v2']
    names = [v for v in names if v != 'v2']
    print(f'Выборка: {len(names)} вариантов — {", ".join(names)}')
    if dropped:
        print(f'Выпал за отсутствием разметки: {", ".join(dropped)} '
              f'(его снимки совпадают с v1 с точностью до шума матрицы)')

    LINE, grid = line_features.build(names)
    print(f'Признаки линии: {len(next(iter(LINE.values())))} чисел '
          f'({line_features.N_COLS} колонок × {len(line_features.VIEWS)} ракурса)')
    for view, g in grid.items():
        print(f'   {view}: колонки {g[0]:.0f}..{g[-1]:.0f} px')

    F = feat5056.load(names)
    for v in names:
        F[v]['line'] = [float(x) for x in LINE[v]]

    piv = np.array([1170.98, 785.15, -191.86])      # точка поворота из model_pose.json
    ref = names[0]
    print('\nПодгонка ICP каждого варианта к эталону...')
    for v in names:
        fit_model.transform_from_ref(v, ref)
    POSE = {(x, y): fit_model.pose_between(x, y, piv, ref)
            for x in names for y in names if x != y}

    fit_model.features = make_shim()
    print(f"\n{'признаки':12s}{'lambda':>8s}{'LOO ближ.':>12s}{'LOO худш.':>12s}")
    out = {}
    for kind in ('prof', 'prof_line'):
        for lam in LAMBDAS:
            per = fit_model.loo_error(names, F, kind, lam, POSE, piv)
            m = float(np.mean([r['nearest'] for r in per.values()]))
            w = float(np.max([r['nearest'] for r in per.values()]))
            out[(kind, lam)] = (m, w, per)
            print(f'{kind:12s}{lam:8g}{m:12.2f}{w:12.2f}')

    best = {k: min((v[0], lam) for (kk, lam), v in out.items() if kk == k)
            for k in ('prof', 'prof_line')}
    b0, l0 = best['prof']
    b1, l1 = best['prof_line']
    print(f'\nЛучшее: силуэт {b0:.2f} мм (lambda={l0}), '
          f'силуэт+линия {b1:.2f} мм (lambda={l1}) — '
          f'{"выигрыш" if b1 < b0 else "проигрыш"} {abs(b0 - b1):.2f} мм')

    print('\nПо вариантам, при лучшей lambda каждого:')
    pa, pb = out[('prof', l0)][2], out[('prof_line', l1)][2]
    print(f"   {'вариант':<10}{'силуэт':>10}{'+линия':>10}")
    for v in names:
        print(f"   {v:<10}{pa[v]['nearest']:>10.2f}{pb[v]['nearest']:>10.2f}")

    # Контроль: 48 лишних чисел могут улучшить подгонку сами по себе, просто как
    # добавка ёмкости. Раздаём те же векторы линий ЧУЖИМ вариантам - связь с
    # позой рвётся, размерность и масштаб остаются. Если выигрыш держится и
    # здесь, он не про линию.
    if n_null:
        print(f'\nКонтроль: разметка, приписанная чужим вариантам ({n_null} перестановок)')
        rng = np.random.default_rng(0)
        null = []
        for i in range(n_null):
            perm = list(names)
            while any(a == b for a, b in zip(perm, names)) or perm == names:
                perm = list(rng.permutation(names))
            for v, u in zip(names, perm):
                F[v]['line'] = [float(x) for x in LINE[u]]
            per = fit_model.loo_error(names, F, 'prof_line', l1, POSE, piv)
            m = float(np.mean([r['nearest'] for r in per.values()]))
            null.append(m)
            print(f'   {i + 1:2d}: {m:.2f} мм')
        null = np.array(null)
        print(f'   перемешанная линия: {null.mean():.2f} мм в среднем, '
              f'лучшая из {n_null} — {null.min():.2f}')
        print(f'   настоящая линия {b1:.2f}, силуэт без линии {b0:.2f}; '
              f'перестановок не хуже настоящей: {int((null <= b1).sum())} из {n_null}')


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--null', type=int, default=0,
                    help='сколько перестановок разметки прогнать как контроль')
    main(ap.parse_args().null)
