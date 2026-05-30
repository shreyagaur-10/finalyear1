"""
Skin Analysis Module
Extracts dominant skin color using K-Means clustering and classifies
the undertone as warm, cool, or neutral. Includes ITA angle classification,
skin health indicators, and color harmony recommendations.
"""

import math
import numpy as np
import cv2
from sklearn.cluster import KMeans
from modules.skin_tone_model import SkinToneClassifier
from modules.shade_comparison import delta_e_ciede2000


# Shade name mapping — covers the full range of Indian/South Asian skin tones
SHADE_RANGES = [
    {"name": "Porcelain Ivory", "range": (220, 255), "code": "IV01"},
    {"name": "Fair Ivory", "range": (200, 220), "code": "IV02"},
    {"name": "Light Beige", "range": (185, 200), "code": "LB01"},
    {"name": "Natural Beige", "range": (170, 185), "code": "NB01"},
    {"name": "Sand Beige", "range": (155, 170), "code": "SB01"},
    {"name": "Golden Beige", "range": (140, 155), "code": "GB01"},
    {"name": "Warm Honey", "range": (125, 140), "code": "WH01"},
    {"name": "Caramel", "range": (110, 125), "code": "CR01"},
    {"name": "Warm Almond", "range": (95, 110), "code": "WA01"},
    {"name": "Rich Mocha", "range": (80, 95), "code": "RM01"},
    {"name": "Deep Espresso", "range": (60, 80), "code": "DE01"},
    {"name": "Deep Mahogany", "range": (0, 60), "code": "DM01"},
]


