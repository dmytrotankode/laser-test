"""Write a generated cut line into a neighbor's .LS text - vendored from
service_3030/export_ls.py's POINT_RE + the text-substitution pattern shared by
export_ls.py and export_cad_ls_contour.py.

Only X/Y/Z per point are rewritten; everything else in the template (headers, speeds,
W/P/R, motion order) stays byte-for-byte, so the tool axes the robot uses are the
template's own and the nozzle-from-cut-line conversion is consistent by construction.
"""
import os
import re

from . import geometry

POINT_RE = re.compile(
    r'(P\[(\d+)\]\{.*?X\s*=\s*)([-\d.]+)(.*?Y\s*=\s*)([-\d.]+)(.*?Z\s*=\s*)([-\d.]+)',
    re.DOTALL | re.IGNORECASE)


def write_ls(template_path, out_dir, point_fn, session_name):
    """Substitute XYZ per point via `point_fn(point_id, orig_xyz) -> new_xyz or None`.

    `None` leaves that point's XYZ untouched (used for lead-in/retreat points that
    aren't part of the fitted contour). Renames /PROG and FILE_NAME to a fresh,
    Fanuc-safe, unique program name derived from `session_name`, and writes to
    `<out_dir>/<name>.LS` - the file name and the in-file /PROG name MUST match (the
    controller refuses to load a program otherwise), so both come from the same `name`
    computed once here, never from a separately-chosen output path.
    """
    text = open(template_path, encoding='utf-8', errors='ignore').read()
    name = geometry.program_name(session_name)

    def replace(m):
        i = int(m.group(2))
        orig = (float(m.group(3)), float(m.group(5)), float(m.group(7)))
        new = point_fn(i, orig)
        if new is None:
            return m.group(0)
        return (f'{m.group(1)}{new[0]:.3f}{m.group(4)}{new[1]:.3f}'
                f'{m.group(6)}{new[2]:.3f}')

    text = POINT_RE.sub(replace, text)
    text = re.sub(r'(/PROG\s+)\S+', lambda m: m.group(1) + name, text, count=1)
    text = re.sub(r'(FILE_NAME\s*=\s*)[^;]*', lambda m: m.group(1) + name[:8],
                  text, count=1)

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f'{name}.LS')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(text)
    return out_path
