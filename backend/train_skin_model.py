"""
Train a skin tone classification model using the UTKFace-based dataset.

Dataset structure:
    dataset/
        Black/   (500 images)
        Brown/   (500 images)
        White/   (500 images)

Features extracted per image:
    - Mean LAB (L, a, b) values from skin-filtered pixels
    - Mean HSV (H, S, V) values
    - Mean RGB (R, G, B) values
    - ITA angle
    - Color channel std devs
    - R/B ratio, R/G ratio

Model: SVM with RBF kernel (works well with small datasets + color features)
Output: backend/models/skin_tone_model.pkl
"""

import os
import sys
import math
import json
import pickle
import numpy as np
import cv2
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold, cross_val_score
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from modules.lighting import normalize_lighting

# Paths
DATASET_DIR = os.path.join(os.path.dirname(__file__), "..", "dataset")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "skin_tone_model.pkl")

SOURCE_CLASSES = ["Black", "Brown", "White"]
SHADE_DEPTH_CLASSES = ["Very_Light", "Light", "Medium", "Tan", "Deep", "Rich"]
MIDTONE_CLASSES = {"Medium", "Tan"}
TRAIN_N_JOBS = int(os.getenv("TRAIN_N_JOBS", "1"))

FEATURE_NAMES = [
    "mean_r", "mean_g", "mean_b",
    "mean_h", "mean_s", "mean_v",
    "mean_L", "mean_a", "mean_lab_b",
    "ita", "luminance",
    "rb_ratio", "rg_ratio", "gb_ratio",
    "std_l", "std_a", "std_lab_b", "std_s", "std_v",
    "p10_L", "median_L", "p90_L",
    "p25_v", "p75_v",
    "skin_pixel_ratio",
    *[f"L_hist_{i}" for i in range(8)],
    *[f"S_hist_{i}" for i in range(6)],
]

AUGMENTATION_PROFILES = [
    ("original", 1.00, 0, 0),
    ("low_light", 0.88, -22, 0),
    ("bright_selfie", 1.08, 18, 0),
    ("warm_indoor", 1.00, 0, 9),
    ("cool_daylight", 1.00, 0, -8),
]

MIDTONE_EXTRA_AUGMENTATION_PROFILES = [
    ("midtone_soft_shadow", 0.94, -10, 0),
    ("midtone_window_light", 1.04, 8, -4),
    ("midtone_warm_store_light", 1.02, 4, 14),
]


def filter_skin_pixels(pixels):
    """Filter pixels to keep only likely skin-colored ones using HSV ranges."""
    pixel_img = pixels.reshape(1, -1, 3).astype(np.uint8)
    hsv = cv2.cvtColor(pixel_img, cv2.COLOR_BGR2HSV).reshape(-1, 3)

    mask = (
        (hsv[:, 0] <= 50) &
        (hsv[:, 1] >= 15) & (hsv[:, 1] <= 220) &
        (hsv[:, 2] >= 40) & (hsv[:, 2] <= 250)
    )

    filtered = pixels[mask]
    return filtered if len(filtered) >= 10 else pixels


