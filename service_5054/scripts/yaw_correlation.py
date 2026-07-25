"""
Direct yaw estimation via circular cross-correlation of the "top" camera's
polar contour profile (radius vs angle), instead of trying to extract yaw
from find_2d_transform's general-purpose 2D affine search (which
MEASUREMENT_ACCURACY.md found to be weak, noisy, and cross-axis-
contaminated for yaw specifically).

Rationale: the top-view silhouette is not circular - it has a real,
confirmed ~26% radius variation around its own centroid (see ROADMAP.md /
3D_POSE_FIT_STATUS.md "Направление 1"), most likely the helmet's genuine
front-to-back vs side-to-side shape. A yaw rotation rotates this
asymmetric profile; circular cross-correlation is the mathematically
direct tool for finding "how much was this periodic signal rotated by",
rather than hoping a general 6-parameter search stumbles onto the right
answer.

Compares REAL photo against REAL photo (current top mask vs etalon top
mask), not real-vs-rendered-CAD-model - avoids a potential shape mismatch
between the final CAD design and the actual raw/uncut shell being
photographed (the helmet is measured before trimming).
"""
import os
import numpy as np
import cv2

N_BINS = 360


def load_mask_alpha_or_gray(path):
    data = np.fromfile(path, dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(path)
    if img.ndim == 3 and img.shape[2] == 4:
        mask = img[:, :, 3]
    else:
        gray = img if img.ndim == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
    return mask


def extract_polar_profile(mask, n_bins=N_BINS, cutoff_frac=None):
    """Outer-contour radius per angle bin, around the mask's own centroid.
    Bins with no contour point are filled by linear interpolation (circular)
    so the profile is complete for correlation."""
    m = mask > 0
    if cutoff_frac is not None:
        rows = np.where(m.any(axis=1))[0]
        if len(rows) > 0:
            y0, y1 = rows[0], rows[-1]
            cutoff_y = int(y0 + (y1 - y0) * cutoff_frac)
            m = m.copy()
            m[cutoff_y:, :] = False

    m_u8 = (m * 255).astype(np.uint8)
    contours, _ = cv2.findContours(m_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return None
    pts = np.concatenate([c.reshape(-1, 2) for c in contours], axis=0).astype(np.float64)

    cx, cy = pts[:, 0].mean(), pts[:, 1].mean()
    dx = pts[:, 0] - cx
    dy = pts[:, 1] - cy
    radius = np.sqrt(dx * dx + dy * dy)
    angle = np.arctan2(dy, dx)

    bin_idx = ((angle + np.pi) / (2 * np.pi) * n_bins).astype(int) % n_bins
    profile = np.full(n_bins, np.nan)
    for b in range(n_bins):
        sel = bin_idx == b
        if np.any(sel):
            profile[b] = radius[sel].max()

    valid = ~np.isnan(profile)
    if valid.sum() < n_bins * 0.5:
        return None
    if not valid.all():
        idx = np.arange(n_bins)
        profile[~valid] = np.interp(idx[~valid], idx[valid], profile[valid], period=n_bins)
    return profile


def estimate_yaw_deg(target_profile, reference_profile):
    """Circular cross-correlation (FFT-based) between two radius-vs-angle
    profiles - returns the angular shift (degrees) that best aligns
    reference to target, i.e. the estimated yaw of target relative to
    reference. Positive = target rotated counter-clockwise in image space
    relative to reference (sign/convention to be verified empirically
    against known synthetic rotations before trusting it)."""
    n = len(target_profile)
    a = target_profile - target_profile.mean()
    b = reference_profile - reference_profile.mean()
    corr = np.real(np.fft.ifft(np.fft.fft(a) * np.conj(np.fft.fft(b))))
    best_shift = int(np.argmax(corr))
    if best_shift > n // 2:
        best_shift -= n
    yaw_deg = best_shift * (360.0 / n)
    peak_strength = corr[best_shift if best_shift >= 0 else best_shift + n] / (np.std(a) * np.std(b) * n)
    return yaw_deg, peak_strength


def estimate_yaw_from_files(target_path, reference_path, cutoff_frac=0.90):
    target_mask = load_mask_alpha_or_gray(target_path)
    reference_mask = load_mask_alpha_or_gray(reference_path)
    target_profile = extract_polar_profile(target_mask, cutoff_frac=cutoff_frac)
    reference_profile = extract_polar_profile(reference_mask, cutoff_frac=cutoff_frac)
    if target_profile is None or reference_profile is None:
        return None, None
    return estimate_yaw_deg(target_profile, reference_profile)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    args = parser.parse_args()
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    results_dir = os.path.join(base_dir, 'results', args.session)
    yaw_deg, strength = estimate_yaw_from_files(
        os.path.join(results_dir, 'current_solid_top.png'),
        os.path.join(results_dir, 'rgba_top.png'),
    )
    print(f"Estimated yaw (cross-correlation): {yaw_deg:.2f}deg  (peak strength={strength:.3f})")
