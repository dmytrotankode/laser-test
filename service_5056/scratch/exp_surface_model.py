"""Пункт 22: обучение в координатах точки реза вместо поз сопла. ЭКСПЕРИМЕНТ.

Ничего в рабочем пайплайне не меняет — только меряет, стоит ли менять.

Замысел. Записанная поза сопла = точка реза на поверхности + отступ d вдоль оси
инструмента. Отступ гулял по сессиям на 3.5-6.4 мм (§4), и сейчас этот мусор сидит
прямо в метках: ICP между контурами сопла пытается объяснить жёстким движением то,
что жёстким движением не является. Переходим к поверхности: S = P - d*ось. Там все
16 съёмок — один и тот же физический контур, и метки становятся чистой позой.

Протокол ровно тот же, что в fit_model.py: leave-one-variant-out ВНУТРИ TRAIN,
оценивается ближайший сосед (так работает эксплуатация). Held-out не читается —
dataset.guard_training. Сравниваются в одном прогоне:

    A. как сейчас   — метки и экспорт в координатах сопла
    B. поверхность  — метки и экспорт через точку реза, ось при повороте ЗАМОРОЖЕНА
    C. поверхность  — то же, но ось поворачивается вместе с позой

B против C — это открытый вопрос: GT записан с замороженными углами (оператор их не
правит), поэтому B обязан лучше совпадать с GT, но C геометрически честнее держит
угол реза к реальной поверхности. Меряем оба, решаем по цифрам.

Отступ d на экспорте: 10 мм (номинал) и d самого варианта (изолирует ошибку позы от
бухгалтерии зазора — та же логика, что в колонке «зазор» у evaluate.py).
"""
import os
import sys
import numpy as np

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import lsgeom     # noqa: E402
import dataset    # noqa: E402
import features   # noqa: E402
from scipy.spatial.transform import Rotation as _R   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

NOMINAL_D = 10.0
ANCHOR = "v1"


# ------------------------------------------------------------------ данные
def load(v):
    """Контур сопла (без врезки) и единичные оси инструмента в тех же точках."""
    prog = lsgeom.load(os.path.join(BASE, 'input', 'archive', v, 'ground_truth.ls'))
    _, ids, _ = prog.split_path()
    ids = ids[1:]                                    # как lsgeom.cut_ring
    P = np.array([prog.points[i][:3] for i in ids])
    wpr = np.array([prog.points[i][3:] for i in ids])
    A = np.array([lsgeom.rot_from_ypr(w[2], w[1], w[0]).apply([0, 0, 1]) for w in wpr])
    return P, A


# ------------------------------------------------------------------ геометрия
def kabsch(A, B):
    ca, cb = A.mean(0), B.mean(0)
    H = (A - ca).T @ (B - cb)
    U, _, Vt = np.linalg.svd(H)
    D = np.diag([1.0, 1.0, np.sign(np.linalg.det(Vt.T @ U.T))])
    Rm = Vt.T @ D @ U.T
    return Rm, cb - Rm @ ca


def icp(A, B, iters=40, n=900):
    """Жёсткое преобразование A -> B без соответствий (как в fit_model.icp)."""
    Bd = lsgeom.resample_closed(np.asarray(B, float), n)
    A = np.asarray(A, float)
    Rm, t, X = np.eye(3), np.zeros(3), A.copy()
    for _ in range(iters):
        j = np.linalg.norm(X[:, None, :] - Bd[None, :, :], axis=2).argmin(1)
        Rm, t = kabsch(A, Bd[j])
        X = A @ Rm.T + t
    return Rm, t


def fit_gap(P, A, ref_surface, grid=np.arange(-6.0, 26.01, 0.5)):
    """Отступ d, при котором поверхность варианта лучше всего ложится на опорную."""
    def resid(d):
        S = P - d * A
        Rm, t = icp(S, ref_surface)
        return float(lsgeom.curve_distance(S @ Rm.T + t, ref_surface).mean())
    e = np.array([resid(d) for d in grid])
    k = int(e.argmin())
    if 0 < k < len(grid) - 1:
        y0, y1, y2 = e[k - 1], e[k], e[k + 1]
        k_off = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) * (grid[1] - grid[0])
    else:
        k_off = 0.0
    return float(grid[k] + k_off), float(e[k])


def pose_between(Ta, Tb, pivot):
    (Ra, ta), (Rb, tb) = Ta, Tb
    Rm = Rb @ Ra.T
    t = tb - Rm @ ta
    yaw, pitch, roll = lsgeom.ypr_from_rot(Rm)
    shift = Rm @ pivot + t - pivot
    return np.array([shift[0], shift[1], shift[2], roll, pitch, yaw])


def apply_pose(pts, p, pivot):
    return lsgeom.rot_from_ypr(p[5], p[4], p[3]).apply(pts - pivot) + pivot + p[:3]


