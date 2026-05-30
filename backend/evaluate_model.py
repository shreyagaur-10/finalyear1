"""
Generate a lightweight robustness report for the trained skin tone model.

The script reuses the training feature extractor and evaluates the saved model
on brightness-shifted images to show how stable predictions are under common
selfie lighting changes.
"""

import json
import os
import pickle

import cv2
import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score

from train_skin_model import (
    SOURCE_CLASSES,
    DATASET_DIR,
    MODEL_PATH,
    extract_features,
    shade_depth_label_from_features,
)


REPORT_PATH = os.path.join(os.path.dirname(__file__), "models", "robustness_report.json")


def adjust_capture(img, alpha=1.0, beta=0, warmth_shift=0):
    shifted = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
    if warmth_shift:
        shifted = shifted.astype(np.int16)
        shifted[:, :, 2] += warmth_shift
        shifted[:, :, 0] -= warmth_shift
        shifted = np.clip(shifted, 0, 255).astype(np.uint8)
    return shifted


def load_model():
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


def collect_samples(limit_per_class=75):
    samples = []
    counts = {}
    for class_name in SOURCE_CLASSES:
        class_dir = os.path.join(DATASET_DIR, class_name)
        files = [
            f for f in os.listdir(class_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
        for fname in files:
            img = cv2.imread(os.path.join(class_dir, fname))
            if img is None:
                continue
            features = extract_features(img)
            if features is None:
                continue
            shade_label = shade_depth_label_from_features(features)
            if counts.get(shade_label, 0) >= limit_per_class:
                continue
            samples.append((img, shade_label))
            counts[shade_label] = counts.get(shade_label, 0) + 1
    return samples


def evaluate():
    model_data = load_model()
    model = model_data["model"]
    scaler = model_data["scaler"]
    label_encoder = model_data["label_encoder"]
    model_classes = set(str(cls) for cls in label_encoder.classes_)

    samples = collect_samples()
    sample_classes = set(label for _, label in samples)
    if not sample_classes.issubset(model_classes):
        report = {
            "status": "incompatible_model_classes",
            "message": "Current model was trained with older labels. Run python3 train_skin_model.py first.",
            "model_classes": sorted(model_classes),
            "expected_classes": sorted(sample_classes),
        }
        os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(json.dumps(report, indent=2))
        return

    scenarios = {
        "original": (1.0, 0, 0),
        "darker_selfie": (1.0, -35, 0),
        "brighter_selfie": (1.0, 35, 0),
        "warm_indoor": (1.0, 0, 12),
        "cool_daylight": (1.0, 0, -12),
    }
    report = {}

    for scenario, (alpha, beta, warmth) in scenarios.items():
        y_true = []
        y_pred = []
        skipped = 0

        for img, label in samples:
            shifted = adjust_capture(img, alpha=alpha, beta=beta, warmth_shift=warmth)
            features = extract_features(shifted)
            if features is None:
                skipped += 1
                continue

            scaled = scaler.transform(np.array(features).reshape(1, -1))
            pred = model.predict(scaled)[0]
            if label not in label_encoder.classes_:
                skipped += 1
                continue
            y_true.append(label_encoder.transform([label])[0])
            y_pred.append(pred)

        report[scenario] = {
            "accuracy": float(accuracy_score(y_true, y_pred)) if y_true else 0.0,
            "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)) if y_true else 0.0,
            "macro_f1": float(f1_score(y_true, y_pred, average="macro")) if y_true else 0.0,
            "samples": len(y_true),
            "skipped": skipped,
        }

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    evaluate()
