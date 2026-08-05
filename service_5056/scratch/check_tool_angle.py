"""Насколько угол сопла в нашем экспорте расходится с записью оператора.

Экспорт переписывает только X/Y/Z, а W/P/R берёт у соседа-шаблона как есть.
Значит угол наклона лазера мы НЕ корректируем. Вопрос: насколько он из-за этого
отличается от того, что стоял у оператора, и что это даёт в миллиметрах.
"""
import os
import sys
import numpy as np

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import lsgeom    # noqa: E402
import dataset   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def axis_at_matched(exp_pts, exp_ax, gt_pts, gt_ax):
    """Ось оператора в СОПОСТАВЛЕННОЙ точке кривой, а не по индексу списка.

    Нумерация точек между старой и новой партиями сдвинута на шаг контура, а сосед
    у held-out как раз из другой партии. Сравнение по индексу сопоставляло бы оси
    в разных физических местах и давало бы ложные ~8 градусов (см. PLAN.md, B5)."""
    A, B = gt_pts, np.roll(gt_pts, -1, axis=0)
    AB = B - A
    den = (AB * AB).sum(1)
    den[den == 0] = 1e-12
    AP = exp_pts[:, None, :] - A[None, :, :]
    t = np.clip((AP * AB[None, :, :]).sum(2) / den[None, :], 0, 1)
    close = A[None, :, :] + t[:, :, None] * AB[None, :, :]
    j = np.linalg.norm(exp_pts[:, None, :] - close, axis=2).argmin(1)
    k = np.arange(len(exp_pts))
    tt = t[k, j][:, None]
    z = gt_ax[j] * (1 - tt) + gt_ax[(j + 1) % len(gt_ax)] * tt
    return z / np.linalg.norm(z, axis=1, keepdims=True)


print("Угол между осью сопла в НАШЕМ экспорте и в записи оператора")
print("(оси сопоставлены по положению на кривой, не по индексу):\n")
print(f"{'вар':<6}{'сред°':>8}{'макс°':>8}{'=> мм при 10 мм отступа':>26}")
for v in dataset.ALL:
    gt = lsgeom.load(os.path.join(BASE, 'input', 'archive', v, 'ground_truth.ls'))
    exp = lsgeom.load(lsgeom.export_path(os.path.join(BASE, 'results', f'audit_{v}')))
    gP, gids = lsgeom.cut_ring(gt)
    eP, eids = lsgeom.cut_ring(exp)
    A = axis_at_matched(eP, None, gP, lsgeom.tool_axes(gt, gids))
    B = lsgeom.tool_axes(exp, eids)
    d = np.degrees(np.arccos(np.clip((A * B).sum(1), -1, 1)))
    mm = lsgeom.NOMINAL_STANDOFF * np.tan(np.radians(d))
    tag = "  <-- held-out" if v in dataset.HELDOUT else ""
    print(f"{v:<6}{d.mean():>8.2f}{d.max():>8.2f}{mm.mean():>16.2f} / {mm.max():.2f}{tag}")

print("\nПояснение: экспорт переписывает только X/Y/Z, углы W/P/R достаются от")
print("соседа-шаблона. Колонка «мм» — на сколько сдвинется точка попадания луча")
print("из-за одного лишь угла, при отступе 10 мм. Эта величина УЖЕ входит в нашу")
print("метрику, потому что линия реза строится по осям самого экспорта.")

# насколько вообще углы отличаются между вариантами внутри партии
print("\nДля сравнения — разброс углов между записями оператора внутри одной партии:")
for batch, name in ((["v1", "v2", "v3", "v4", "v5", "v6"], "старая v1-v6"),
                    ([f"v{i}" for i in range(7, 17)], "новая v7-v16")):
    ref = lsgeom.load(os.path.join(BASE, 'input', 'archive', batch[0], 'ground_truth.ls'))
    _, rids = lsgeom.cut_ring(ref)
    A = lsgeom.tool_axes(ref, rids)
    worst = 0.0
    for v in batch[1:]:
        p = lsgeom.load(os.path.join(BASE, 'input', 'archive', v, 'ground_truth.ls'))
        _, ids = lsgeom.cut_ring(p)
        n = min(len(ids), len(rids))
        B = lsgeom.tool_axes(p, ids[:n])
        worst = max(worst, float(np.degrees(np.arccos(
            np.clip((A[:n] * B).sum(1), -1, 1))).max()))
    print(f"  {name}: максимум {worst:.2f}°")
