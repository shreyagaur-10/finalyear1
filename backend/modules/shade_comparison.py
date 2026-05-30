"""
Shade Comparison Engine
Calculates Delta-E color differences between skin tone and product shades,
and finds color-close product dupes.
"""

import re
import math
import numpy as np
import cv2


HEX_PATTERN = re.compile(r"^#?[0-9a-fA-F]{6}$")


def validate_hex_color(hex_color: str) -> str:
    """Validate and normalize a 6-digit hex color."""
    if not isinstance(hex_color, str) or not HEX_PATTERN.match(hex_color.strip()):
        raise ValueError("Expected a 6-digit hex color like #C8A07A.")
    value = hex_color.strip()
    return value if value.startswith("#") else f"#{value}"


def _hex_to_lab(hex_color: str) -> tuple:
    """Convert a hex color string to CIE-LAB values."""
    hex_color = validate_hex_color(hex_color).lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    pixel = np.array([[[b, g, r]]], dtype=np.uint8)
    lab = cv2.cvtColor(pixel, cv2.COLOR_BGR2LAB)
    L, a, b_val = lab[0][0].astype(float)
    # OpenCV LAB range: L: 0-255, a: 0-255, b: 0-255 (128 is zero)
    # Convert to standard LAB: L: 0-100, a: -128-127, b: -128-127
    L = L * 100.0 / 255.0
    a = a - 128.0
    b_val = b_val - 128.0
    return (L, a, b_val)


def delta_e_cie76(hex_a: str, hex_b: str) -> float:
    """Return CIE76 Delta-E distance between two hex colors."""
    lab_a = _hex_to_lab(hex_a)
    lab_b = _hex_to_lab(hex_b)
    return math.sqrt(
        (lab_a[0] - lab_b[0]) ** 2 +
        (lab_a[1] - lab_b[1]) ** 2 +
        (lab_a[2] - lab_b[2]) ** 2
    )


def delta_e_ciede2000(hex_a: str, hex_b: str) -> float:
    """
    Return CIEDE2000 color distance between two hex colors.
    CIEDE2000 tracks human-visible shade differences better than CIE76.
    """
    L1, a1, b1 = _hex_to_lab(hex_a)
    L2, a2, b2 = _hex_to_lab(hex_b)

    avg_lp = (L1 + L2) / 2.0
    c1 = math.sqrt(a1 * a1 + b1 * b1)
    c2 = math.sqrt(a2 * a2 + b2 * b2)
    avg_c = (c1 + c2) / 2.0

    g = 0.5 * (1 - math.sqrt((avg_c ** 7) / ((avg_c ** 7) + (25 ** 7))))
    a1p = (1 + g) * a1
    a2p = (1 + g) * a2
    c1p = math.sqrt(a1p * a1p + b1 * b1)
    c2p = math.sqrt(a2p * a2p + b2 * b2)
    avg_cp = (c1p + c2p) / 2.0

    def hp(a_prime, b_value):
        if a_prime == 0 and b_value == 0:
            return 0.0
        angle = math.degrees(math.atan2(b_value, a_prime))
        return angle + 360 if angle < 0 else angle

    h1p = hp(a1p, b1)
    h2p = hp(a2p, b2)

    dlp = L2 - L1
    dcp = c2p - c1p

    if c1p * c2p == 0:
        dhp = 0.0
    elif abs(h2p - h1p) <= 180:
        dhp = h2p - h1p
    elif h2p <= h1p:
        dhp = h2p - h1p + 360
    else:
        dhp = h2p - h1p - 360

    dhp_term = 2 * math.sqrt(c1p * c2p) * math.sin(math.radians(dhp / 2.0))

    if c1p * c2p == 0:
        avg_hp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        avg_hp = (h1p + h2p) / 2.0
    elif h1p + h2p < 360:
        avg_hp = (h1p + h2p + 360) / 2.0
    else:
        avg_hp = (h1p + h2p - 360) / 2.0

    t = (
        1
        - 0.17 * math.cos(math.radians(avg_hp - 30))
        + 0.24 * math.cos(math.radians(2 * avg_hp))
        + 0.32 * math.cos(math.radians(3 * avg_hp + 6))
        - 0.20 * math.cos(math.radians(4 * avg_hp - 63))
    )
    delta_ro = 30 * math.exp(-(((avg_hp - 275) / 25) ** 2))
    rc = 2 * math.sqrt((avg_cp ** 7) / ((avg_cp ** 7) + (25 ** 7)))
    sl = 1 + ((0.015 * ((avg_lp - 50) ** 2)) / math.sqrt(20 + ((avg_lp - 50) ** 2)))
    sc = 1 + 0.045 * avg_cp
    sh = 1 + 0.015 * avg_cp * t
    rt = -math.sin(math.radians(2 * delta_ro)) * rc

    return math.sqrt(
        (dlp / sl) ** 2
        + (dcp / sc) ** 2
        + (dhp_term / sh) ** 2
        + rt * (dcp / sc) * (dhp_term / sh)
    )


