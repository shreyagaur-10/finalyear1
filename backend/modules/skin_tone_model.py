"""
Skin Tone Model — Loads the trained skin tone classifier and provides
prediction methods that integrate with the existing SkinAnalyzer pipeline.
"""

import os
import math
import pickle
import numpy as np
import cv2


MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "skin_tone_model.pkl")

# Mapping from model classes to shade/ITA categories
TONE_TO_SHADES = {
    "Very_Light": {
        "ita_categories": ["Very Light"],
        "shade_range": (220, 255),
    },
    "Light": {
        "ita_categories": ["Light"],
        "shade_range": (185, 225),
    },
    "Medium": {
        "ita_categories": ["Intermediate"],
        "shade_range": (145, 190),
    },
    "Tan": {
        "ita_categories": ["Tan"],
        "shade_range": (110, 155),
    },
    "Deep": {
        "ita_categories": ["Brown"],
        "shade_range": (75, 120),
    },
    "Rich": {
        "ita_categories": ["Dark"],
        "shade_range": (0, 85),
    },
    "White": {
        "ita_categories": ["Very Light", "Light", "Intermediate"],
        "shade_range": (155, 255),
    },
    "Brown": {
        "ita_categories": ["Intermediate", "Tan"],
        "shade_range": (95, 170),
    },
    "Black": {
        "ita_categories": ["Brown", "Dark"],
        "shade_range": (0, 110),
    },
}

DISPLAY_TONE_LABELS = {
    "Very_Light": "Very Light",
    "Light": "Light",
    "Medium": "Medium",
    "Tan": "Tan",
    "Deep": "Deep",
    "Rich": "Rich",
    "White": "Fair / Light",
    "Brown": "Medium / Tan",
    "Black": "Deep / Rich",
}


class SkinToneClassifier:
    """ML-based skin tone classifier trained on UTKFace dataset."""

    def __init__(self):
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.loaded = False

        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, 'rb') as f:
                    data = pickle.load(f)
                self.model = data["model"]
                self.scaler = data["scaler"]
                self.label_encoder = data["label_encoder"]
                self.loaded = True
            except Exception:
                self.loaded = False

    def predict_from_pixels(self, skin_pixels):
        """
        Predict skin tone category from raw skin pixels (BGR).

        Args:
            skin_pixels: numpy array of shape (N, 3) in BGR format

        Returns:
            dict with predicted_tone, confidence, probabilities
            or None if model not loaded
        """
        if not self.loaded or len(skin_pixels) < 10:
            return None

        features = self._extract_features_from_pixels(skin_pixels)
        if features is None:
            return None

        features_scaled = self.scaler.transform(features.reshape(1, -1))
        prediction = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]

        class_name = self.label_encoder.inverse_transform([prediction])[0]
        confidence = float(probabilities.max())

        prob_dict = {}
        for i, cls in enumerate(self.label_encoder.classes_):
            prob_dict[str(cls)] = round(float(probabilities[i]), 3)

        return {
            "predicted_tone": DISPLAY_TONE_LABELS.get(str(class_name), str(class_name)),
            "model_class": str(class_name),
            "confidence": round(confidence, 3),
            "probabilities": prob_dict,
            "display_probabilities": {
                DISPLAY_TONE_LABELS.get(str(cls), str(cls)): prob
                for cls, prob in prob_dict.items()
            },
            "tone_info": TONE_TO_SHADES.get(str(class_name), {}),
        }

    def _filter_skin_pixels(self, pixels):
        """Filter to keep only likely skin pixels."""
        pixel_img = pixels.reshape(1, -1, 3).astype(np.uint8)
        hsv = cv2.cvtColor(pixel_img, cv2.COLOR_BGR2HSV).reshape(-1, 3)

        mask = (
            (hsv[:, 0] <= 50) &
            (hsv[:, 1] >= 15) & (hsv[:, 1] <= 220) &
            (hsv[:, 2] >= 40) & (hsv[:, 2] <= 250)
        )

        filtered = pixels[mask]
        return filtered if len(filtered) >= 10 else pixels

    def _extract_features_from_pixels(self, pixels):
        """Extract the same features used during training from skin pixels."""
        pixels = np.array(pixels, dtype=np.float32)
        filtered = self._filter_skin_pixels(pixels)

        if len(filtered) < 10:
            return None

        pixel_img = filtered.reshape(1, -1, 3).astype(np.uint8)
        hsv = cv2.cvtColor(pixel_img, cv2.COLOR_BGR2HSV).reshape(-1, 3).astype(np.float32)
        lab = cv2.cvtColor(pixel_img, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)

        mean_b, mean_g, mean_r = filtered.mean(axis=0)
        mean_h, mean_s, mean_v = hsv.mean(axis=0)

        mean_L = lab[:, 0].mean() * 100.0 / 255.0
        mean_a = lab[:, 1].mean() - 128.0
        mean_lab_b = lab[:, 2].mean() - 128.0

        b_val = mean_lab_b if abs(mean_lab_b) > 1e-6 else 1e-6
        ita = math.atan2(mean_L - 50, b_val) * (180.0 / math.pi)

        luminance = 0.299 * mean_r + 0.587 * mean_g + 0.114 * mean_b

        rb_ratio = mean_r / (mean_b + 1e-6)
        rg_ratio = mean_r / (mean_g + 1e-6)
        gb_ratio = mean_g / (mean_b + 1e-6)

        std_l = float(np.std(lab[:, 0]))
        std_a = float(np.std(lab[:, 1]))
        std_lab_b = float(np.std(lab[:, 2]))
        std_s = float(np.std(hsv[:, 1]))
        std_v = float(np.std(hsv[:, 2]))

        L_vals = lab[:, 0] * 100.0 / 255.0
        p10_L = float(np.percentile(L_vals, 10))
        p90_L = float(np.percentile(L_vals, 90))
        median_L = float(np.median(L_vals))
        p25_v = float(np.percentile(hsv[:, 2], 25))
        p75_v = float(np.percentile(hsv[:, 2], 75))

        l_hist = np.histogram(L_vals, bins=8, range=(0, 100))[0].astype(float)
        l_hist = l_hist / (l_hist.sum() + 1e-6)

        s_hist = np.histogram(hsv[:, 1], bins=6, range=(0, 255))[0].astype(float)
        s_hist = s_hist / (s_hist.sum() + 1e-6)

        features = [
            mean_r, mean_g, mean_b,
            mean_h, mean_s, mean_v,
            mean_L, mean_a, mean_lab_b,
            ita, luminance,
            rb_ratio, rg_ratio, gb_ratio,
            std_l, std_a, std_lab_b, std_s, std_v,
            p10_L, median_L, p90_L,
            p25_v, p75_v,
            float(len(filtered)) / len(pixels),
        ]
        features.extend(l_hist.tolist())
        features.extend(s_hist.tolist())

        return np.array(features, dtype=np.float64)
