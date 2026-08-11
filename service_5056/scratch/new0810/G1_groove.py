"""Канавка, шаг 1: разведка — видна ли граница прессования на снимках.

Заказчик указал на признак, которого не было ни в одной нашей модели: у края
детали идёт тёмная линия — след границы прессования (кевлар выходит за кромку
формы, там остаётся наплыв и ступенька, в ней тень). Оператор, по его словам,
ориентируется именно на неё, и на цеховой проверке 05.08 правил программу как
раз там, где она расходилась с этой линией.

Если это так, задача меняется в корне: вместо "угадать позу шлема по силуэту"
получается "найти на снимке линию, по которой режут". Признак принадлежит самой
детали, поэтому не зависит ни от библиотеки поз, ни от CAD, и не упирается в
потолок переноса чужого контура (0.99 мм).

Здесь ничего не измеряется в миллиметрах - только разведка:
  * видна ли линия и на какой части контура;
  * отличается ли она от прочих тёмных мест (края силуэта, теней, швов);
  * повторяется ли между съёмками одного шлема.

Метод намеренно тупой и прозрачный: канавка - это тёмная борозда, то есть
локальный минимум яркости ВДОЛЬ вертикали, лежащий ниже купола и выше нижнего
края силуэта. Никакого обучения, чтобы результат нельзя было списать на подгонку.
"""
import os
import sys
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(HERE, 'G1_out')
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.join(BASE, 'scripts'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

VARIANTS = ['v1', 'v8', 'v13', 'v20', 'v22', 'v25']
VIEWS = ['back', 'left']


def silhouette_band(img):
    """Грубая полоса поиска: от низа купола до нижнего края детали.

    Сегментация здесь НЕ используется: она обрезает ровно ту зону, которая нам
    нужна (Safe Zone выбрасывает нижние 42 %). Полоса берётся от яркости - тело
    детали заметно светлее фона.
    """
    blur = cv2.GaussianBlur(img, (21, 21), 0)
    body = blur > max(60, int(np.percentile(blur, 60)))
    rows = np.where(body.sum(1) > img.shape[1] * 0.06)[0]
    if len(rows) < 10:
        return None
    top, bot = int(rows.min()), int(rows.max())
    h = bot - top
    return top + int(h * 0.45), bot          # нижняя половина детали


def find_groove(img):
    """Для каждого столбца - строка самой тёмной борозды внутри полосы."""
    band = silhouette_band(img)
    if band is None:
        return None, None
    y0, y1 = band
    strip = cv2.GaussianBlur(img[y0:y1, :], (9, 9), 0).astype(np.int16)

    # борозда: пиксель темнее того, что на 25 px выше И на 25 px ниже
    up = np.roll(strip, 25, axis=0)
    dn = np.roll(strip, -25, axis=0)
    darkness = np.minimum(up - strip, dn - strip)
    darkness[:30, :] = -999
    darkness[-30:, :] = -999

    ys, strength = [], []
    for c in range(strip.shape[1]):
        col = darkness[:, c]
        i = int(np.argmax(col))
        ys.append(y0 + i)
        strength.append(int(col[i]))
    return np.array(ys), np.array(strength)


print()
print("Разведка канавки: доля контура, где борозда видна уверенно")
print("=" * 72)
print(f"{'вариант':<9}{'вид':<7}{'уверенных столбцов':>20}{'медиана глубины':>18}")
print("-" * 72)

for v in VARIANTS:
    for view in VIEWS:
        p = os.path.join(BASE, 'input', 'archive', v, f'{view}.png')
        if not os.path.exists(p):
            continue
        img = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
        ys, st = find_groove(img)
        if ys is None:
            print(f"{v:<9}{view:<7}{'полоса не найдена':>20}")
            continue
        # столбцы, где деталь вообще есть: яркость выше фоновой
        body = cv2.GaussianBlur(img, (21, 21), 0).max(0) > 60
        ok = body & (st > 12)
        frac = ok.sum() / max(body.sum(), 1)
        print(f"{v:<9}{view:<7}{frac * 100:>19.0f}%{np.median(st[ok]) if ok.any() else 0:>18.0f}")

        vis = cv2.cvtColor(cv2.resize(img, (1024, 750)), cv2.COLOR_GRAY2BGR)
        for c in range(0, img.shape[1], 8):
            if ok[c]:
                cv2.circle(vis, (c // 4, ys[c] // 4), 1, (0, 0, 255), -1)
        cv2.putText(vis, f'{v} {view}', (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (0, 255, 0), 2)
        cv2.imwrite(os.path.join(OUT, f'{v}_{view}.png'), vis)

print()
print("Красным отмечено найденное - смотреть G1_out/*.png. Числа сами по себе")
print("ничего не доказывают: борозда могла быть найдена не там, где надо.")
