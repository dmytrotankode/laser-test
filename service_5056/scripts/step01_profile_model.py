"""Step 1: profile the CAD reference mesh.

Previously this file computed nothing: the dimensions 285.4 / 242.1 / 176.0 mm were
hardcoded constants, the .STL and .IGS were never opened, and the result was presented
as "bounding box, centre of mass and principal axes of the factory model". It now
actually reads the mesh.

Read the caveat in the result before using any of this: the mesh lives in its OWN
coordinate frame, centred near the origin, while the robot programme is in machine
coordinates ~1170 mm away. Nothing has ever registered one to the other, so these
numbers are descriptive - no downstream step consumes them.
"""
import os
import sys
import json
import struct
import argparse
import numpy as np
import cv2


def load_stl(path):
    """Vertices of a binary or ASCII STL, as (n, 3), plus the triangle count."""
    with open(path, 'rb') as f:
        data = f.read()
    if len(data) > 84:
        n_tri = struct.unpack('<I', data[80:84])[0]
        if len(data) == 84 + n_tri * 50:                    # binary
            raw = np.frombuffer(data[84:84 + n_tri * 50], dtype=np.uint8).reshape(n_tri, 50)
            v = np.empty((n_tri, 3, 3), dtype=np.float32)
            for k in range(3):
                chunk = raw[:, 12 + k * 12:24 + k * 12].tobytes()
                v[:, k, :] = np.frombuffer(chunk, dtype='<f4').reshape(n_tri, 3)
            return v.reshape(-1, 3).astype(float), n_tri
    txt = data.decode('utf-8', errors='ignore')
    verts = [[float(x) for x in ln.split()[1:4]]
             for ln in txt.splitlines() if ln.strip().startswith('vertex')]
    return np.array(verts, dtype=float), len(verts) // 3


def main():
    parser = argparse.ArgumentParser(description="Step 1: Profile 3D Model & Safe Zone")
    parser.add_argument("--session", required=True)
    args = parser.parse_args()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    results_dir = os.path.join(base_dir, 'results', args.session)
    os.makedirs(results_dir, exist_ok=True)

    stl_path = os.path.join(base_dir, 'input', 'model_3d', 'helmet_ref.stl')
    if not os.path.exists(stl_path):
        print(f"Error: missing {stl_path}")
        sys.exit(1)

    verts, n_tri = load_stl(stl_path)
    if len(verts) == 0:
        print(f"Error: no vertices parsed from {stl_path}")
        sys.exit(1)

    lo, hi = verts.min(axis=0), verts.max(axis=0)
    size = hi - lo
    centroid = verts.mean(axis=0)
    # principal axes of the vertex cloud (not mass-weighted - the mesh is a shell)
    cov = np.cov((verts - centroid).T)
    eigval, eigvec = np.linalg.eigh(cov)
    order = np.argsort(eigval)[::-1]
    eigval, eigvec = eigval[order], eigvec[:, order]

    length_mm, width_mm, height_mm = float(size[0]), float(size[1]), float(size[2])
    asymmetry_ratio = length_mm / width_mm if width_mm else 0.0
    safe_zone_cutoff_z = float(lo[2] + size[2] * 0.42)      # keep the top 58%, as step 3 does

    print(f"Parsed {n_tri} triangles / {len(verts)} vertices from helmet_ref.stl")
    print(f"  bounding box : {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm")
    print(f"  centroid     : ({centroid[0]:.2f}, {centroid[1]:.2f}, {centroid[2]:.2f})")

    vis_img = np.full((500, 800, 3), 40, dtype=np.uint8)
    cv2.putText(vis_img, "CAD reference mesh (helmet_ref.stl)", (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    rng = np.random.default_rng(0)
    idx = rng.choice(len(verts), size=min(4000, len(verts)), replace=False)
    sample = verts[idx]
    scale = 150.0 / max(size.max(), 1.0)

    def draw(ax0, ax1, ox, oy, colour, title, tx, ty):
        cv2.putText(vis_img, title, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
        for p in sample:
            x = int(ox + (p[ax0] - centroid[ax0]) * scale)
            y = int(oy - (p[ax1] - centroid[ax1]) * scale)
            if 0 <= x < 800 and 0 <= y < 500:
                vis_img[y, x] = colour

    draw(0, 1, 200, 260, (0, 200, 255), "Top (XY)", 155, 85)
    draw(0, 2, 600, 290, (0, 255, 120), "Side (XZ)", 550, 85)
    cv2.putText(vis_img, f"{size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm, {n_tri} triangles",
                (30, 455), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)
    cv2.putText(vis_img, "NOT registered to machine coordinates - descriptive only",
                (30, 480), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (120, 160, 255), 1)

    vis_filename = "step01_asymmetry.png"
    cv2.imwrite(os.path.join(results_dir, vis_filename), vis_img)

    results = {
        "status": "success",
        "model_file": "helmet_ref.stl",
        "triangles": int(n_tri),
        "vertices": int(len(verts)),
        "length_mm": round(length_mm, 2),
        "width_mm": round(width_mm, 2),
        "height_mm": round(height_mm, 2),
        "bbox_min": [round(float(x), 2) for x in lo],
        "bbox_max": [round(float(x), 2) for x in hi],
        "centroid": [round(float(x), 2) for x in centroid],
        "principal_axes": [[round(float(x), 4) for x in eigvec[:, k]] for k in range(3)],
        "principal_extents_mm": [round(float(np.sqrt(v)), 2) for v in eigval],
        "asymmetry_ratio": round(asymmetry_ratio, 4),
        "safe_zone_cutoff_z": round(safe_zone_cutoff_z, 2),
        "registered_to_machine_frame": False,
        "caveat": ("Меш у власній системі координат (центр біля нуля), програма робота — "
                   "у координатах верстата (~1170 мм). Прив'язки між ними не існує, тож "
                   "ці числа описові: жоден наступний крок їх не використовує."),
        "vis_image": f"/files/{args.session}/{vis_filename}",
        "caption": (f"Прочитано еталонний меш helmet_ref.stl: {n_tri} трикутників, "
                    f"габарити {length_mm:.1f} × {width_mm:.1f} × {height_mm:.1f} мм, "
                    f"центроїд ({centroid[0]:.1f}, {centroid[1]:.1f}, {centroid[2]:.1f}), "
                    f"співвідношення довжина/ширина {asymmetry_ratio:.3f}. "
                    f"УВАГА: меш НЕ прив'язаний до системи координат верстата — ці числа "
                    f"описові й у розрахунку пози участі не беруть.")
    }

    out_path = os.path.join(results_dir, "step01_result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"Saved step 1 profiling results to {out_path}")


if __name__ == "__main__":
    main()
