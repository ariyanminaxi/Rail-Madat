"""Evaluate the trained Maintenance Classifier model."""

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import (
    LABEL_MAPS_PATH,
    METRICS_PATH,
    MODEL_PATH,
    RANDOM_SEED,
    TARGET_COLUMNS,
)
from ml.maintenance_intelligence.training.prepare_features import (
    build_feature_dataframe,
    build_label_dataframe,
    load_raw_data,
    validate_columns,
)
from ml.maintenance_intelligence.training.split_dataset import split_by_case


def evaluate(target_column: str = None) -> dict:
    print("=" * 60)
    print("Maintenance Intelligence — Model Evaluation")
    print("=" * 60)

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model artifact not found at {MODEL_PATH}")

    pipeline = joblib.load(MODEL_PATH)
    print(f"Loaded model from {MODEL_PATH}")

    with open(LABEL_MAPS_PATH) as f:
        label_maps = json.load(f)

    df = load_raw_data()
    validate_columns(df)

    features = build_feature_dataframe(df)
    labels = build_label_dataframe(df)
    case_ids = df["case_id"]

    X_train, X_val, X_test, y_train, y_val, y_test = split_by_case(
        features, labels, case_ids, seed=RANDOM_SEED
    )

    X_eval, y_eval = X_test, y_test
    print(f"\nEvaluating on test set ({len(X_eval)} samples)")

    y_pred = pipeline.predict(X_eval)
    y_pred_proba = None
    try:
        y_pred_proba = pipeline.predict_proba(X_eval)
    except AttributeError:
        print("Warning: predict_proba not available")

    target_columns = list(y_eval.columns)
    per_class_metrics = {}
    all_confusion_matrices = {}
    accuracies = []
    f1_macros = []
    f1_weighteds = []

    for i, col in enumerate(target_columns):
        y_true_col = y_eval[col].values
        y_pred_col = y_pred[:, i] if y_pred.ndim > 1 else y_pred

        acc = accuracy_score(y_true_col, y_pred_col)
        f1m = f1_score(y_true_col, y_pred_col, average="macro", zero_division=0)
        f1w = f1_score(y_true_col, y_pred_col, average="weighted", zero_division=0)
        accuracies.append(acc)
        f1_macros.append(f1m)
        f1_weighteds.append(f1w)

        report = classification_report(y_true_col, y_pred_col, output_dict=True, zero_division=0)
        per_class_metrics[col] = report

        cm = confusion_matrix(y_true_col, y_pred_col)
        all_confusion_matrices[col] = cm.tolist()

        print(f"\n--- {col} ---")
        print(classification_report(y_true_col, y_pred_col, zero_division=0))

    accuracy = sum(accuracies) / len(accuracies)
    macro_f1 = sum(f1_macros) / len(f1_macros)
    weighted_f1 = sum(f1_weighteds) / len(f1_weighteds)

    print(f"\nOverall Metrics:")
    print(f"  Accuracy:   {accuracy:.4f}")
    print(f"  Macro F1:   {macro_f1:.4f}")
    print(f"  Weighted F1: {weighted_f1:.4f}")

    low_confidence_cases = []
    if y_pred_proba is not None:
        for i, col in enumerate(target_columns):
            if i < len(y_pred_proba):
                probas = y_pred_proba[i]
                max_proba = np.max(probas, axis=1)
                threshold = 0.5
                low_conf_mask = max_proba < threshold
                n_low = np.sum(low_conf_mask)
                if n_low > 0:
                    low_confidence_cases.append({
                        "target": col,
                        "count": int(n_low),
                        "threshold": threshold,
                    })

    metrics = {
        "accuracy": float(accuracy),
        "macro_f1": float(macro_f1),
        "weighted_f1": float(weighted_f1),
        "per_class_metrics": per_class_metrics,
        "confusion_matrix": all_confusion_matrices,
        "low_confidence_cases": low_confidence_cases,
        "n_test_samples": len(X_eval),
        "target_columns": target_columns,
    }

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    print(f"\nMetrics saved to {METRICS_PATH}")

    return metrics


if __name__ == "__main__":
    evaluate()