def extract_features(img):
    """
    Extract color-based features from a face image.
    Includes multi-region sampling, percentile features, and color histograms.
    """
    # Match production inference: normalize capture lighting before sampling skin regions.
    img = normalize_lighting(img)
    h, w = img.shape[:2]

    pixels = extract_inference_matched_face_pixels(img)
    if pixels is None or len(pixels) < 10:
        return None
    filtered = filter_skin_pixels(pixels)

    if len(filtered) < 10:
        return None

    # Convert to different color spaces
    pixel_img = filtered.reshape(1, -1, 3).astype(np.uint8)
    hsv = cv2.cvtColor(pixel_img, cv2.COLOR_BGR2HSV).reshape(-1, 3).astype(np.float32)
    lab = cv2.cvtColor(pixel_img, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)

    # Mean BGR
    mean_b, mean_g, mean_r = filtered.mean(axis=0)

    # Mean HSV
    mean_h, mean_s, mean_v = hsv.mean(axis=0)

    # Mean LAB (convert to standard scale)
    mean_L = lab[:, 0].mean() * 100.0 / 255.0
    mean_a = lab[:, 1].mean() - 128.0
    mean_lab_b = lab[:, 2].mean() - 128.0

    # ITA angle
    b_val = mean_lab_b if abs(mean_lab_b) > 1e-6 else 1e-6
    ita = math.atan2(mean_L - 50, b_val) * (180.0 / math.pi)

    # Luminance
    luminance = 0.299 * mean_r + 0.587 * mean_g + 0.114 * mean_b

    # Channel ratios
    rb_ratio = mean_r / (mean_b + 1e-6)
    rg_ratio = mean_r / (mean_g + 1e-6)
    gb_ratio = mean_g / (mean_b + 1e-6)

    # Std deviations (capture color variation)
    std_l = float(np.std(lab[:, 0]))
    std_a = float(np.std(lab[:, 1]))
    std_lab_b = float(np.std(lab[:, 2]))
    std_s = float(np.std(hsv[:, 1]))
    std_v = float(np.std(hsv[:, 2]))

    # Percentile features (robust to outliers)
    L_vals = lab[:, 0] * 100.0 / 255.0
    p10_L = float(np.percentile(L_vals, 10))
    p90_L = float(np.percentile(L_vals, 90))
    median_L = float(np.median(L_vals))
    p25_v = float(np.percentile(hsv[:, 2], 25))
    p75_v = float(np.percentile(hsv[:, 2], 75))

    # Color histogram features (compact representation)
    l_hist = np.histogram(L_vals, bins=8, range=(0, 100))[0].astype(float)
    l_hist = l_hist / (l_hist.sum() + 1e-6)

    s_hist = np.histogram(hsv[:, 1], bins=6, range=(0, 255))[0].astype(float)
    s_hist = s_hist / (s_hist.sum() + 1e-6)

    features = [
        mean_r, mean_g, mean_b,                 # 3: RGB means
        mean_h, mean_s, mean_v,                  # 3: HSV means
        mean_L, mean_a, mean_lab_b,              # 3: LAB means
        ita,                                     # 1: ITA angle
        luminance,                               # 1: Luminance
        rb_ratio, rg_ratio, gb_ratio,            # 3: Channel ratios
        std_l, std_a, std_lab_b, std_s, std_v,   # 5: Std deviations
        p10_L, median_L, p90_L,                  # 3: L percentiles
        p25_v, p75_v,                            # 2: V percentiles
        float(len(filtered)) / len(pixels),      # 1: Skin pixel ratio
    ]
    features.extend(l_hist.tolist())              # 8: L histogram
    features.extend(s_hist.tolist())              # 6: S histogram

    return np.array(features, dtype=np.float64)


def extract_inference_matched_face_pixels(img):
    """
    Match backend inference sampling: forehead + cheek patches from a face crop.
    Dataset images are already cropped faces, so the whole image acts as the bbox.
    """
    h, w = img.shape[:2]
    fx, fy, fw, fh = 0, 0, w, h
    radius = max(5, int(fw * 0.04))
    sample_points = {
        "left_cheek": [
            (fx + int(fw * 0.25), fy + int(fh * 0.55)),
            (fx + int(fw * 0.20), fy + int(fh * 0.50)),
            (fx + int(fw * 0.30), fy + int(fh * 0.60)),
        ],
        "right_cheek": [
            (fx + int(fw * 0.75), fy + int(fh * 0.55)),
            (fx + int(fw * 0.80), fy + int(fh * 0.50)),
            (fx + int(fw * 0.70), fy + int(fh * 0.60)),
        ],
        "forehead": [
            (fx + int(fw * 0.50), fy + int(fh * 0.15)),
            (fx + int(fw * 0.40), fy + int(fh * 0.18)),
            (fx + int(fw * 0.60), fy + int(fh * 0.18)),
        ],
    }

    all_pixels = []
    for points in sample_points.values():
        for cx, cy in points:
            y_start = max(0, cy - radius)
            y_end = min(h, cy + radius)
            x_start = max(0, cx - radius)
            x_end = min(w, cx + radius)
            patch = img[y_start:y_end, x_start:x_end]
            if patch.size > 0:
                all_pixels.append(patch.reshape(-1, 3).astype(np.float32))

    if not all_pixels:
        return None
    return np.vstack(all_pixels)


