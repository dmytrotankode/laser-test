"""Синтетичний наскрізний тест Методу 3 на геометрії камер.
Правда = кільце різу з еталону; розмітка = його проекція + шум оператора;
старт - зі збитої пози; міряємо, наскільки підігнане кільце відходить від правди.

Член невязки - той самий, що в methods/method3/run.py, з двома відмінностями:
  * видима дуга передискретизується до 120 точок (у продакшн-коді довжина
    near_arc плаває, і least_squares падає "could not broadcast" - спіймано тут);
  * для top береться все кільце (згори видно його цілим; near_arc вибирав
    щоразу інший шматок і підгонка розвалювалась).
Не враховує: відмінність форми еталона від реального шолома і різницю
"лінія згину vs лінія реза" (~2.3 мм) - тобто це НИЖНЯ межа похибки.

    python synth_method3.py [кількість спроб]
"""
import sys, os, numpy as np, cv2
from scipy.optimize import least_squares
S21 = r"C:\Art\Ai projects\Laser2\service_2021"; sys.path.insert(0, S21)
from pipeline import camera_model as CM, contour_fit
import ls_points
rng = np.random.default_rng(0)

def setup(ls, camdir):
    ring = np.array([p[2] for p in ls_points.read_ring(ls)])
    cams = contour_fit.marker_cams(camdir)
    return ring, cams

def make_marks(ring, cams, views, sig_px, corr=15, bias_mm=0.0):
    marks = {}
    for w in views:
        pc, f = cams[w]
        uv, z = CM.project(ring, pc[:3], pc[3:6], f)
        vis = contour_fit.resample(np.r_[uv, uv[:1]] if w == 'top' else CM.near_arc(uv, z), 200)
        mm2px = f / np.median(z)
        # шум оператора: гладкий (коррельований вздовж лінії), по нормалі до лінії
        n = len(vis)
        e = np.convolve(rng.normal(size=n + 4 * corr), np.ones(corr) / np.sqrt(corr), 'same')[2 * corr:2 * corr + n]
        tng = np.gradient(vis, axis=0); nrm = np.c_[-tng[:, 1], tng[:, 0]]
        nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
        off = sig_px * e + bias_mm * mm2px * rng.choice([-1, 1])
        marks[w] = vis + nrm * off[:, None]
    return marks

def fit(ref, marks, cams, x0):
    center = ref.mean(0)
    def resid(p7):
        R = cv2.Rodrigues(p7[:3])[0]; s = np.exp(p7[6])
        P = (ref - center) @ R.T * s + center + p7[3:6]
        out = []
        for w, m in marks.items():
            pc, f = cams[w]; uv, z = CM.project(P, pc[:3], pc[3:6], f)
            vis = contour_fit.resample(np.r_[uv, uv[:1]] if w == 'top' else CM.near_arc(uv, z), 120); mu = contour_fit.resample(m)
            d = np.r_[np.abs(CM.dist_to_polyline(mu, vis)), np.abs(CM.dist_to_polyline(vis, mu))]
            out.append(d * float(np.median(z)) / f)
        return np.concatenate(out)
    b = (np.r_[[-0.6] * 3, [-150.0] * 3, -0.35], np.r_[[0.6] * 3, [150.0] * 3, 0.35])
    x = least_squares(resid, x0, method='trf', bounds=b, max_nfev=1500).x
    R = cv2.Rodrigues(x[:3])[0]; s = np.exp(x[6])
    return (ref - center) @ R.T * s + center + x[3:6]

def trial(ring, cams, views, sig_px, bias_mm=0.0, scale=True):
    # еталон = правда у збитій позі (поворот ~3°, зсув ~15 мм, масштаб ~1%)
    c = ring.mean(0)
    Rp = cv2.Rodrigues(np.radians(rng.normal(0, 3, 3)))[0]
    ref = (ring - c) @ Rp.T * np.exp(rng.normal(0, 0.01)) + c + rng.normal(0, 15, 3)
    marks = make_marks(ring, cams, views, sig_px, bias_mm=bias_mm)
    P = fit(ref, marks, cams, np.zeros(7))
    d = np.linalg.norm(P - ring, axis=1)
    return d.mean(), d.max()

if __name__ == '__main__':
    L = r"C:\Art\Ai projects\Laser2"
    rigs = {
        'НОВА (30.09, TOR_XL_1010_1)': setup(L + r"\laserdot_3\TOR_XL_1010_1.LS", S21 + r"\calib\cameras\marker_2026-09-30"),
        'СТАРА (08.21, TOR_XL_1009)': setup(S21 + r"\methods\method3\TOR_XL_1009.LS", S21 + r"\calib\cameras\marker_2026-08-21"),
    }
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    for name, (ring, cams) in rigs.items():
        print('====', name)
        for views in (('back', 'left'), ('back', 'left', 'top')):
            for sig, bias in ((0, 0), (3, 0), (6, 0), (3, 1.0)):
                r = np.array([trial(ring, cams, views, sig, bias) for _ in range(N)])
                print(f'  {"+".join(views):15s} шум {sig}px зсув {bias}мм:  середня {np.median(r[:,0]):.2f} мм,'
                      f' макс по кільцю: медіана {np.median(r[:,1]):.2f}, гірший {r[:,1].max():.2f}')
