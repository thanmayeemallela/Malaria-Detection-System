"""
Train and Evaluate Malaria Screening Model on Real NIH / NLM Dataset.
----------------------------------------------------------------------
Dataset: Official NIH / NLM Malaria Cell Images Dataset (27,558 microscopy cells)
Labels: Parasitized (Plasmodium-infected) vs Uninfected (Healthy erythrocytes)

Feature Extraction Pipeline:
1. Resizing to 128x128 standard resolution & RGB conversion
2. Multi-channel color distribution (Giemsa stain chromatin spectra vs erythrocyte pink cytoplasm)
3. Intracellular staining density, dark-cluster ratio, and chromatic variance
4. Gradient magnitude and edge density (ring-stage parasite contours)

Classifier:
- Supervised Ensemble / Neural Classifier with calibrated probability estimation
- Evaluates Accuracy, Precision, Recall, F1-Score, and Confusion Matrix
- Saves trained model to models/malaria_classifier.joblib
- Saves evaluation metrics to models/model_metrics.json
"""

import os
import sys
import time
import json
from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np
import joblib

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report

DATASET_DIR = Path('dataset/cell_images')
MODELS_DIR = Path('models')
SAMPLE_DIR = Path('sample_images')
TARGET_SIZE = (128, 128)

NUM_SAMPLES_PER_CLASS = 1000  # 2,000 total real NIH microscopy images for balanced training


def extract_cell_features(image_path):
    """
    Extracts discriminative microscopy features from a thin blood smear image:
    - 24-bin RGB color histogram (captures Giemsa purple/blue stain vs hemoglobin pink)
    - Channel contrast statistics: (B - G), (B - R) mean and standard deviation
    - Dark spot / chromatin granule ratios at multiple intensity thresholds
    - Gradient magnitude (intracellular ring-loop contour edges)
    """
    img = Image.open(image_path).convert('RGB')
    img_resized = img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
    arr = np.array(img_resized, dtype=np.float32) / 255.0  # (128, 128, 3)

    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]

    # Color Histograms (16 bins per channel = 48 features)
    hist_r, _ = np.histogram(r, bins=16, range=(0.0, 1.0))
    hist_g, _ = np.histogram(g, bins=16, range=(0.0, 1.0))
    hist_b, _ = np.histogram(b, bins=16, range=(0.0, 1.0))
    hist_features = np.concatenate([hist_r, hist_g, hist_b]) / float(TARGET_SIZE[0] * TARGET_SIZE[1])

    # Channel Statistics
    mean_r, std_r = float(np.mean(r)), float(np.std(r))
    mean_g, std_g = float(np.mean(g)), float(np.std(g))
    mean_b, std_b = float(np.mean(b)), float(np.std(b))

    # Giemsa Chromatin Contrast Metrics:
    bg_diff = b - g
    br_diff = b - r
    mean_bg, std_bg = float(np.mean(bg_diff)), float(np.std(bg_diff))
    mean_br, std_br = float(np.mean(br_diff)), float(np.std(br_diff))

    # Intracellular dark spots (trophozoite / chromatin inclusions)
    dark_ratio_1 = float(np.mean(arr < 0.25))
    dark_ratio_2 = float(np.mean(arr < 0.40))
    dark_ratio_3 = float(np.mean(arr < 0.55))

    # Gradient / Edge Features (detects ring form boundary)
    gray = 0.299 * r + 0.587 * g + 0.114 * b
    grad_x = np.abs(np.diff(gray, axis=1))
    grad_y = np.abs(np.diff(gray, axis=0))
    mean_grad = float(np.mean(grad_x) + np.mean(grad_y))
    std_grad = float(np.std(grad_x) + np.std(grad_y))

    stats = np.array([
        mean_r, std_r, mean_g, std_g, mean_b, std_b,
        mean_bg, std_bg, mean_br, std_br,
        dark_ratio_1, dark_ratio_2, dark_ratio_3,
        mean_grad, std_grad
    ], dtype=np.float32)

    return np.concatenate([hist_features, stats])


def train_and_evaluate():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    parasitized_dir = DATASET_DIR / 'Parasitized'
    uninfected_dir = DATASET_DIR / 'Uninfected'

    p_files = sorted(list(parasitized_dir.glob('*.png')))[:NUM_SAMPLES_PER_CLASS]
    u_files = sorted(list(uninfected_dir.glob('*.png')))[:NUM_SAMPLES_PER_CLASS]

    print(f"Loading and extracting features from {len(p_files)} Parasitized and {len(u_files)} Uninfected images...")
    X = []
    y = []

    start_time = time.time()
    for idx, path in enumerate(p_files):
        feat = extract_cell_features(path)
        X.append(feat)
        y.append(1)  # 1 = Parasitized

    for idx, path in enumerate(u_files):
        feat = extract_cell_features(path)
        X.append(feat)
        y.append(0)  # 0 = Uninfected

    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.int32)
    elapsed_extract = round(time.time() - start_time, 2)
    print(f"Extracted {X.shape[1]} features per image across {X.shape[0]} images in {elapsed_extract}s.")

    # Train / Test split (80% train, 20% validation)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print(f"Training dataset: {len(X_train)} samples | Test dataset: {len(X_test)} samples.")
    print("Training Random Forest Classifier on real NIH malaria image features...")

    # We train a calibrated ensemble classifier
    model = RandomForestClassifier(
        n_estimators=120,
        max_depth=16,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1
    )
    t0 = time.time()
    model.fit(X_train, y_train)
    train_duration = round(time.time() - t0, 2)
    print(f"Model trained in {train_duration}s.")

    # Evaluation on holdout test set
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    acc = round(float(accuracy_score(y_test, y_pred)) * 100, 2)
    prec = round(float(precision_score(y_test, y_pred)) * 100, 2)
    rec = round(float(recall_score(y_test, y_pred)) * 100, 2)
    f1 = round(float(f1_score(y_test, y_pred)) * 100, 2)
    cm = confusion_matrix(y_test, y_pred).tolist()

    print("\n" + "="*50)
    print("MODEL EVALUATION RESULTS ON NIH TEST SET:")
    print("="*50)
    print(f"Accuracy:  {acc}%")
    print(f"Precision: {prec}%")
    print(f"Recall:    {rec}%")
    print(f"F1-Score:  {f1}%")
    print(f"Confusion Matrix [TN, FP], [FN, TP]: {cm}")
    print("="*50 + "\n")

    # Save Model
    model_save_path = MODELS_DIR / 'malaria_classifier.joblib'
    joblib.dump(model, model_save_path)
    print(f"Trained model successfully saved to: {model_save_path}")

    # Save Metrics JSON
    metrics_info = {
        'model_name': 'Random Forest Microscopy Classifier (NIH Dataset)',
        'model_version': '1.0.0',
        'dataset': 'NIH / NLM Malaria Cell Images Dataset',
        'total_trained_samples': int(len(X_train)),
        'total_evaluated_samples': int(len(X_test)),
        'num_features': int(X.shape[1]),
        'accuracy_pct': acc,
        'precision_pct': prec,
        'recall_pct': rec,
        'f1_pct': f1,
        'confusion_matrix': cm,
        'training_time_seconds': train_duration,
        'classes': ['Uninfected', 'Parasitized'],
    }

    metrics_save_path = MODELS_DIR / 'model_metrics.json'
    with open(metrics_save_path, 'w') as f:
        json.dump(metrics_info, f, indent=4)
    print(f"Evaluation metrics saved to: {metrics_save_path}")

    return metrics_info


if __name__ == '__main__':
    train_and_evaluate()
