"""Шаг 4: замер шести слепых наборов штатной метрикой.

Критерии объявлены до прогона (протокол HANDOFF 6): метрика - расстояние
точка->кривая между ЛИНИЯМИ РЕЗА, показатели - среднее, p90, максимум и доля
точек в допуске 2 мм, и обязательны две базы:

  "ничего не делать"      одна фиксированная программа на все шлемы. Какая именно -
                          выбрано по TRAIN штатным evaluate.fixed_baselines();
  "ближайший сосед как есть"  программа выбранной опоры без нашей поправки. Она
                          показывает, что добавила именно математика, а не удачный
                          выбор соседа.

Всё считается функциями evaluate.py, а не своими копиями: любая самодельная
метрика в этом проекте уже дважды оказывалась мерящей не то.
"""
import os
import sys
import json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import lsgeom      # noqa: E402
import evaluate    # noqa: E402
import dataset     # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SESS = json.load(open(os.path.join(HERE, 's6_sessions.json')))
SESS['v20'] = 'run_20260810_125404'          # прогнан руками через веб-интерфейс
ORDER = ['v20', 'v21', 'v22', 'v23', 'v24', 'v25']
FORM = {'v20': 1, 'v21': 1, 'v22': 4, 'v23': 4, 'v24': 1, 'v25': 1}


def stats(pred, gt):
    d = lsgeom.curve_distance(pred, gt)
    return dict(mean=float(d.mean()), p90=float(np.percentile(d, 90)),
                mx=float(d.max()), within=float((d <= 2.0).mean() * 100))


rows = {}
for v in ORDER:
    sd = os.path.join(BASE, 'results', SESS[v])
    p = lsgeom.export_path(sd)
    assert p, f'{v}: экспорт не найден'
    prog = lsgeom.load(p)
    probs = prog.problems() or ([] if len(prog.order) >= 90 else ['мало команд'])
    st4 = json.load(open(os.path.join(sd, 'step04_result.json'), encoding='utf-8'))

    G = evaluate.gt_contour(v)
    ours = lsgeom.cut_surface(prog, evaluate.NOMINAL)[0]
    nb = st4['etalon']
    rows[v] = dict(
        nb=nb, dist=st4['nearest_distance'], oor=st4['out_of_range'],
        probs=probs, n=len(prog.order),
        ours=stats(ours, G),
        nothing=stats(evaluate.gt_contour(evaluate.FIXED), G),
        neigh=stats(evaluate.gt_contour(nb), G))

print()
print("ШЕСТЬ СЛЕПЫХ НАБОРОВ. Ошибка против программы оператора, по линии реза, мм")
print(f'база "ничего не делать" = {evaluate.FIXED} (выбрана по TRAIN)')
print("=" * 88)
print(f"{'':<6}{'форма':>6}{'опора':>7}{'дист':>7}{'':<3}"
      f"{'':<22}{'среднее':>9}{'p90':>7}{'макс':>8}{'≤2 мм':>8}")
print("-" * 88)
for v in ORDER:
    r = rows[v]
    head = f"{v:<6}{FORM[v]:>6}{r['nb']:>7}{r['dist']:>7.1f}{'':<3}"
    for key, name in (('nothing', 'ничего не делать'),
                      ('neigh', 'сосед как есть'),
                      ('ours', 'ПАЙПЛАЙН')):
        s = r[key]
        print(f"{head if key == 'nothing' else '':<25}{name:<22}"
              f"{s['mean']:>9.2f}{s['p90']:>7.2f}{s['mx']:>8.2f}{s['within']:>7.0f}%")
    print("-" * 88)

print()
print("Свод по шести:")
for key, name in (('nothing', 'ничего не делать'), ('neigh', 'сосед как есть'),
                  ('ours', 'ПАЙПЛАЙН')):
    m = np.mean([rows[v][key]['mean'] for v in ORDER])
    mx = max(rows[v][key]['mx'] for v in ORDER)
    w = np.mean([rows[v][key]['within'] for v in ORDER])
    print(f"  {name:<22} среднее {m:>6.2f}   худший максимум {mx:>6.2f}   "
          f"в допуске {w:>4.0f}%")

print()
print("Предсказывает ли out_of_range реальную ошибку:")
for v in ORDER:
    print(f"  {v}: дистанция {rows[v]['dist']:>5.1f}, флаг "
          f"{'ДА' if rows[v]['oor'] else 'нет'}, ошибка {rows[v]['ours']['mean']:.2f} мм")
d = np.array([rows[v]['dist'] for v in ORDER])
e = np.array([rows[v]['ours']['mean'] for v in ORDER])
print(f"  корреляция дистанции с ошибкой по шести: {np.corrcoef(d, e)[0, 1]:+.2f}")

print()
print("Валидность файлов:", ", ".join(
    f"{v}: {rows[v]['n']} команд{'' if not rows[v]['probs'] else ' ' + str(rows[v]['probs'])}"
    for v in ORDER))

json.dump(rows, open(os.path.join(HERE, 's7_results.json'), 'w'), indent=1)
