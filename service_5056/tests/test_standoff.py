"""Проверки геометрии отступа (lsgeom.cut_surface / fit_standoff).

Смысл проверок — не «цифра стала меньше», а инварианты, которые обязаны выполняться,
если разделение «точка реза + отступ» сделано правильно.

Run:  python tests/test_standoff.py
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

FAILURES = []
ANCHOR = "v1"

# Замерены в scratch/exp_*.py до внесения в пайплайн. Тест фиксирует их, чтобы
# случайная правка сегментации/парсера/конвенции углов не уехала незаметно.
EXPECTED = {"v1": 10.00, "v2": 10.08, "v3": 10.11, "v4": 10.68, "v5": 10.70,
            "v6": 11.33, "v7": 10.17, "v8": 9.96, "v9": 10.08, "v10": 10.04,
            "v11": 10.04, "v12": 9.99, "v13": 6.49, "v14": 6.47, "v15": 3.73,
            "v16": 3.69}


def check(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if detail else ""))
    if not ok:
        FAILURES.append(f"{name}: {detail}")
    return ok


def prog(v):
    return lsgeom.load(os.path.join(BASE, 'input', 'archive', v, 'ground_truth.ls'))


PROGS = {v: prog(v) for v in dataset.ALL}
REF, _ = lsgeom.cut_surface(PROGS[ANCHOR], lsgeom.NOMINAL_STANDOFF)


# ---------------------------------------------------------------- S1
print("\nS1  сдвиг сопла вдоль оси не двигает точку реза")
# Это вся суть новой метрики: если бы двигал, отступ нельзя было бы игнорировать.
for v in ("v1", "v9", "v15"):
    S0, _ = lsgeom.cut_surface(PROGS[v], 0.0)
    for d in (5.0, 10.0, 25.0):
        Sd, _ = lsgeom.cut_surface(PROGS[v], d)
        # точка реза = пересечение луча с деталью; сам луч при сдвиге вдоль оси
        # остаётся той же прямой, поэтому S(d) обязана лежать на луче из S(0)
        A = lsgeom.tool_axes(PROGS[v], lsgeom.cut_ring(PROGS[v])[1])
        off = np.linalg.norm((S0 - Sd) - d * A, axis=1).max()
        check(f"S1 {v} d={d:g} точка реза на том же луче", off < 1e-9, f"{off:.2e} мм")


# ---------------------------------------------------------------- S2
print("\nS2  подобранный отступ воспроизводится")
worst = 0.0
for v in dataset.ALL:
    d, res = lsgeom.fit_standoff(PROGS[v], REF)
    worst = max(worst, abs(d - EXPECTED[v]))
    check(f"S2 {v} отступ {d:.2f} мм", abs(d - EXPECTED[v]) < 0.05,
          f"ожидалось {EXPECTED[v]:.2f}, остаток формы {res:.2f} мм")
print(f"  максимальное расхождение с эталонными значениями: {worst:.3f} мм")


# ---------------------------------------------------------------- S3
print("\nS3  после снятия отступа все 16 съёмок — один контур")
# Шлем один и тот же (подтверждено заказчиком), значит линии реза обязаны совпасть
# с точностью до жёсткого движения. Порог 2.0 мм — заметно выше наблюдаемого 0.2-1.9,
# но заметно ниже 3.4-6.0, которые были бы БЕЗ снятия отступа.
for v in dataset.ALL:
    d, _ = lsgeom.fit_standoff(PROGS[v], REF)
    S, _ = lsgeom.cut_surface(PROGS[v], d)
    Rm, t = lsgeom.icp(S, REF)
    e = float(lsgeom.curve_distance(S @ Rm.T + t, REF).mean())
    N, _ = lsgeom.cut_surface(PROGS[v], lsgeom.NOMINAL_STANDOFF)
    Rn, tn = lsgeom.icp(N, REF)
    en = float(lsgeom.curve_distance(N @ Rn.T + tn, REF).mean())
    check(f"S3 {v} совпадает после снятия отступа", e < 2.0,
          f"{e:.2f} мм (без снятия было бы {en:.2f})")


# ---------------------------------------------------------------- S4
print("\nS4  ICP без соответствий не зависит от нумерации точек")
# Старая партия и новая нумеруют контур по-разному; поиск по индексу сравнивал бы
# точки в ~10 мм друг от друга. Сдвиг вершин по кругу не должен менять результат.
S, _ = lsgeom.cut_surface(PROGS["v9"], 10.0)
R1, t1 = lsgeom.icp(S, REF)
R2, t2 = lsgeom.icp(np.roll(S, 37, axis=0), REF)
a = float(np.degrees(np.linalg.norm(
    lsgeom._R.from_matrix(R1 @ R2.T).as_rotvec())))
check("S4 поворот совпадает при сдвиге нумерации", a < 0.05, f"{a:.4f}°")
check("S4 сдвиг совпадает при сдвиге нумерации",
      float(np.linalg.norm(t1 - t2)) < 0.05, f"{np.linalg.norm(t1 - t2):.4f} мм")


print("\n" + "=" * 70)
if FAILURES:
    print(f"ПРОВАЛЕНО {len(FAILURES)}:")
    for f in FAILURES:
        print("  -", f)
    sys.exit(1)
print("все проверки пройдены")