def shade_depth_label_from_ita(ita):
    if ita > 55:
        return "Very_Light"
    if ita > 41:
        return "Light"
    if ita > 28:
        return "Medium"
    if ita > 10:
        return "Tan"
    if ita > -30:
        return "Deep"
    return "Rich"


def shade_depth_label_from_features(features):
    return shade_depth_label_from_ita(float(features[9]))


def apply_capture_augmentation(img, alpha=1.0, beta=0, warmth_shift=0):
    """
    Simulate common selfie capture conditions.
    alpha/beta adjust brightness/contrast; warmth_shift shifts red/blue balance.
    """
    aug = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
    if warmth_shift:
        aug = aug.astype(np.int16)
        aug[:, :, 2] += warmth_shift
        aug[:, :, 0] -= warmth_shift
        aug = np.clip(aug, 0, 255).astype(np.uint8)
    return aug


def load_image_records():
    """Load image paths and derive 6 shade-depth labels from original image ITA."""
    records = []
    skipped = 0

    for class_name in SOURCE_CLASSES:
        class_dir = os.path.join(DATASET_DIR, class_name)
        if not os.path.isdir(class_dir):
            print(f"  WARNING: {class_dir} not found, skipping")
            continue

        files = [f for f in os.listdir(class_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
        print(f"  Found {class_name}: {len(files)} images...")

        for fname in files:
            path = os.path.join(class_dir, fname)
            img = cv2.imread(path)
            if img is None:
                skipped += 1
                continue
            feat = extract_features(img)
            if feat is None:
                skipped += 1
                continue
            shade_label = shade_depth_label_from_features(feat)
            records.append((path, shade_label, class_name))

    print(f"  Derived shade-depth labels for {len(records)} images, skipped {skipped}")
    return records


def extract_record_features(records, augment=False):
    """Extract features from image records. Augment only training records."""
    features = []
    labels = []
    skipped = 0
    augmentation_counts = {
        name: 0
        for name, *_ in [*AUGMENTATION_PROFILES, *MIDTONE_EXTRA_AUGMENTATION_PROFILES]
    }

    base_profiles = AUGMENTATION_PROFILES if augment else [AUGMENTATION_PROFILES[0]]

    for path, label, _source_class in records:
        img = cv2.imread(path)
        if img is None:
            skipped += 1
            continue

        profiles = list(base_profiles)
        if augment and label in MIDTONE_CLASSES:
            profiles.extend(MIDTONE_EXTRA_AUGMENTATION_PROFILES)

        for profile_name, alpha, beta, warmth in profiles:
            aug_img = apply_capture_augmentation(img, alpha=alpha, beta=beta, warmth_shift=warmth)
            feat = extract_features(aug_img)
            if feat is not None:
                features.append(feat)
                labels.append(label)
                augmentation_counts[profile_name] = augmentation_counts.get(profile_name, 0) + 1
            else:
                skipped += 1

    return np.array(features), np.array(labels), skipped, augmentation_counts


def fit_model_search(X_train_scaled, y_train):
    """Run a compact but meaningful model search over classical ML baselines."""
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    searches = {
        "SVM": GridSearchCV(
            SVC(probability=True, class_weight="balanced", random_state=42),
            {
                "C": [1, 3, 10, 30],
                "gamma": ["scale", 0.01, 0.03, 0.1],
                "kernel": ["rbf"],
            },
            scoring="f1_macro",
            cv=cv,
            n_jobs=TRAIN_N_JOBS,
            refit=True,
        ),
        "RandomForest": GridSearchCV(
            RandomForestClassifier(class_weight="balanced", random_state=42, n_jobs=TRAIN_N_JOBS),
            {
                "n_estimators": [250, 450],
                "max_depth": [12, 18, None],
                "min_samples_leaf": [1, 3],
            },
            scoring="f1_macro",
            cv=cv,
            n_jobs=TRAIN_N_JOBS,
            refit=True,
        ),
        "ExtraTrees": GridSearchCV(
            ExtraTreesClassifier(class_weight="balanced", random_state=42, n_jobs=TRAIN_N_JOBS),
            {
                "n_estimators": [300, 500],
                "max_depth": [12, 18, None],
                "min_samples_leaf": [1, 3],
            },
            scoring="f1_macro",
            cv=cv,
            n_jobs=TRAIN_N_JOBS,
            refit=True,
        ),
    }

    fitted = {}
    for name, search in searches.items():
        print(f"  Searching {name}...")
        search.fit(X_train_scaled, y_train)
        fitted[name] = search
        print(f"    best CV macro-F1: {search.best_score_:.4f}")
        print(f"    best params: {search.best_params_}")
    return fitted


def train():
    """Train the skin tone classification model."""
    print("=" * 60)
    print("ShadeSense AI — Skin Tone Model Training")
    print("=" * 60)
    print(f"Parallel workers: {TRAIN_N_JOBS} (set TRAIN_N_JOBS=4 to speed up on stable Python envs)")

    # Load data
    print("\n[1/5] Loading image records...")
    records = load_image_records()

    if len(records) == 0:
        print("ERROR: No valid samples found. Check dataset path.")
        sys.exit(1)

    labels = np.array([label for _, label, _ in records])
    print(f"  Total images: {len(records)}")
    print("  Source folders:")
    for cls in SOURCE_CLASSES:
        print(f"    {cls}: {sum(source == cls for _, _, source in records)}")
    print("  Derived shade-depth classes:")
    for cls in SHADE_DEPTH_CLASSES:
        print(f"    {cls}: {sum(labels == cls)}")

    usable_classes = [cls for cls in SHADE_DEPTH_CLASSES if sum(labels == cls) >= 2]
    if len(usable_classes) < len(SHADE_DEPTH_CLASSES):
        missing = sorted(set(SHADE_DEPTH_CLASSES) - set(usable_classes))
        print(f"  WARNING: not enough samples for classes: {missing}")
        records = [record for record in records if record[1] in usable_classes]
        labels = np.array([label for _, label, _ in records])

    # Split data
    print("\n[2/5] Splitting original images into train/test (80/20)...")
    train_records, test_records = train_test_split(
        records, test_size=0.2, random_state=42, stratify=labels
    )
    print(f"  Train originals: {len(train_records)}, Test originals: {len(test_records)}")

    print("\n[3/5] Extracting features with training-only augmentation...")
    X_train, y_train_raw, skipped_train, aug_counts = extract_record_features(train_records, augment=True)
    X_test, y_test_raw, skipped_test, _ = extract_record_features(test_records, augment=False)

    if len(X_train) == 0 or len(X_test) == 0:
        print("ERROR: Feature extraction failed. Check dataset images.")
        sys.exit(1)

    label_encoder = LabelEncoder()
    y_train = label_encoder.fit_transform(y_train_raw)
    y_test = label_encoder.transform(y_test_raw)
    print(f"  Classes: {list(label_encoder.classes_)}")
    print(f"  Train feature rows: {len(X_train)}")
    print(f"  Test feature rows:  {len(X_test)}")
    print(f"  Skipped train/test augmentations: {skipped_train}/{skipped_test}")
    print(f"  Augmentation counts: {aug_counts}")

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print("\n[4/5] Training and tuning model candidates...")
    searches = fit_model_search(X_train_scaled, y_train)

    model_comparison = {}
    best_name = None
    best_model = None
    best_macro_f1 = -1

    for name, search in searches.items():
        y_candidate = search.best_estimator_.predict(X_test_scaled)
        metrics = {
            "accuracy": float(accuracy_score(y_test, y_candidate)),
            "balanced_accuracy": float(balanced_accuracy_score(y_test, y_candidate)),
            "macro_f1": float(f1_score(y_test, y_candidate, average="macro")),
            "cv_macro_f1": float(search.best_score_),
            "best_params": search.best_params_,
        }
        model_comparison[name] = metrics
        print(
            f"  {name}: accuracy={metrics['accuracy']:.4f}, "
            f"balanced={metrics['balanced_accuracy']:.4f}, macro-F1={metrics['macro_f1']:.4f}"
        )
        if metrics["macro_f1"] > best_macro_f1:
            best_macro_f1 = metrics["macro_f1"]
            best_name = name
            best_model = search.best_estimator_

    print(f"\n  Best model: {best_name}")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(best_model, X_train_scaled, y_train, cv=cv, scoring='f1_macro')
    print(f"  5-Fold CV Macro-F1: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # Detailed report
    y_pred = best_model.predict(X_test_scaled)
    print(f"\n  Classification Report ({best_name}):")
    report_text = classification_report(
        y_test, y_pred,
        target_names=label_encoder.classes_
    )
    report_dict = classification_report(
        y_test, y_pred,
        target_names=label_encoder.classes_,
        output_dict=True
    )
    print(report_text)

    print("  Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"  {'':>8} ", "  ".join(f"{c:>6}" for c in label_encoder.classes_))
    for i, row in enumerate(cm):
        print(f"  {label_encoder.classes_[i]:>8}  ", "  ".join(f"{v:>6}" for v in row))

    test_accuracy = float(accuracy_score(y_test, y_pred))
    test_balanced_accuracy = float(balanced_accuracy_score(y_test, y_pred))
    test_macro_f1 = float(f1_score(y_test, y_pred, average="macro"))

    # Save model
    print(f"\n[5/5] Saving model to {MODEL_PATH}...")
    os.makedirs(MODEL_DIR, exist_ok=True)

    model_data = {
        "model": best_model,
        "scaler": scaler,
        "label_encoder": label_encoder,
        "model_type": best_name,
        "accuracy": test_accuracy,
        "balanced_accuracy": test_balanced_accuracy,
        "macro_f1": test_macro_f1,
        "cv_macro_f1": float(cv_scores.mean()),
        "cv_std": float(cv_scores.std()),
        "model_comparison": model_comparison,
        "classification_report": report_dict,
        "confusion_matrix": cm.tolist(),
        "feature_names": FEATURE_NAMES,
        "classes": list(label_encoder.classes_),
        "source_classes": SOURCE_CLASSES,
        "label_strategy": "ITA-derived shade depth from inference-matched face regions",
        "augmentation_profiles": [name for name, *_ in AUGMENTATION_PROFILES],
        "midtone_extra_augmentation_profiles": [name for name, *_ in MIDTONE_EXTRA_AUGMENTATION_PROFILES],
    }

    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model_data, f)

    # Also save a metadata JSON for reference
    meta = {
        "model_type": best_name,
        "accuracy": test_accuracy,
        "balanced_accuracy": test_balanced_accuracy,
        "macro_f1": test_macro_f1,
        "cv_macro_f1": float(cv_scores.mean()),
        "cv_std": float(cv_scores.std()),
        "model_comparison": model_comparison,
        "classes": list(label_encoder.classes_),
        "source_classes": SOURCE_CLASSES,
        "label_strategy": "ITA-derived shade depth from inference-matched face regions",
        "feature_count": X_train.shape[1],
        "feature_names": FEATURE_NAMES,
        "training_original_images": len(train_records),
        "test_original_images": len(test_records),
        "training_feature_rows": len(X_train),
        "test_feature_rows": len(X_test),
        "augmentation_profiles": [name for name, *_ in AUGMENTATION_PROFILES],
        "midtone_extra_augmentation_profiles": [name for name, *_ in MIDTONE_EXTRA_AUGMENTATION_PROFILES],
        "augmentation_counts": aug_counts,
        "classification_report": report_dict,
        "confusion_matrix": cm.tolist(),
    }
    with open(os.path.join(MODEL_DIR, "model_metadata.json"), 'w') as f:
        json.dump(meta, f, indent=2)

    print(f"  Model saved successfully!")
    print(f"\n{'=' * 60}")
    print(f"Training complete! Accuracy: {test_accuracy:.1%}, Macro-F1: {test_macro_f1:.1%}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    train()
