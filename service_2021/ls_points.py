"""Чтение и запись точек .LS - свой маленький парсер, ни от кого не зависит.

Не переиспользует lsgeom (5056) или export_ls (3030) специально: те живут в
сервисах, которые будут меняться, а этот файл должен продолжать работать, даже
если там что-то переименуют или удалят (сегодня так и произошло с одним файлом
в 3030). Формат самих .LS - это формат контроллера робота, он не наш и меняться
не должен, поэтому опираться на него безопаснее, чем на чужой код поверх него.

Формат точки в файле:  P[12]{ ... X = 123.456  ... Y = ... Z = ... }
"""
import re

POINT_RE = re.compile(
    r'(P\[(\d+)\]\{.*?X\s*=\s*)([-\d.]+)(.*?Y\s*=\s*)([-\d.]+)(.*?Z\s*=\s*)([-\d.]+)',
    re.DOTALL | re.IGNORECASE)


def read_points(path):
    """-> [(id:int, x, y, z), ...] в порядке появления в файле."""
    text = open(path, encoding='utf-8', errors='ignore').read()
    out = []
    for m in POINT_RE.finditer(text):
        pid = int(m.group(2))
        x, y, z = float(m.group(3)), float(m.group(5)), float(m.group(7))
        out.append((pid, x, y, z))
    return out


def write_points(src_path, dst_path, xyz_by_id, new_prog_name=None):
    """Взять src_path как шаблон (текст, скорости, W/P/R не трогаются),
    подставить новые X/Y/Z только для точек из xyz_by_id, остальные - как есть.

    xyz_by_id: {id: (x, y, z)}
    """
    text = open(src_path, encoding='utf-8', errors='ignore').read()

    def replace(m):
        pid = int(m.group(2))
        if pid not in xyz_by_id:
            return m.group(0)
        x, y, z = xyz_by_id[pid]
        return f'{m.group(1)}{x:.3f}{m.group(4)}{y:.3f}{m.group(6)}{z:.3f}'

    text = POINT_RE.sub(replace, text)
    if new_prog_name:
        text = re.sub(r'(/PROG\s+)\S+', lambda m: m.group(1) + new_prog_name, text, count=1)
        text = re.sub(r'(FILE_NAME\s*=\s*)[^;]*', lambda m: m.group(1) + new_prog_name[:8],
                      text, count=1)
    with open(dst_path, 'w', encoding='utf-8') as f:
        f.write(text)
    return dst_path


if __name__ == '__main__':
    import sys
    for pid, x, y, z in read_points(sys.argv[1])[:5]:
        print(f'{pid:>4}  {x:>10.3f} {y:>10.3f} {z:>10.3f}')
