"""Сводится ли разница форм к масштабу?

Если шлем с другой формы — просто чуть больше/меньше, то его радиальный профиль
получается из эталонного умножением на одно число. Тогда чинить это можно тем же
параметром d из §4a (смещение вдоль оси сопла работает как масштаб контура),
и отдельная библиотека на каждую форму не нужна.

Меряем: остаток профиля до и после подбора одного масштаба на вид.
Контроль — архивные варианты: там заведомо один шлем, остаток покажет шум.
"""
import os
import sys
import json
import numpy as np

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import features   # noqa: E402
import dataset    # noqa: E402

with open(os.path.join(BASE, 'results', '_forms_features.json'), encoding='utf-8') as f:
    NEW = json.load(f)

LIB = dataset.ALL
F = features.load(LIB)
VIEWS = ("back", "left", "top")


def radii(entry):
    """(3, 48) радиусы профиля в px, без cx/cy."""
    return np.array([row[2:] for row in entry["prof"]], float)


R_lib = np.array([radii(F[v]) for v in LIB])       # (16, 3, 48)
ref = R_lib.mean(0)                                 # эталонный профиль


def fit_scale(r):
    """Один масштаб на вид: s = <r, ref> / <ref, ref>. Остатки до и после, %."""
    out = []
    for i in range(3):
        a, b = r[i], ref[i]
        s = float(a @ b / (b @ b))
        before = np.linalg.norm(a - b) / np.linalg.norm(b) * 100
        after = np.linalg.norm(a - s * b) / np.linalg.norm(b) * 100
        out.append((s, before, after))
    return out


print("Контроль — архивные варианты (один и тот же шлем):")
print(f"{'вар':<7}" + "".join(f"{v+' масшт':>12}{v+' ост.%':>11}" for v in VIEWS))
ctrl = []
for v, r in zip(LIB, R_lib):
    f_ = fit_scale(r)
    ctrl.append([x[2] for x in f_])
    print(f"{v:<7}" + "".join(f"{s:>12.4f}{aft:>11.2f}" for s, _, aft in f_))
ctrl = np.array(ctrl)
print(f"{'СРЕДН':<7}" + "".join(f"{'':>12}{ctrl[:, i].mean():>11.2f}" for i in range(3)))

print("\nНовые шлемы:")
print(f"{'шлем':<12}" + "".join(f"{v+' масшт':>12}{v+' до%':>9}{v+' после%':>11}"
                                for v in VIEWS))
for n in sorted(NEW):
    f_ = fit_scale(radii(NEW[n]))
    print(f"{n:<12}" + "".join(f"{s:>12.4f}{bef:>9.2f}{aft:>11.2f}" for s, bef, aft in f_))

print("\nЧитать так: если 'после' падает почти до уровня контроля — разница формы")
print("это в основном размер, и её берёт один масштабный параметр. Если 'после'")
print("остаётся высоким — форма отличается НЕ размером, а самой геометрией купола.")
