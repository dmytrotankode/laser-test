"""Чтение и запись точек .LS - свой маленький парсер, ни от кого не зависит.

Не переиспользует lsgeom (5056) или export_ls (3030) специально: те живут в
сервисах, которые будут меняться, а этот файл должен продолжать работать, даже
если там что-то переименуют или удалят (сегодня так и произошло с одним файлом
в 3030). Формат самих .LS - это формат контроллера робота, он не наш и меняться
не должен, поэтому опираться на него безопаснее, чем на чужой код поверх него.

ВАЖНО: X/Y/Z в файле - это путь СОПЛА, не линия реза. Луч режет на NOMINAL_STANDOFF
(10 мм) дальше вдоль оси инструмента, которая знается по W/P/R и у каждой точки
своя (наклон 55-76° от вертикали, не константа). Без вычитания этого отступа
показывать/править "линию реза" было бы неверно - в первой версии 2021 так и
было, отступ давал видимое расхождение по ширине.

Матрица оси инструмента - через scipy (внешняя, стабильная библиотека, не
проектный код): rot = Rotation.from_euler('ZYX', [R, P, W], degrees=True),
ось = rot.apply([0,0,1]). Да, W и R именно так меняются местами - это
соглашение Fanuc, не опечатка (сверено с lsgeom.tool_axes в 5056, 24.08).
"""
import re
from scipy.spatial.transform import Rotation

NOMINAL_STANDOFF = 10.0


def fanuc_safe_name(raw, max_len=17):
    """Ім'я, яке контролер точно погодиться завантажити в /PROG.

    Спіймано наживо: /PROG CORR_NABIR-0828-001 (дефіси з наших-таки нових
    імен на кшталт nabir-0828-001) впала з ASBN-002/008/009/050 "Invalid
    name in /PROG section" при спробі завантажити на робота. write_points()
    раніше писала new_prog_name у файл без жодної перевірки - працювало
    лише випадково, поки імена варіантів (v21, v26) не містили нічого, крім
    літер і цифр. 17 символів - те саме емпіричне обмеження, що вже
    задокументоване в pipeline/geometry.py.program_name (найдовше ім'я в
    продакшені - TORXL_NEW_PROG2_5).
    """
    s = re.sub(r'[^A-Za-z0-9]+', '_', raw).upper().strip('_')
    return (s[:max_len] or 'PROG')

POINT_RE = re.compile(
    r'P\[(\d+)\]\{.*?'
    r'X\s*=\s*([-\d.]+).*?Y\s*=\s*([-\d.]+).*?Z\s*=\s*([-\d.]+).*?'
    r'W\s*=\s*([-\d.]+).*?P\s*=\s*([-\d.]+).*?R\s*=\s*([-\d.]+)',
    re.DOTALL | re.IGNORECASE)

# Для записи обратно: та же группа X/Y/Z, но W/P/R не трогаем - только меняем
# число внутри уже существующего блока.
WRITE_RE = re.compile(
    r'(P\[(\d+)\]\{.*?X\s*=\s*)([-\d.]+)(.*?Y\s*=\s*)([-\d.]+)(.*?Z\s*=\s*)([-\d.]+)',
    re.DOTALL | re.IGNORECASE)


def tool_axis(w, p, r):
    """Единичная ось инструмента (+Z, от детали), в координатах станка."""
    rot = Rotation.from_euler('ZYX', [r, p, w], degrees=True)
    return rot.apply([0.0, 0.0, 1.0])