# ------------------------------------------------------------------ модель
def ridge(X, Y, lam):
    return np.linalg.solve(X.T @ X + lam * np.eye(X.shape[1]), X.T @ Y)


def fit_pairs(names, F, kind, lam, POSE):
    X, Y = [], []
    for a in names:
        for b in names:
            if a != b:
                X.append(features.vec(F[b], kind) - features.vec(F[a], kind))
                Y.append(POSE[(a, b)])
    X, Y = np.array(X), np.array(Y)
    sx = X.std(0)
    sx[sx < 1e-9] = 1.0
    return ridge(X / sx, Y, lam), sx


KIND, LAM = "prof", 100                      # как в model_pose.json


# ------------------------------------------------------------------ прогон
def main():
    names = dataset.guard_training(dataset.TRAIN)
    print(f"TRAIN: {len(names)} вариантов. Held-out не читается.\n")

    F = features.load(names)
    D = {v: load(v) for v in names}

    print("Подбор отступа d по каждому варианту (опора — v1 при 10 мм):")
    Pa, Aa = D[ANCHOR]
    ref_surface = Pa - NOMINAL_D * Aa
    gap, gap_res = {}, {}
    for v in names:
        P, A = D[v]
        if v == ANCHOR:
            gap[v], gap_res[v] = NOMINAL_D, 0.0
        else:
            gap[v], gap_res[v] = fit_gap(P, A, ref_surface)
        print(f"  {v:<5} d = {gap[v]:6.2f} мм   остаток формы {gap_res[v]:.2f} мм")

    SURF = {v: D[v][0] - gap[v] * D[v][1] for v in names}
    NOZZ = {v: D[v][0] for v in names}
    pivot = NOZZ[names[0]].mean(0)               # «центроид контура» — выбор из fit_model

    print("\nICP к опорному варианту (11 подгонок покрывают все 110 пар):")
    T_surf = {v: icp(SURF[ANCHOR], SURF[v]) for v in names}
    T_nozz = {v: icp(NOZZ[ANCHOR], NOZZ[v]) for v in names}
    POSE_S = {(a, b): pose_between(T_surf[a], T_surf[b], pivot)
              for a in names for b in names if a != b}
    POSE_N = {(a, b): pose_between(T_nozz[a], T_nozz[b], pivot)
              for a in names for b in names if a != b}
    print("  готово")


    def export(ref, v, p, mode, d_target):
        """Собрать предсказанный контур СОПЛА для варианта v из соседа ref."""
        if mode == "nozzle":
            return apply_pose(NOZZ[ref], p, pivot)
        S = apply_pose(SURF[ref], p, pivot)
        A = D[ref][1]
        if mode == "surface_rot":
            A = lsgeom.rot_from_ypr(p[5], p[4], p[3]).apply(A)
        return S + d_target * A


    def loo(mode, POSE, d_rule):
        errs = []
        for v in names:
            tr = [u for u in names if u != v]
            W, sx = fit_pairs(tr, F, KIND, LAM, POSE)
            d = {r: np.linalg.norm(features.vec(F[v], "f8") - features.vec(F[r], "f8"))
                 for r in tr}
            ref = min(d, key=d.get)
            p = (features.vec(F[v], KIND) - features.vec(F[ref], KIND)) / sx @ W
            dt = NOMINAL_D if d_rule == "nominal" else gap[v]
            pred = export(ref, v, p, mode, dt)
            errs.append(float(lsgeom.curve_distance(pred, NOZZ[v]).mean()))
        return np.mean(errs), np.max(errs), errs


    print("\n" + "=" * 78)
    print("LOO внутри TRAIN, ошибка до записанного контура сопла (мм)")
    print("=" * 78)
    print(f"{'вариант модели':<44}{'среднее':>10}{'худший':>10}")
    rows = [
        ("A. как сейчас (координаты сопла)", "nozzle", POSE_N, "nominal"),
        ("B. поверхность, ось заморожена, d=10", "surface_frozen", POSE_S, "nominal"),
        ("C. поверхность, ось повёрнута,  d=10", "surface_rot", POSE_S, "nominal"),
        ("B'. поверхность, ось заморожена, d варианта", "surface_frozen", POSE_S, "own"),
        ("C'. поверхность, ось повёрнута,  d варианта", "surface_rot", POSE_S, "own"),
    ]
    out = {}
    for label, mode, POSE, rule in rows:
        m, w, e = loo(mode, POSE, rule)
        out[label] = e
        print(f"{label:<44}{m:>10.2f}{w:>10.2f}")

    print("\nПо вариантам:")
    print(f"{'вар':<6}" + "".join(f"{lab.split('.')[0]:>9}" for lab, *_ in rows))
    for i, v in enumerate(names):
        print(f"{v:<6}" + "".join(f"{out[lab][i]:>9.2f}" for lab, *_ in rows))


if __name__ == '__main__':
    main()
