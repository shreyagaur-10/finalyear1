"""
Virtual Try-On Module
Applies semi-transparent color overlays for lipstick, blush,
foundation, and concealer using geometric face region approximations.
"""

import cv2
import numpy as np


# Opacity per product type
_OPACITY = {
    "foundation": 0.3,
    "lipstick": 0.4,
    "blush": 0.25,
    "concealer": 0.3,
}


def apply_virtual_tryon(
    image: np.ndarray,
    face_bbox: dict,
    product_type: str,
    hex_color: str,
) -> np.ndarray:
    """
    Overlay a semi-transparent makeup color on the appropriate face region.

    Args:
        image: BGR image as numpy array
        face_bbox: dict with x, y, width, height
        product_type: one of "foundation", "lipstick", "blush", "concealer"
        hex_color: hex color string like "#C44040"

    Returns:
        Modified BGR image as numpy array
    """
    color_bgr = _hex_to_bgr(hex_color)
    alpha = _OPACITY.get(product_type, 0.3)

    fx = face_bbox["x"]
    fy = face_bbox["y"]
    fw = face_bbox["width"]
    fh = face_bbox["height"]

    output = image.copy()

    if product_type == "lipstick":
        output = _apply_to_lips(output, fx, fy, fw, fh, color_bgr, alpha)
    elif product_type == "blush":
        output = _apply_to_cheeks(output, fx, fy, fw, fh, color_bgr, alpha)
    elif product_type == "foundation":
        output = _apply_to_face(output, fx, fy, fw, fh, color_bgr, alpha)
    elif product_type == "concealer":
        output = _apply_to_undereye(output, fx, fy, fw, fh, color_bgr, alpha)

    return output


def _hex_to_bgr(hex_color: str) -> tuple:
    """Convert '#RRGGBB' to (B, G, R) tuple."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (b, g, r)


def _blend_region(image: np.ndarray, mask: np.ndarray, color_bgr: tuple, alpha: float) -> np.ndarray:
    """Alpha-blend a solid color onto the image within the given mask."""
    overlay = image.copy()
    overlay[mask > 0] = color_bgr
    blended = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
    result = image.copy()
    result[mask > 0] = blended[mask > 0]
    return result


def _make_ellipse_mask(shape: tuple, center: tuple, axes: tuple) -> np.ndarray:
    """Create a binary mask with a filled ellipse."""
    mask = np.zeros(shape[:2], dtype=np.uint8)
    cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
    mask = cv2.GaussianBlur(mask, (15, 15), 5)
    return mask


def _apply_to_lips(image, fx, fy, fw, fh, color_bgr, alpha):
    """Overlay color on the lip region (geometric approximation)."""
    cx = fx + fw // 2
    cy = fy + int(fh * 0.82)
    axes = (int(fw * 0.22), int(fh * 0.07))
    mask = _make_ellipse_mask(image.shape, (cx, cy), axes)
    return _blend_region(image, mask, color_bgr, alpha)


def _apply_to_cheeks(image, fx, fy, fw, fh, color_bgr, alpha):
    """Overlay color on both cheek regions."""
    axes = (int(fw * 0.13), int(fh * 0.10))
    # Left cheek
    left_center = (fx + int(fw * 0.22), fy + int(fh * 0.60))
    mask = _make_ellipse_mask(image.shape, left_center, axes)
    image = _blend_region(image, mask, color_bgr, alpha)
    # Right cheek
    right_center = (fx + int(fw * 0.78), fy + int(fh * 0.60))
    mask = _make_ellipse_mask(image.shape, right_center, axes)
    return _blend_region(image, mask, color_bgr, alpha)


def _apply_to_face(image, fx, fy, fw, fh, color_bgr, alpha):
    """Apply a subtle color shift to the entire face region (foundation)."""
    cx = fx + fw // 2
    cy = fy + fh // 2
    axes = (fw // 2, fh // 2)
    mask = _make_ellipse_mask(image.shape, (cx, cy), axes)
    return _blend_region(image, mask, color_bgr, alpha)


def _apply_to_undereye(image, fx, fy, fw, fh, color_bgr, alpha):
    """Overlay color on the under-eye areas (concealer)."""
    axes = (int(fw * 0.12), int(fh * 0.05))
    # Left under-eye
    left_center = (fx + int(fw * 0.32), fy + int(fh * 0.48))
    mask = _make_ellipse_mask(image.shape, left_center, axes)
    image = _blend_region(image, mask, color_bgr, alpha)
    # Right under-eye
    right_center = (fx + int(fw * 0.68), fy + int(fh * 0.48))
    mask = _make_ellipse_mask(image.shape, right_center, axes)
    return _blend_region(image, mask, color_bgr, alpha)
