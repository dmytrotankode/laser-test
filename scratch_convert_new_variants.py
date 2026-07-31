import os
import shutil
import numpy as np
import cv2

W, H = 4096, 3000

STAGING = "_staging"
ROOT_ARCHIVE = "archive"
SERVICE_ARCHIVE = "service_5056/input/archive"

# old rar-internal name -> new global name (chronological, avoids collision with existing v1-v6)
RENAME_MAP = {
    "v1": "v7", "v2": "v8", "v3": "v9", "v4": "v10", "v5": "v11",
    "v6": "v12", "v7": "v13", "v8": "v14", "v9": "v15", "v10": "v16",
}
VIEW_ORDER = ["back", "left", "top"]  # frame1, frame2, frame3 by capture timestamp order


def raw_to_png(raw_path):
    data = np.fromfile(raw_path, dtype=np.uint8)
    assert data.size == W * H, f"Unexpected raw size {data.size} for {raw_path}"
    return data.reshape(H, W)


def make_thumb(img, target_w=512):
    h, w = img.shape
    target_h = int(target_w * h / w)
    return cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_AREA)


for old_name, new_name in RENAME_MAP.items():
    src_dir = os.path.join(STAGING, old_name)
    if not os.path.isdir(src_dir):
        print(f"SKIP missing {src_dir}")
        continue

    raw_files = sorted(f for f in os.listdir(src_dir) if f.lower().endswith(".raw"))
    ls_files = [f for f in os.listdir(src_dir) if f.lower().endswith(".ls")]
    assert len(raw_files) == 3, f"{src_dir}: expected 3 raw files, found {len(raw_files)}"
    assert len(ls_files) == 1, f"{src_dir}: expected 1 .ls file, found {len(ls_files)}"

    # --- root archive/vNN : raw dump + converted (full png + thumb), mirrors existing v1-v5 convention
    root_out = os.path.join(ROOT_ARCHIVE, new_name)
    conv_out = os.path.join(root_out, "converted")
    os.makedirs(conv_out, exist_ok=True)

    view_pngs = {}
    for i, raw_name in enumerate(raw_files, start=1):
        raw_path = os.path.join(src_dir, raw_name)
        shutil.copy2(raw_path, os.path.join(root_out, raw_name))

        img = raw_to_png(raw_path)
        full_png = os.path.join(conv_out, f"frame{i}_{os.path.splitext(raw_name)[0]}.png")
        cv2.imwrite(full_png, img)
        thumb = make_thumb(img)
        cv2.imwrite(os.path.join(conv_out, f"frame{i}_thumb.png"), thumb)

        view = VIEW_ORDER[i - 1]
        view_pngs[view] = img

    ls_src = os.path.join(src_dir, ls_files[0])
    shutil.copy2(ls_src, os.path.join(root_out, ls_files[0]))
    ls_src_lower = os.path.join(root_out, ls_files[0].lower())
    if ls_src_lower != os.path.join(root_out, ls_files[0]):
        shutil.copy2(ls_src, ls_src_lower)

    # --- service_5056/input/archive/vNN : pipeline-ready back/left/top.png + ground_truth.ls
    svc_out = os.path.join(SERVICE_ARCHIVE, new_name)
    os.makedirs(svc_out, exist_ok=True)
    for view, img in view_pngs.items():
        cv2.imwrite(os.path.join(svc_out, f"{view}.png"), img)
    shutil.copy2(ls_src, os.path.join(svc_out, "ground_truth.ls"))

    print(f"{old_name} -> {new_name}: OK ({raw_files[0]} -> back, {raw_files[1]} -> left, {raw_files[2]} -> top)")

print("Done.")