class SkinAnalyzer:
    def __init__(self):
        self.tone_classifier = SkinToneClassifier()

    def analyze(self, skin_pixels: list, region_pixels: dict = None) -> dict:
        """
        Analyze skin pixels to determine skin tone and undertone.

        Args:
            skin_pixels: List of [B, G, R] pixel values from face regions
            region_pixels: Optional dict with left_cheek, right_cheek, forehead pixel lists

        Returns:
            dict with hex_color, shade_name, undertone, confidence,
            ita_angle, ita_category, skin_health_indicators, color_harmony
        """
        if not skin_pixels or len(skin_pixels) < 10:
            return {"error": "Not enough skin pixels to analyze. Please try a clearer photo."}

        pixels = np.array(skin_pixels, dtype=np.float32)

        # Step 1: Filter out non-skin pixels (too dark/bright or saturated)
        filtered = self._filter_skin_pixels(pixels)

        if len(filtered) < 10:
            return {"error": "Could not isolate skin area. Please try a photo with better lighting."}

        sample_quality = self._compute_sample_quality(pixels, filtered, region_pixels)

        # Step 2: Robust color estimation to reduce shadow/highlight bias
        dominant_color = self._find_representative_color(filtered)

        # dominant_color is in BGR format (from OpenCV)
        b, g, r = dominant_color

        # Step 3: Determine shade name
        # Use luminance as the primary selector
        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        shade_info = self._get_shade_name(luminance)

        # Step 4: Classify undertone
        undertone = self._classify_undertone(r, g, b)

        # Step 5: Convert to hex
        hex_color = "#{:02x}{:02x}{:02x}".format(int(r), int(g), int(b))

        # Step 6: ITA angle calculation
        ita_angle, ita_category = self._compute_ita(dominant_color)

        # Step 7: Skin health indicators
        skin_health = self._compute_skin_health(region_pixels)

        # Step 8: Color harmony recommendations
        color_harmony = self._compute_color_harmony(undertone["type"])

        # Step 9: ML-based skin tone classification
        ml_prediction = self.tone_classifier.predict_from_pixels(
            np.array(skin_pixels, dtype=np.float32)
        )

        # Use ML prediction to boost confidence when it agrees with rule-based
        if ml_prediction:
            tone_info = ml_prediction.get("tone_info", {})
            ita_cats = tone_info.get("ita_categories", [])
            if ita_category in ita_cats:
                undertone["confidence"] = min(0.97, undertone["confidence"] + 0.1)

        confidence = self._combine_confidence(
            undertone["confidence"],
            sample_quality,
            ml_prediction,
            ita_category,
        )

        result = {
            "hex_color": hex_color,
            "rgb": {"r": int(r), "g": int(g), "b": int(b)},
            "shade_name": shade_info["name"],
            "shade_code": shade_info["code"],
            "undertone": undertone["type"],
            "undertone_description": undertone["description"],
            "luminance": round(float(luminance), 1),
            "confidence": confidence,
            "ita_angle": ita_angle,
            "ita_category": ita_category,
            "sample_quality": sample_quality,
            "skin_health_indicators": skin_health,
            "color_harmony": color_harmony,
        }

        if ml_prediction:
            result["ml_skin_tone"] = {
                "predicted_tone": ml_prediction["predicted_tone"],
                "model_class": ml_prediction.get("model_class"),
                "confidence": ml_prediction["confidence"],
                "probabilities": ml_prediction.get("display_probabilities", ml_prediction["probabilities"]),
            }

        return result

    def _filter_skin_pixels(self, pixels: np.ndarray) -> np.ndarray:
        """
        Filter pixels to keep only likely skin-colored ones.
        Removes very dark shadows, bright highlights, and non-skin colors.
        """
        # Convert BGR to HSV for better skin detection
        # Reshape for OpenCV conversion
        pixel_img = pixels.reshape(1, -1, 3).astype(np.uint8)
        hsv = cv2.cvtColor(pixel_img, cv2.COLOR_BGR2HSV).reshape(-1, 3)

        # Skin color ranges in HSV
        # Hue: 0-50 (red-yellow range covers most skin tones)
        # Saturation: 20-200 (avoid very grey or very saturated)
        # Value: 50-250 (avoid very dark shadows and blown-out highlights)
        mask = (
            (hsv[:, 0] <= 50) &
            (hsv[:, 1] >= 20) & (hsv[:, 1] <= 200) &
            (hsv[:, 2] >= 50) & (hsv[:, 2] <= 250)
        )

        filtered = pixels[mask]
        return filtered if len(filtered) >= 10 else pixels

    def _find_dominant_color(self, pixels: np.ndarray) -> tuple:
        """
        Use K-Means clustering to find the dominant skin color.
        We use k=3 to separate skin from minor shadows/highlights,
        then pick the cluster closest to typical skin color.
        """
        k = min(3, len(pixels))
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(pixels)

        # Find the largest cluster — most likely the dominant skin tone
        labels, counts = np.unique(kmeans.labels_, return_counts=True)
        dominant_idx = labels[np.argmax(counts)]
        dominant = kmeans.cluster_centers_[dominant_idx]

        return tuple(dominant)

    def _find_representative_color(self, pixels: np.ndarray) -> tuple:
        """
        Estimate skin color from the stable center of the LAB distribution.
        This is more robust than picking only the largest RGB K-Means cluster.
        """
        pixel_img = pixels.reshape(1, -1, 3).astype(np.uint8)
        lab = cv2.cvtColor(pixel_img, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)
        l_vals = lab[:, 0]
        low, high = np.percentile(l_vals, [18, 82])
        stable = pixels[(l_vals >= low) & (l_vals <= high)]
        if len(stable) < 20:
            stable = pixels

        kmeans_color = np.array(self._find_dominant_color(stable), dtype=np.float32)
        median_color = np.median(stable, axis=0)
        representative = (0.55 * median_color) + (0.45 * kmeans_color)
        return tuple(np.clip(representative, 0, 255))

    def _bgr_to_hex(self, bgr: np.ndarray) -> str:
        b, g, r = [int(v) for v in np.clip(bgr, 0, 255)]
        return "#{:02x}{:02x}{:02x}".format(r, g, b)

    def _compute_sample_quality(self, original_pixels: np.ndarray, filtered: np.ndarray,
                                region_pixels: dict = None) -> dict:
        """Score whether extracted samples are trustworthy enough for commerce-grade matching."""
        skin_pixel_ratio = len(filtered) / max(len(original_pixels), 1)
        sample_count_score = min(1.0, len(filtered) / 450.0)
        ratio_score = min(1.0, skin_pixel_ratio / 0.72)

        region_consistency = None
        if region_pixels:
            region_hexes = []
            for pixels in region_pixels.values():
                if pixels and len(pixels) >= 10:
                    arr = self._filter_skin_pixels(np.array(pixels, dtype=np.float32))
                    if len(arr) >= 10:
                        region_hexes.append(self._bgr_to_hex(np.median(arr, axis=0)))

            if len(region_hexes) >= 2:
                distances = []
                for i in range(len(region_hexes)):
                    for j in range(i + 1, len(region_hexes)):
                        distances.append(delta_e_ciede2000(region_hexes[i], region_hexes[j]))
                region_consistency = round(float(np.mean(distances)), 2)

        consistency_score = 1.0
        if region_consistency is not None:
            consistency_score = max(0.0, 1.0 - min(region_consistency, 18) / 18)

        score = int(round((0.35 * sample_count_score + 0.30 * ratio_score + 0.35 * consistency_score) * 100))
        if score >= 78:
            label = "high"
        elif score >= 55:
            label = "medium"
        else:
            label = "low"

        warnings = []
        if len(filtered) < 180:
            warnings.append("low_skin_sample_count")
        if skin_pixel_ratio < 0.45:
            warnings.append("possible_occlusion_or_background_noise")
        if region_consistency is not None and region_consistency > 10:
            warnings.append("uneven_regional_color")

        return {
            "score": max(0, min(100, score)),
            "label": label,
            "skin_pixel_ratio": round(float(skin_pixel_ratio), 3),
            "filtered_sample_count": int(len(filtered)),
            "region_delta_e": region_consistency,
            "warnings": warnings,
        }

    def _get_shade_name(self, luminance: float) -> dict:
        """Map luminance value to a shade name."""
        for shade in SHADE_RANGES:
            low, high = shade["range"]
            if low <= luminance < high:
                return {"name": shade["name"], "code": shade["code"]}

        # Default fallback
        if luminance >= 255:
            return {"name": SHADE_RANGES[0]["name"], "code": SHADE_RANGES[0]["code"]}
        return {"name": SHADE_RANGES[-1]["name"], "code": SHADE_RANGES[-1]["code"]}

    def _classify_undertone(self, r: float, g: float, b: float) -> dict:
        """
        Classify undertone as warm, cool, or neutral based on RGB channel ratios.

        Warm: Higher red/yellow — R > B, and green is relatively high
        Cool: Higher blue/pink — B >= R, or strong pink hue
        Neutral: Balanced — R and B are close together
        """
        # Calculate ratios
        rb_ratio = r / (b + 1e-6)  # Avoid division by zero
        rg_ratio = r / (g + 1e-6)

        # Calculate the difference between R and B channels
        rb_diff = abs(r - b)
        total = r + g + b + 1e-6

        # Normalized channel proportions
        r_prop = r / total
        b_prop = b / total

        pixel = np.array([[[b, g, r]]], dtype=np.uint8)
        lab = cv2.cvtColor(pixel, cv2.COLOR_BGR2LAB)[0][0].astype(float)
        lab_a = lab[1] - 128.0
        lab_b = lab[2] - 128.0

        # Classification logic
        confidence = 0.0

        if rb_diff < 15 and abs(lab_a) < 10:
            # R and B are very close → Neutral
            undertone_type = "neutral"
            description = "Your skin has a balanced undertone — neither warm nor cool. You can wear both gold and silver jewelry."
            confidence = 0.7 + (15 - rb_diff) / 15 * 0.3

        elif (r > b and rb_ratio > 1.1) or lab_b > 17:
            # Significantly more red → Warm
            undertone_type = "warm"
            description = "Your skin has warm, golden-yellow undertones. Gold jewelry and earthy tones complement you best."
            confidence = min(0.95, 0.6 + (rb_ratio - 1.0) * 0.3)

        elif (b >= r and rb_ratio < 0.95) or lab_a > 13:
            # More blue → Cool
            undertone_type = "cool"
            description = "Your skin has cool, pink-blue undertones. Silver jewelry and jewel tones look great on you."
            confidence = min(0.95, 0.6 + (1.0 / rb_ratio - 1.0) * 0.3)

        else:
            # Slight lean but not definitive → Neutral-leaning
            if r > b:
                undertone_type = "neutral-warm"
                description = "Your skin has a neutral-warm undertone — slightly golden. Both warm and neutral shades work well."
            else:
                undertone_type = "neutral-cool"
                description = "Your skin has a neutral-cool undertone — slightly pink. Both cool and neutral shades work well."
            confidence = 0.6

        return {
            "type": undertone_type,
            "description": description,
            "confidence": confidence
        }

    def _combine_confidence(self, undertone_confidence: float, sample_quality: dict,
                            ml_prediction: dict, ita_category: str) -> float:
        quality_factor = sample_quality.get("score", 65) / 100.0
        ml_factor = 0.65
        if ml_prediction:
            ml_factor = float(ml_prediction.get("confidence", 0.65))
            tone_info = ml_prediction.get("tone_info", {})
            if ita_category in tone_info.get("ita_categories", []):
                ml_factor = min(0.98, ml_factor + 0.08)

        confidence = (0.45 * undertone_confidence) + (0.35 * quality_factor) + (0.20 * ml_factor)
        return round(max(0.25, min(0.98, confidence)), 2)

    def _compute_ita(self, dominant_bgr: tuple) -> tuple:
        """
        Compute Individual Typology Angle (ITA) from dominant BGR color.
        ITA = atan2(L - 50, b) * (180 / pi) where L, b are from CIE-LAB.
        """
        pixel = np.array([[[dominant_bgr[0], dominant_bgr[1], dominant_bgr[2]]]], dtype=np.uint8)
        lab = cv2.cvtColor(pixel, cv2.COLOR_BGR2LAB)
        L_raw, _, b_raw = lab[0][0].astype(float)
        # Convert OpenCV LAB to standard LAB
        L = L_raw * 100.0 / 255.0
        b = b_raw - 128.0

        if abs(b) < 1e-6:
            b = 1e-6
        ita_angle = math.atan2(L - 50, b) * (180.0 / math.pi)
        ita_angle = round(ita_angle, 2)

        if ita_angle > 55:
            category = "Very Light"
        elif ita_angle > 41:
            category = "Light"
        elif ita_angle > 28:
            category = "Intermediate"
        elif ita_angle > 10:
            category = "Tan"
        elif ita_angle > -30:
            category = "Brown"
        else:
            category = "Dark"

        return ita_angle, category

    def _compute_skin_health(self, region_pixels: dict = None) -> dict:
        """
        Compute skin health indicators from regional pixel data.
        """
        if not region_pixels:
            return {
                "hydration_estimate": "moderate",
                "evenness_score": 75,
                "tip": "Upload a clear, well-lit selfie for more accurate skin health analysis.",
            }

        # Collect per-region stats
        region_means = []
        all_sat_vars = []

        for region_name in ["forehead", "left_cheek", "right_cheek"]:
            pixels = region_pixels.get(region_name, [])
            if not pixels or len(pixels) < 3:
                continue

            arr = np.array(pixels, dtype=np.uint8).reshape(1, -1, 3)
            hsv = cv2.cvtColor(arr, cv2.COLOR_BGR2HSV).reshape(-1, 3)
            lab = cv2.cvtColor(arr, cv2.COLOR_BGR2LAB).reshape(-1, 3)

            sat_var = float(np.var(hsv[:, 1]))
            all_sat_vars.append(sat_var)

            region_means.append(lab.mean(axis=0))

        # Hydration estimate based on saturation variance
        avg_sat_var = float(np.mean(all_sat_vars)) if all_sat_vars else 500.0
        if avg_sat_var < 300:
            hydration = "good"
        elif avg_sat_var < 800:
            hydration = "moderate"
        else:
            hydration = "low"

        # Evenness score based on color standard deviation across regions
        if len(region_means) >= 2:
            region_arr = np.array(region_means, dtype=float)
            color_std = float(np.mean(np.std(region_arr, axis=0)))
            evenness = max(0, min(100, int(100 - color_std * 2.5)))
        else:
            evenness = 75

        # Contextual tip
        if hydration == "low" and evenness < 50:
            tip = "Your skin appears a bit dry and uneven. Consider a hydrating primer and color-correcting concealer."
        elif hydration == "low":
            tip = "Your skin could use more hydration. Try a moisturizing primer or dewy foundation."
        elif evenness < 50:
            tip = "Your skin tone varies across regions. A color-correcting primer can help even things out."
        elif hydration == "good" and evenness >= 80:
            tip = "Your skin looks well-hydrated and even — a great canvas for any makeup look!"
        else:
            tip = "Your skin is in good shape. A lightweight foundation will enhance your natural glow."

        return {
            "hydration_estimate": hydration,
            "evenness_score": evenness,
            "tip": tip,
        }

    def _compute_color_harmony(self, undertone: str) -> dict:
        """
        Generate color harmony recommendations based on undertone.
        Uses color theory: warm undertones pair with earth tones,
        cool with jewel tones, neutral with both.
        """
        warm_clothing = ["#C8553D", "#E8985E", "#D4A574", "#8B6914", "#A0522D", "#CC7722"]
        cool_clothing = ["#4B0082", "#2E4057", "#800020", "#008080", "#483D8B", "#4169E1"]
        neutral_clothing = ["#556B2F", "#8B4513", "#4682B4", "#708090", "#9370DB", "#CD853F"]

        warm_lips = ["#C04000", "#CC5533", "#B5651D", "#A0522D"]
        cool_lips = ["#C71585", "#DC143C", "#8B0000", "#B22222"]
        neutral_lips = ["#BC544B", "#CD5C5C", "#C04040", "#A52A2A"]

        warm_avoid = ["#C0C0C0", "#4169E1", "#FF69B4"]
        cool_avoid = ["#FF8C00", "#DAA520", "#CD853F"]
        neutral_avoid = ["#FF4500", "#00FF00", "#FF00FF"]

        if undertone in ("warm", "neutral-warm"):
            return {
                "best_clothing_colors": warm_clothing,
                "best_jewelry": "gold",
                "best_lip_colors": warm_lips,
                "avoid_colors": warm_avoid,
            }
        elif undertone in ("cool", "neutral-cool"):
            return {
                "best_clothing_colors": cool_clothing,
                "best_jewelry": "silver",
                "best_lip_colors": cool_lips,
                "avoid_colors": cool_avoid,
            }
        else:
            return {
                "best_clothing_colors": neutral_clothing,
                "best_jewelry": "all",
                "best_lip_colors": neutral_lips,
                "avoid_colors": neutral_avoid,
            }