def read_ring(path, standoff=NOMINAL_STANDOFF, outlier_factor=3.0):
    """Как read_points, но без подвода/отвода - тех одиночных точек, что стоят
    далеко от остального кольца (например 'парковка' в конце программы).

    Отличаем чисто геометрически, без знания структуры файла: у обычной точки
    кольца соседи в пределах пары мм, у отвода - на порядок дальше. Точки, у
    которых ближайший сосед дальше чем `outlier_factor` от медианного шага,
    считаются подводом/отводом и не идут в редактируемую линию (но остаются
    в шаблоне нетронутыми при сборке .LS - write_points их не трогает, если их
    id не попал в cut_by_id).
    """
    import numpy as np
    pts = read_points(path, standoff)
    if len(pts) < 4:
        return pts
    cuts = np.array([p[2] for p in pts])
    # ближайший сосед КАЖДОЙ точки среди остальных (не только по порядку в
    # файле - двух соседних id может не быть рядом физически)
    d = np.linalg.norm(cuts[:, None, :] - cuts[None, :, :], axis=2)
    np.fill_diagonal(d, np.inf)
    nearest = d.min(axis=1)
    step = np.median(nearest)
    keep = nearest < outlier_factor * step
    dropped = [pts[i][0] for i in range(len(pts)) if not keep[i]]
    if dropped:
        print(f'  read_ring: исключены как подвод/отвод, id {dropped}')
    return [p for p, k in zip(pts, keep) if k]


def read_points(path, standoff=NOMINAL_STANDOFF):
    """-> [(id, nozzle_xyz, cut_xyz, axis), ...] в порядке появления в файле.

    nozzle_xyz - как записано в файле (путь сопла).
    cut_xyz    - nozzle - standoff*axis (то, что реально режется - вот это и
                 показываем/правим в вьювере).
    axis       - ось инструмента в этой точке, нужна, чтобы потом перевести
                 поправленную cut_xyz обратно в nozzle_xyz для записи в файл.
    """
    text = open(path, encoding='utf-8', errors='ignore').read()
    out = []
    for m in POINT_RE.finditer(text):
        pid = int(m.group(1))
        x, y, z = float(m.group(2)), float(m.group(3)), float(m.group(4))
        w, p, r = float(m.group(5)), float(m.group(6)), float(m.group(7))
        axis = tool_axis(w, p, r)
        nozzle = (x, y, z)
        cut = tuple(n - standoff * a for n, a in zip(nozzle, axis))
        out.append((pid, nozzle, cut, tuple(axis)))
    return out


def write_points(src_path, dst_path, cut_xyz_by_id, axis_by_id, standoff=NOMINAL_STANDOFF,
                 new_prog_name=None):
    """Взять src_path как шаблон, подставить X/Y/Z (пересчитав cut -> сопло по
    оси инструмента ЭТОЙ ЖЕ точки из шаблона), W/P/R не трогать.

    cut_xyz_by_id: {id: (x, y, z)} - поправленная линия РЕЗА, не сопла.
    axis_by_id:    {id: (ax, ay, az)} - та же ось, что вернул read_points -
                   правка двигает точку вдоль реза, не меняет наклон инструмента.
    """
    text = open(src_path, encoding='utf-8', errors='ignore').read()

    def replace(m):
        pid = int(m.group(2))
        if pid not in cut_xyz_by_id:
            return m.group(0)
        cx, cy, cz = cut_xyz_by_id[pid]
        ax, ay, az = axis_by_id[pid]
        x, y, z = cx + standoff * ax, cy + standoff * ay, cz + standoff * az
        return f'{m.group(1)}{x:.3f}{m.group(4)}{y:.3f}{m.group(6)}{z:.3f}'

    text = WRITE_RE.sub(replace, text)
    if new_prog_name:
        text = re.sub(r'(/PROG\s+)\S+', lambda m: m.group(1) + new_prog_name, text, count=1)
        text = re.sub(r'(FILE_NAME\s*=\s*)[^;]*', lambda m: m.group(1) + new_prog_name[:8],
                      text, count=1)
    with open(dst_path, 'w', encoding='utf-8') as f:
        f.write(text)
    return dst_path


if __name__ == '__main__':
    import sys
    for pid, nozzle, cut, axis in read_points(sys.argv[1])[:5]:
        print(f'{pid:>4}  сопло {nozzle}  рез {tuple(round(c,2) for c in cut)}')