class ShadeComparator:
    def compare_shades(self, skin_hex: str, product_hexes: list) -> list:
        """
        Compare skin color against a list of product hex colors.

        Args:
            skin_hex: Skin hex color string (e.g. "#C8A07A")
            product_hexes: List of product hex color strings

        Returns:
            List of dicts with delta_e, match_quality, color_shift_description
        """
        skin_lab = _hex_to_lab(skin_hex)
        results = []

        for p_hex in product_hexes:
            p_lab = _hex_to_lab(p_hex)

            delta_e = delta_e_ciede2000(skin_hex, p_hex)

            match_quality = self._get_match_quality(delta_e)
            color_shift = self._get_color_shift(skin_lab, p_lab)

            results.append({
                "hex_color": p_hex,
                "delta_e": round(delta_e, 2),
                "delta_e_method": "CIEDE2000",
                "match_quality": match_quality,
                "color_shift_description": color_shift,
            })

        return results

    def find_dupes(self, target_hex: str, all_products: list, max_delta_e: float = 8.0) -> list:
        """
        Find products that are color-close (dupes) to a given hex color.

        Args:
            target_hex: Target hex color to match against
            all_products: Full product list (each must have "hex_color" key)
            max_delta_e: Maximum Delta-E threshold for a dupe

        Returns:
            List of product dicts with delta_e and match_quality added, sorted by delta_e
        """
        target_lab = _hex_to_lab(target_hex)
        dupes = []

        for product in all_products:
            p_hex = product.get("hex_color", "")
            if not p_hex:
                continue

            p_lab = _hex_to_lab(p_hex)
            delta_e = delta_e_ciede2000(target_hex, p_hex)

            if delta_e <= max_delta_e:
                dupes.append({
                    **product,
                    "delta_e": round(delta_e, 2),
                    "delta_e_method": "CIEDE2000",
                    "match_quality": self._get_match_quality(delta_e),
                    "color_shift_description": self._get_color_shift(target_lab, p_lab),
                })

        dupes.sort(key=lambda x: x["delta_e"])
        return dupes

    def _get_match_quality(self, delta_e: float) -> str:
        if delta_e < 3:
            return "exact"
        elif delta_e < 6:
            return "great"
        elif delta_e < 10:
            return "good"
        elif delta_e < 15:
            return "fair"
        else:
            return "poor"

    def _get_color_shift(self, lab1: tuple, lab2: tuple) -> str:
        """Describe the color shift from lab1 (skin) to lab2 (product)."""
        dL = lab2[0] - lab1[0]
        da = lab2[1] - lab1[1]
        db = lab2[2] - lab1[2]

        total = math.sqrt(dL ** 2 + da ** 2 + db ** 2)

        if total < 3:
            return "nearly identical"

        # Determine the dominant shift
        abs_dL = abs(dL)
        abs_db = abs(db)

        # b-channel: positive = yellow (warm), negative = blue (cool)
        if abs_db > abs_dL and abs_db > abs(da):
            if db > 0:
                return "slightly warmer"
            else:
                return "slightly cooler"
        elif abs_dL > abs(da):
            if dL > 0:
                return "lighter"
            else:
                return "darker"
        else:
            if da > 0:
                return "slightly warmer"
            else:
                return "slightly cooler"
