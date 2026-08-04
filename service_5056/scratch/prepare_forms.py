"""Этап 4b, шаг 1: raw -> png + признаки профиля силуэта для шлемов из forms/.

Признаки считаются ТОЙ ЖЕ сегментацией (step03.segment_image) и той же формулой
профиля, что и для архивных вариантов. Чтобы это не осталось обещанием, скрипт
сначала пересчитывает v1 своей копией кода и сверяет с results/_features.json —
если копия разошлась с оригиналом, работа останавливается.

Раскладка ракурсов в forms/: 1=back, 2=left, 3=top (подтверждено по серийникам
камер и визуально). PNG-файлы в form1/1 названы по индексу камеры и идут в другом
порядке — они игнорируются.
"""
import os
import sys
import json
import numpy as np
import cv2

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
from step03_segment_monochrome import segment_image   # noqa: E402
import features                                        # noqa: E402

ROOT = os.path.abspath(os.path.join(BASE, '..'))
FORMS = os.path.join(ROOT, 'forms')
STAGE = os.path.join(BASE, 'results', '_forms_png')
OUT = os.path.join(BASE, 'results', '_forms_features.json')

W, H = 4096, 3000
VIEW_BY_INDEX = {1: 'back', 2: 'left', 3: 'top'}
N_BINS = features.N_BINS
VIEWS = features.VIEWS


def measure_dir(d):
    """Копия features._measure, но по произвольной папке. Сверяется с оригиналом ниже."""
    f8, prof = [], []
    for name, is_top in VIEWS:
        path = os.path.join(d, f'{name}.png')
        mask, _, _, _, _ = segment_image(path, is_top)
        M = cv2.moments(mask)
        cx, cy = M["m10"] / M["m00"], M["m01"] / M["m00"]
        clipped = mask.copy()
        clipped[:100, :] = 0
        top_y = float(np.min(np.where(clipped > 0)[0]))
        f8.append((cx, cy, top_y))

        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        c = max(cnts, key=cv2.contourArea)[:, 0, :].astype(float)
        ang = np.arctan2(c[:, 1] - cy, c[:, 0] - cx)
        rad = np.hypot(c[:, 0] - cx, c[:, 1] - cy)
        o = np.argsort(ang)
        grid = np.linspace(-np.pi, np.pi, N_BINS, endpoint=False)
        prof.append([cx, cy] + list(np.interp(grid, ang[o], rad[o], period=2 * np.pi)))
    return {"f8": f8, "prof": prof}


def selftest():
    """Копия кода обязана давать бит-в-бит то же, что кэш признаков архива."""
    ref = features.load(["v1"])["v1"]
    mine = measure_dir(os.path.join(BASE, 'input', 'archive', 'v1'))
    for kind in ("f8", "prof"):
        a = np.array(ref[kind], float).ravel()
        b = np.array(mine[kind], float).ravel()
        d = float(np.abs(a - b).max())
        print(f"  сверка с features.py, {kind}: макс расхождение {d:.2e}")
        if d > 1e-9:
            sys.exit(f"КОПИЯ РАЗОШЛАСЬ С ОРИГИНАЛОМ по {kind} ({d:.3e}). Замер отменён.")
    print("  копия эквивалентна оригиналу\n")


def convert():
    names = []
    for form in sorted(os.listdir(FORMS)):
        fdir = os.path.join(FORMS, form)
        if not os.path.isdir(fdir):
            continue
        for helmet in sorted(os.listdir(fdir)):
            src = os.path.join(fdir, helmet)
            if not os.path.isdir(src):
                continue
            raws = {i: os.path.join(src, f"{i}.raw") for i in (1, 2, 3)}
            if not all(os.path.exists(p) for p in raws.values()):
                print(f"  ПРОПУСК {form}/{helmet}: нет всех трёх .raw")
                continue
            name = f"{form}_h{helmet}"
            dst = os.path.join(STAGE, name)
            os.makedirs(dst, exist_ok=True)
            for i, p in raws.items():
                data = np.fromfile(p, dtype=np.uint8)
                if data.size != W * H:
                    sys.exit(f"{p}: размер {data.size}, ожидался {W*H}")
                out = os.path.join(dst, f"{VIEW_BY_INDEX[i]}.png")
                if not os.path.exists(out):
                    cv2.imwrite(out, data.reshape(H, W))
            names.append(name)
            print(f"  {name}: back/left/top готовы")
    return names


print("Проверка, что сегментатор — rembg, а не откат на Otsu:")
m, _, _, _, backend = segment_image(
    os.path.join(BASE, 'input', 'archive', 'v1', 'back.png'), False)
print(f"  backend = {backend}")
if backend != "rembg":
    sys.exit("Сегментация ушла на Otsu — все калибровочные константы недействительны.")
print()

print("Сверка копии кода признаков с features.py:")
selftest()

print("Конвертация forms/ -> png:")
names = convert()
print()

print("Признаки (сегментация ~1.6 с на кадр):")
res = {}
for n in names:
    print(f"  {n} ...", flush=True)
    res[n] = measure_dir(os.path.join(STAGE, n))

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(res, f)
print(f"\nЗаписано: {OUT}  ({len(res)} шлемов)")
