"""Проверка наблюдения заказчика: купол на месте, а внизу деталь отличается?

Два независимых измерения высоты дают, на первый взгляд, разный знак:

  по .LS      линия реза новых наборов ВЫШЕ архивной на 1.6-3.2 мм;
  по фото     верх купола НИЖЕ архивного на 17-36 px в боковом виде.

Если шлем движется как жёсткое тело, обе величины обязаны идти вместе. Проверяется
это на архиве, где шлем заведомо ОДИН И ТОТ ЖЕ: там связь «верх купола в кадре» ->
«высота линии реза» чистая, и она же даёт масштаб мм/px и знак. Затем этой связью
предсказывается высота новых наборов, и расхождение с их настоящей высотой из .LS
показывает, насколько деталь отличается от мастер-шлема ИМЕННО между куполом и
линией реза.

Ничего не подбирается: связь строится только по архиву, шесть наборов лишь
измеряются.
"""
import os
import sys
import json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import fit_model   # noqa: E402
import dataset     # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MODEL = json.load(open(os.path.join(BASE, 'input', 'model_pose.json'), encoding='utf-8'))
PIVOT, ANCHOR = np.array(MODEL['pivot']), MODEL['anchor']
SKIRT = json.load(open(os.path.join(HERE, 's4_skirt.json')))
ARCH = dataset.TRAIN + dataset.HELDOUT

for v in ARCH + dataset.BLIND:
    fit_model.transform_from_ref(v, ANCHOR)
Z = {v: fit_model.pose_between(ANCHOR, v, PIVOT, ANCHOR)[2] for v in ARCH + dataset.BLIND}

print()
print("СВЯЗЬ «верх купола в кадре» <-> «высота линии реза», по архиву (один шлем)")
print("=" * 78)
fit = {}
for view in ('back', 'left'):
    t = np.array([SKIRT[f'{v}/{view}']['top'] for v in ARCH])
    z = np.array([Z[v] for v in ARCH])
    k, b = np.polyfit(z, t, 1)
    r = np.corrcoef(z, t)[0, 1]
    resid = t - (k * z + b)
    fit[view] = (k, b, resid.std())
    print(f"  {view:<5} наклон {k:>7.1f} px на мм  (масштаб {abs(1 / k):.3f} мм/px), "
          f"корреляция {r:>+5.2f}, разброс вокруг связи {resid.std():.1f} px")
print()
print("  знак: отрицательный наклон = шлем выше -> верх купола выше в кадре (y меньше),")
print("  это физически правильно и подтверждает, что оси согласованы.")

print()
print("Новые наборы: где купол ОКАЗАЛСЯ и где он ДОЛЖЕН БЫ быть при их высоте")
print("=" * 78)
print(f"{'':<7}{'Z из .LS':>10}{'':<3}"
      + "".join(f"{v + ' факт':>11}{v + ' ожид':>11}{'разница':>9}" for v in ('back',)))
print("-" * 78)
for v in dataset.BLIND:
    row = f"{v:<7}{Z[v]:>10.2f}{'':<3}"
    for view in ('back', 'left'):
        k, b, s = fit[view]
        exp = k * Z[v] + b
        got = SKIRT[f'{v}/{view}']['top']
        row += f"{got:>8.0f}{exp:>9.0f}{got - exp:>+8.0f}"
    print(row + "   px: факт / ожидаемый / разница, back затем left")

print()
print("То же в миллиметрах — насколько купол новых деталей ниже, чем требует их посадка:")
for view in ('back', 'left'):
    k, b, s = fit[view]
    d = [(SKIRT[f'{v}/{view}']['top'] - (k * Z[v] + b)) * abs(1 / k) for v in dataset.BLIND]
    print(f"  {view:<5} {np.mean(d):>+6.2f} мм в среднем "
          f"(от {min(d):+.2f} до {max(d):+.2f}), шум связи на архиве ±{s * abs(1 / k):.2f} мм")

print()
print("Для сравнения — то же для НИЗА силуэта (край необрезанного кевлара):")
for view in ('back', 'left'):
    t = np.array([SKIRT[f'{v}/{view}']['bottom'] for v in ARCH])
    z = np.array([Z[v] for v in ARCH])
    k2, b2 = np.polyfit(z, t, 1)
    s2 = (t - (k2 * z + b2)).std()
    kk = fit[view][0]
    d = [(SKIRT[f'{v}/{view}']['bottom'] - (k2 * Z[v] + b2)) * abs(1 / kk)
         for v in dataset.BLIND]
    print(f"  {view:<5} {np.mean(d):>+6.2f} мм в среднем "
          f"(от {min(d):+.2f} до {max(d):+.2f}), шум связи на архиве "
          f"±{s2 * abs(1 / kk):.2f} мм")
