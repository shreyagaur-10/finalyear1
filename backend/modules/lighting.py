"""
Lighting Normalization Module
Auto white-balance correction (gray-world algorithm) and histogram
equalization in LAB color space for consistent brightness.
"""

import cv2
import numpy as np


def normalize_lighting(image: np.ndarray) -> np.ndarray:
    """
    Normalize lighting in a BGR image.

    Steps:
    1. Gray-world white-balance correction
    2. CLAHE histogram equalization on the L channel in LAB space

    Args:
        image: BGR image as numpy array

    Returns:
        Corrected BGR image as numpy array
    """
    corrected = _gray_world_white_balance(image)
    corrected = _lab_histogram_equalization(corrected)
    return corrected


def assess_lighting_quality(image: np.ndarray) -> dict:
    """
    Estimate whether an uploaded image is suitable for color-sensitive analysis.
    Returns a compact score plus actionable flags for the API/UI.
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    value = hsv[:, :, 2].astype(np.float32)
    lightness = lab[:, :, 0].astype(np.float32)

    mean_v = float(np.mean(value))
    std_l = float(np.std(lightness))
    shadow_ratio = float(np.mean(value < 45))
    highlight_ratio = float(np.mean(value > 245))

    score = 100
    flags = []

    if mean_v < 70:
        score -= 30
        flags.append("low_light")
    elif mean_v > 220:
        score -= 25
        flags.append("overexposed")

    if shadow_ratio > 0.18:
        score -= 20
        flags.append("heavy_shadows")

    if highlight_ratio > 0.08:
        score -= 20
        flags.append("blown_highlights")

    if std_l < 22:
        score -= 10
        flags.append("flat_lighting")

    score = max(0, min(100, int(score)))
    if score >= 80:
        label = "good"
        message = "Lighting looks reliable for shade analysis."
    elif score >= 55:
        label = "usable"
        message = "Lighting is usable, but results may shift slightly."
    else:
        label = "poor"
        message = "Lighting may affect shade accuracy. Try natural, even light."

    return {
        "score": score,
        "label": label,
        "flags": flags,
        "message": message,
    }


def assess_capture_quality(image: np.ndarray, face_bbox: dict = None) -> dict:
    """
    Score capture quality beyond lighting: blur, resolution, and face size.
    This lets the product warn users before turning weak input into false certainty.
    """
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    score = 100
    flags = []

    if min(h, w) < 360:
        score -= 25
        flags.append("low_resolution")

    if blur_score < 55:
        score -= 35
        flags.append("blurry")
    elif blur_score < 95:
        score -= 15
        flags.append("slightly_blurry")

    face_coverage = None
    if face_bbox:
        face_area = face_bbox.get("width", 0) * face_bbox.get("height", 0)
        face_coverage = face_area / max(h * w, 1)
        if face_coverage < 0.08:
            score -= 25
            flags.append("face_too_small")
        elif face_coverage > 0.72:
            score -= 10
            flags.append("face_too_close")

    score = max(0, min(100, int(score)))
    if score >= 80:
        label = "high"
    elif score >= 55:
        label = "medium"
    else:
        label = "low"

    return {
        "score": score,
        "label": label,
        "blur_variance": round(blur_score, 2),
        "face_coverage": round(face_coverage, 3) if face_coverage is not None else None,
        "flags": flags,
    }


def _gray_world_white_balance(image: np.ndarray) -> np.ndarray:
    """
    Apply gray-world algorithm: scale each channel so its mean
    equals the overall mean across all channels.
    """
    img = image.astype(np.float32)
    avg_b = np.mean(img[:, :, 0])
    avg_g = np.mean(img[:, :, 1])
    avg_r = np.mean(img[:, :, 2])
    overall_avg = (avg_b + avg_g + avg_r) / 3.0

    img[:, :, 0] *= overall_avg / (avg_b + 1e-6)
    img[:, :, 1] *= overall_avg / (avg_g + 1e-6)
    img[:, :, 2] *= overall_avg / (avg_r + 1e-6)

    return np.clip(img, 0, 255).astype(np.uint8)


def _lab_histogram_equalization(image: np.ndarray) -> np.ndarray:
    """
    Convert to LAB, apply CLAHE on the L channel for consistent
    brightness, then convert back to BGR.
    """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)

    lab = cv2.merge([l, a, b])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
