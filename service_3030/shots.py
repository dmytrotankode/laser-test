"""Где лежат снимки. Общее для веб-интерфейса и для замеров.

Раньше путь до снимка знал только app.py, а tune.py искал всё в archive - и
молча не находил цеховую съёмку 05.08, которая лежит отдельно. Подбор шёл по
трём снимкам вместо пяти, причём без единого предупреждения.
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ARCHIVE = os.path.abspath(os.path.join(BASE, '..', 'service_5056', 'input', 'archive'))
LINES = os.path.join(BASE, 'data', 'lines')

# Съёмки не из архива. Цеховая 05.08 - единственная, где есть и наша программа, и
# правки оператора поверх неё, и видео самого реза: по ней можно свериться с тем,
# как линия идёт на самом деле, а не только с тем, как её видно на снимке.
EXTRA = {
    'shop_05.08': os.path.abspath(os.path.join(
        BASE, '..', 'service_5056', 'scratch', 'phys', 'shop_png')),
}

# Масштаб кадра. Мера в миллиметрах приблизительная и нужна только чтобы
# понимать порядок ошибки: реальный масштаб разный по камерам (~0.08 / 0.09 /
# 0.12 мм на пиксель, PLAN B9) и зависит от расстояния до участка.
MM_PER_PX = {'back': 0.09, 'left': 0.082, 'top': 0.12}


def img_path(variant, view):
    if variant in EXTRA:
        return os.path.join(EXTRA[variant], f'{view}.png')
    return os.path.join(ARCHIVE, variant, f'{view}.png')


def mark_name(stem):
    """'shop_05.08_left' -> ('shop_05.08', 'left'). Имя варианта с '_' внутри."""
    variant, view = stem.rsplit('_', 1)
    return variant, view
