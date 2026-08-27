"""Helmet silhouette segmentation - vendored from
service_5056/scripts/step03_segment_monochrome.py.

Isolated in its own file on purpose: rembg/onnxruntime is the single most fragile
external dependency in this pipeline (model download, backend availability), so "did
segmentation change" is always a one-file diff against this module.
"""
import os

import cv2
import numpy as np

BACKEND_REMBG = "rembg"
BACKEND_OTSU = "otsu"


def _backend_version():
    try:
        import rembg
        return getattr(rembg, "__version__", "unknown")
    except Exception:
        return "n/a"


def strip_mounting_stand(mask, is_top_view=False):
    if is_top_view:
        y_indices = np.where(mask > 0)[0]
        return mask, np.max(y_indices) if len(y_indices) > 0 else 0

    h, w = mask.shape
    y_indices = np.where(mask > 0)[0]
    if len(y_indices) == 0:
        return mask, 0

    bot = np.max(y_indices)
    top = np.min(y_indices)

    w_max = 0
    for r in range(top, bot, max(1, (bot - top) // 50)):
        row_x = np.where(mask[r, :] > 0)[0]
        if len(row_x) > 0:
            w_max = max(w_max, row_x[-1] - row_x[0])

    bot_clean = bot
    for y in range(bot, top, -5):
        row_x = np.where(mask[y, :] > 0)[0]
        if len(row_x) > 0 and (row_x[-1] - row_x[0]) > w_max * 0.35:
            bot_clean = y
            cutoff_stand = min(bot, y + int((bot - top) * 0.015))
            mask[cutoff_stand:, :] = 0
            break

    return mask, bot_clean


def segment_image(img_path, is_top_view=False, allow_fallback=False, depth_px=None,
                  abs_y=None):
    """Returns (clean_mask, gray, (x, y, w, h), cutoff_y, backend).

    rembg is required by default - every calibration constant downstream was fitted on
    rembg masks, and a silent Otsu fallback would keep the pipeline running while
    quietly invalidating them (wrong pose, no error, full confidence). Pass
    allow_fallback=True to run with Otsu anyway; the caller is responsible for treating
    that result as uncalibrated.
    """
    if not os.path.exists(img_path):
        raise FileNotFoundError(f"Missing {img_path}")

    img = cv2.imread(img_path)
    if img is None:
        raise RuntimeError(f"Cannot decode image: {img_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    backend = BACKEND_REMBG
    try:
        from rembg import remove
        out = remove(img)
        mask = out[:, :, 3]
    except Exception as e:
        if not allow_fallback:
            raise RuntimeError(
                f"rembg segmentation failed ({type(e).__name__}: {e}). All calibration "
                f"constants were fitted on rembg masks, so the Otsu fallback would "
                f"produce a confident but wrong pose. Fix the rembg install (model "
                f"cache in ~/.u2net), or pass allow_fallback=True to run anyway - the "
                f"result will be marked uncalibrated.") from e
        backend = BACKEND_OTSU
        blur = cv2.GaussianBlur(gray, (7, 7), 0)
        _, mask = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return np.zeros_like(gray), gray, (0, 0, 0, 0), 0, backend

    c = max(contours, key=cv2.contourArea)
    clean_mask = np.zeros_like(gray)
    cv2.drawContours(clean_mask, [c], -1, 255, -1)

    clean_mask, bot_clean = strip_mounting_stand(clean_mask, is_top_view)

    y_indices = np.where(clean_mask > 0)[0]
    if len(y_indices) == 0:
        return clean_mask, gray, (0, 0, 0, 0), 0, backend
    top_clean = np.min(y_indices)
    true_h = bot_clean - top_clean

    # Safe-zone cutoff anchored to the bottom of the silhouette (58% of dome height) -
    # every downstream constant (library features, k-NN scale) was fitted on masks made
    # with this rule; the depth_px/abs_y alternatives exist but are opt-in only.
    cutoff_y = bot_clean
    if not is_top_view and true_h > 0:
        if abs_y:
            cut = int(abs_y)
        elif depth_px:
            cut = top_clean + int(depth_px)
        else:
            cut = top_clean + int(true_h * 0.58)
        cutoff_y = int(min(cut, bot_clean))
        clean_mask[cutoff_y:, :] = 0

    contours, _ = cv2.findContours(clean_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        c = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(c)
    else:
        x, y, w, h = 0, 0, 0, 0

    return clean_mask, gray, (x, y, w, h), cutoff_y, backend
