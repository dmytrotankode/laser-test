"""Подготовка съёмки 05.08 к прогону через веб.

Конвертирует .raw -> .png, но СНАЧАЛА строит контактный лист рядом с архивным v1,
чтобы ракурсы можно было сверить глазами: имена файлов доверия не заслуживают,
программа камер нумерует их по индексу камеры, и этот порядок не совпадает с
back/left/top (см. PLAN.md §4b).

    python scratch/import_test1.py            # только конвертация + лист
    python scratch/import_test1.py --install  # ещё и положить в input/photos_current
"""
import os
import sys
import shutil
import numpy as np
import cv2

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ROOT = os.path.abspath(os.path.join(BASE, '..'))
SRC = os.path.join(ROOT, '05082026_test1')
STAGE = os.path.join(BASE, 'results', '_test1_png')
DEST = os.path.join(BASE, 'input', 'photos_current')
BACKUP = os.path.join(BASE, 'input', '_photos_current_backup')
W, H = 4096, 3000
VIEWS = ('back', 'left', 'top')

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

os.makedirs(STAGE, exist_ok=True)
print("Конвертация:")
for v in VIEWS:
    p = os.path.join(SRC, f'{v}.raw')
    d = np.fromfile(p, dtype=np.uint8)
    if d.size != W * H:
        sys.exit(f"{p}: размер {d.size}, ожидался {W*H} (4096x3000 mono8)")
    cv2.imwrite(os.path.join(STAGE, f'{v}.png'), d.reshape(H, W))
    print(f"  {v}.raw -> {v}.png   ok, {W}x{H}")

# контактный лист: сверху архивный v1, снизу новая съёмка
TW = 330
rows = []
for label, folder in (("arhiv v1 (27.07)", os.path.join(BASE, 'input', 'archive', 'v1')),
                      ("novaya syomka 05.08", STAGE)):
    tiles = []
    for v in VIEWS:
        im = cv2.imread(os.path.join(folder, f'{v}.png'), 0)
        h, w = im.shape
        t = cv2.cvtColor(cv2.resize(im, (TW, int(TW * h / w)),
                                    interpolation=cv2.INTER_AREA), cv2.COLOR_GRAY2BGR)
        cv2.putText(t, v, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (90, 220, 255), 2)
        tiles.append(t)
    rows.append((label, tiles))

ph = rows[0][1][0].shape[0]
sheet = np.full((len(rows) * (ph + 30), 3 * TW + 16, 3), 25, np.uint8)
for r, (label, tiles) in enumerate(rows):
    y = r * (ph + 30)
    cv2.putText(sheet, label, (8, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                (200, 200, 200), 2)
    for c, t in enumerate(tiles):
        sheet[y + 28:y + 28 + t.shape[0], c * (TW + 6):c * (TW + 6) + TW] = t
p = os.path.join(STAGE, 'compare_with_v1.png')
cv2.imwrite(p, sheet)
print(f"\nконтактный лист: {p}")

if '--install' in sys.argv:
    if os.path.isdir(DEST) and not os.path.isdir(BACKUP):
        shutil.copytree(DEST, BACKUP)
        print(f"\nстарое содержимое photos_current сохранено в {BACKUP}")
    # переписываем ТОЛЬКО три рабочих ракурса; всё прочее в папке не трогаем
    for v in VIEWS:
        shutil.copy2(os.path.join(STAGE, f'{v}.png'), os.path.join(DEST, f'{v}.png'))
    print(f"установлено в {DEST}: {sorted(os.listdir(DEST))}")
else:
    print("\nсверьте ракурсы на листе, затем запустите с --install")
