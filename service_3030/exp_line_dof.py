"""Что именно линия знает о позе - и видел ли её 5056 раньше.

Два вопроса заказчика, оба проверяемые.

1. Могла ли модель 5056 уже брать эту линию? Признаки там строятся по МАСКЕ
   силуэта, а у боковых видов маска обрезается на 58 % высоты сверху
   (step03_segment_monochrome, "safe zone cutoff"). Здесь просто печатается, где
   проходит эта отсечка и где лежит размеченная линия.

2. Связана ли линия с записанными программами напрямую? Поза каждого варианта
   относительно эталона берётся из .LS через ICP (то же, что в fit_model), и
   дальше смотрим, какую из шести степеней свободы можно предсказать по одной
   только линии, по одному только силуэту и по обоим вместе. Оценка - с
   выбрасыванием варианта (LOO), иначе на 13 образцах и 48 признаках любая
   регрессия покажет идеал.

Ничего не пишет; service_5056 только читается.
"""
import os
import sys
import numpy as np
import cv2

BASE = os.path.dirname(os.path.abspath(__file__))
S5056 = os.path.abspath(os.path.join(BASE, '..', 'service_5056'))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(S5056, 'scripts'))

import line_features                                    # noqa: E402
import dataset                                          # noqa: E402
import features as feat5056                             # noqa: E402
import fit_model                                        # noqa: E402
from shots import img_path                              # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DOF = ('сдвиг X', 'сдвиг Y', 'сдвиг Z', 'roll', 'pitch', 'yaw')
UNIT = ('мм', 'мм', 'мм', '°', '°', '°')


def cutoff_report(variants, marks):
    """Где обрезается маска и где лежит линия."""
    from step03_segment_monochrome import segment_image
    print('Отсечка маски у боковых видов против положения линии:')
    print(f"   {'вариант':<8}{'ракурс':<7}{'верх купола':>12}{'отсечка':>10}"
          f"{'линия y':>16}   попадает в маску?")
    for v in variants:
        for view in ('back', 'left'):
            mask, _, _, _, _ = segment_image(img_path(v, view), False)
            ys = np.where(mask > 0)[0]
            top, bot = int(ys.min()), int(ys.max())
            line = marks[v][view][:, 1]
            inside = float(np.mean(line <= bot))
            print(f'   {v:<8}{view:<7}{top:>12}{bot:>10}'
                  f'{line.min():>8.0f}..{line.max():<8.0f}   {inside * 100:.0f}%')


def loo_r(X, y, lam):
    """Предсказание с выбрасыванием варианта; возвращает корреляцию и RMSE."""
    n = len(y)
    mu, sd = X.mean(0), X.std(0)
    sd[sd < 1e-9] = 1.0
    Z = (X - mu) / sd
    pred = np.zeros(n)
    for i in range(n):
        m = np.ones(n, bool)
        m[i] = False
        A = Z[m]
        b = y[m] - y[m].mean()
        w = np.linalg.solve(A.T @ A + lam * np.eye(A.shape[1]), A.T @ b)
        pred[i] = Z[i] @ w + y[m].mean()
    r = float(np.corrcoef(pred, y)[0, 1]) if np.std(pred) > 1e-12 else 0.0
    return r, float(np.sqrt(np.mean((pred - y) ** 2)))


def main():
    names = [v for v in dataset.guard_training(dataset.TRAIN) if v != 'v2']
    marks = line_features.load_marks()
    LINE, grid = line_features.build(names)
    F = feat5056.load(names)

    cutoff_report(names[:4], marks)

    piv = np.array([1170.98, 785.15, -191.86])
    ref = names[0]
    for v in names:
        fit_model.transform_from_ref(v, ref)
    Y = np.array([fit_model.pose_between(ref, v, piv, ref) for v in names])
    Y[:, 3:] = np.degrees(Y[:, 3:]) if np.abs(Y[:, 3:]).max() < 1 else Y[:, 3:]

    XL = np.array([LINE[v] for v in names])
    XS = np.array([feat5056.vec(F[v], 'prof') for v in names])
    XB = np.hstack([XS, XL])

    print('\nЧто можно предсказать по признакам, LOO (r — корреляция '
          'предсказания с записанной программой):')
    print(f"   {'степень свободы':<18}{'разброс':>10}"
          f"{'силуэт':>18}{'линия':>18}{'вместе':>18}")
    for j, (name, unit) in enumerate(zip(DOF, UNIT)):
        y = Y[:, j]
        cells = []
        for X in (XS, XL, XB):
            r, rmse = loo_r(X, y, 100.0)
            cells.append(f'r={r:+.2f} ±{rmse:.2f}')
        print(f'   {name:<18}{y.std():>7.2f} {unit:<3}'
              + ''.join(f'{c:>18}' for c in cells))


if __name__ == '__main__':
    main()
