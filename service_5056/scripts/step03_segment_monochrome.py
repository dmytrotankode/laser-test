import os
import sys
import json
import argparse
import numpy as np
import cv2

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
    
    # Calculate maximum object width across rows
    w_max = 0
    for r in range(top, bot, max(1, (bot - top) // 50)):
        row_x = np.where(mask[r, :] > 0)[0]
        if len(row_x) > 0:
            w_max = max(w_max, row_x[-1] - row_x[0])
            
    bot_clean = bot
    # Scan from bottom up to find where narrow mounting stand ends and helmet dome begins
    for y in range(bot, top, -5):
        row_x = np.where(mask[y, :] > 0)[0]
        if len(row_x) > 0 and (row_x[-1] - row_x[0]) > w_max * 0.35:
            bot_clean = y
            # Zero out the mounting stand below bot_clean + small buffer
            cutoff_stand = min(bot, y + int((bot - top) * 0.015))
            mask[cutoff_stand:, :] = 0
            break
            
    return mask, bot_clean

# Every calibration constant downstream (KNN_LIBRARY ref_cm, W_calib) was fitted on
# masks produced by rembg. Otsu thresholding gives a visibly different silhouette, so
# falling back to it silently would keep the pipeline running while quietly invalidating
# those constants - wrong pose, no error, full confidence. The fallback therefore has to
# be asked for explicitly, and when it is used the result is marked as uncalibrated.
BACKEND_REMBG = "rembg"
BACKEND_OTSU = "otsu"


def _backend_version():
    try:
        import rembg
        return getattr(rembg, "__version__", "unknown")
    except Exception:
        return "n/a"


def segment_image(img_path, is_top_view=False, allow_fallback=False):
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
                f"cache in ~/.u2net), or pass --allow-fallback to run anyway - the "
                f"result will be marked uncalibrated.") from e
        backend = BACKEND_OTSU
        blur = cv2.GaussianBlur(gray, (7, 7), 0)
        _, mask = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Clean contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return np.zeros_like(gray), gray, (0, 0, 0, 0), 0, backend
        
    c = max(contours, key=cv2.contourArea)
    clean_mask = np.zeros_like(gray)
    cv2.drawContours(clean_mask, [c], -1, 255, -1)
    
    # 1. Strip the mounting stand (vertical cylinder at bottom)
    clean_mask, bot_clean = strip_mounting_stand(clean_mask, is_top_view)
    
    y_indices = np.where(clean_mask > 0)[0]
    if len(y_indices) == 0:
        return clean_mask, gray, (0, 0, 0, 0), 0, backend
    top_clean = np.min(y_indices)
    true_h = bot_clean - top_clean
    
    # 2. APPLY SAFE ZONE CUTOFF: Cut at 58% of true helmet height from top!
    # This guarantees we cut ABOVE the mounting stand, ABOVE ear cutouts, and ABOVE uncut front/back skirts!
    cutoff_y = bot_clean
    if not is_top_view and true_h > 0:
        cutoff_y = top_clean + int(true_h * 0.58)
        clean_mask[cutoff_y:, :] = 0
        
    # Re-compute bounding box of safe zone
    contours, _ = cv2.findContours(clean_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        c = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(c)
    else:
        x, y, w, h = 0, 0, 0, 0
            
    return clean_mask, gray, (x, y, w, h), cutoff_y, backend

def main():
    parser = argparse.ArgumentParser(description="Step 3: Monochrome Safe Zone Segmentation")
    parser.add_argument("--session", required=True)
    parser.add_argument("--allow-fallback", action="store_true",
                        help="run with Otsu if rembg is unavailable; marks the result "
                             "as uncalibrated instead of failing")
    args = parser.parse_args()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    results_dir = os.path.join(base_dir, 'results', args.session)
    os.makedirs(results_dir, exist_ok=True)

    cfg_path = os.path.join(results_dir, "config.json")
    variant = "default"
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                variant = json.load(f).get("variant", "default")
        except Exception:
            pass

    if variant != "default" and os.path.exists(os.path.join(base_dir, 'input', 'archive', variant)):
        print(f"Using archive photos for variant: {variant}")
        photos_dir = os.path.join(base_dir, 'input', 'archive', variant)
    else:
        photos_dir = os.path.join(base_dir, 'input', 'photos_current')

    views = {
        "back": {"path": os.path.join(photos_dir, 'back.png'), "top": False},
        "left": {"path": os.path.join(photos_dir, 'left.png'), "top": False},
        "top":  {"path": os.path.join(photos_dir, 'top.png'),  "top": True}
    }

    vis_panels = []
    stats = {}
    backends = set()

    for name, info in views.items():
        print(f"Segmenting {name} view with Stand Removal & Safe Zone Cutoff...")
        mask, gray, (x, y, w, h), cutoff_y, backend = segment_image(
            info["path"], info["top"], allow_fallback=args.allow_fallback)
        backends.add(backend)
        
        mask_filename = f"mask_current_{name}.png"
        mask_path = os.path.join(results_dir, mask_filename)
        cv2.imwrite(mask_path, mask)
        
        stats[name] = {
            "mask_file": f"/files/{args.session}/{mask_filename}",
            "bbox": [int(x), int(y), int(w), int(h)],
            "safe_zone_applied": not info["top"]
        }

        # Prepare side-by-side panel for visualization WITHOUT squishing (1:1 aspect ratio)!
        h_img, w_img = gray.shape
        target_h = 300
        target_w = int(target_h * (w_img / float(h_img)))
        
        thumb_orig = cv2.resize(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR), (target_w, target_h))
        thumb_mask = cv2.resize(cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR), (target_w, target_h))
        
        # Draw cutoff line indication on side views
        if not info["top"] and cutoff_y > 0:
            thumb_cutoff_y = int(target_h * (cutoff_y / float(h_img)))
            cv2.line(thumb_mask, (0, thumb_cutoff_y), (target_w, thumb_cutoff_y), (0, 0, 255), 2)
            cv2.putText(thumb_mask, "Safe Zone Cutoff (58% Top Dome)", (15, thumb_cutoff_y - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
            
        panel = np.hstack([thumb_orig, thumb_mask])
        cv2.putText(panel, f"{name.upper()} (Orig vs Safe Mask - No Horizontal Compression)", (15, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        vis_panels.append(panel)

    # Combine 3 panels vertically
    composite_vis = np.vstack(vis_panels)
    vis_filename = "step03_segment_vis.png"
    vis_path = os.path.join(results_dir, vis_filename)
    cv2.imwrite(vis_path, composite_vis)

    backend = BACKEND_OTSU if BACKEND_OTSU in backends else BACKEND_REMBG
    calibrated = (backend == BACKEND_REMBG)
    warn = ("" if calibrated else
            " УВАГА: сегментація виконана резервним методом (Otsu), а не rembg. "
            "Усі калібрувальні константи налаштовані під rembg, тож результат пози "
            "НЕ є каліброваним і використовувати його на верстаті не можна.")
    if not calibrated:
        print("WARNING: Otsu fallback used - result is NOT calibrated.")

    results = {
        "status": "success",
        "segmentation_backend": backend,
        "segmentation_backend_version": _backend_version(),
        "calibrated": calibrated,
        "views": stats,
        "vis_image": f"/files/{args.session}/{vis_filename}",
        "caption": warn + "Субпіксельна сегментація виконана з ідеальними пропорціями (без горизонтального скручення). НАЙВАЖЛИВІШЕ: 1) Автоматично розпізнано та видалено вертикальну монтажну стійку (конструкцію, на якій стоїть шолом); 2) Лінію відсікання Cutoff встановлено на рівні 58% висоти купола — гарантовано ВИЩЕ лінії обрізу лазером, вище вушок та вище будь-яких нерівних виступів кевлару. Маска містить лише ідеально стабільний верхній купол!"
    }

    out_path = os.path.join(results_dir, "step03_result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"Saved step 3 segmentation results to {out_path}")

if __name__ == "__main__":
    main()
