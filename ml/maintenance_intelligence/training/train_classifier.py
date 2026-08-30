"""Train the Maintenance Classifier pipeline.

Pipeline: TF-IDF + OneHotEncoder + Logistic Regression (multi-output)
"""

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multioutput import MultiOutputClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import (
    ARTIFACTS_DIR,
    CATEGORICAL_FEATURES,
    CONFIDENCE_THRESHOLD,
    MODEL_MANIFEST_PATH,
    MODEL_PATH,
    NUMERIC_FEATURES,
    RANDOM_SEED,
    TARGET_COLUMNS,
    TEXT_COLUMN,
)
from ml.maintenance_intelligence.training.prepare_features import (
    build_feature_dataframe,
    build_label_dataframe,
    create_label_mappings,
    load_raw_data,
    save_feature_schema,
    save_label_mappings,
    validate_columns,
)
from ml.maintenance_intelligence.training.split_dataset import split_by_case


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            (
                "text_tfidf",
                TfidfVectorizer(
                    max_features=500,
                    ngram_range=(1, 2),
                    stop_words="english",
                    min_df=2,
                    max_df=0.95,
                    sublinear_tf=True,
                ),
                TEXT_COLUMN,
            ),
            (
                "cat_ohe",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                    min_frequency=2,
                ),
                CATEGORICAL_FEATURES,
            ),
            ("num_passthrough", "passthrough", NUMERIC_FEATURES),
        ],
        remainder="drop",
    )


def build_pipeline(preprocessor: ColumnTransformer) -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                MultiOutputClassifier(
                    LogisticRegression(
                        C=1.0,
                        max_iter=2000,
                        solver="lbfgs",
                        random_state=RANDOM_SEED,
                        class_weight="balanced",
                    ),
                    n_jobs=-1,
                ),
            ),
        ]
    )


def train(data_path=None) -> dict:
    if data_path is None:
        data_path = ARTIFACTS_DIR.parent / "datasets" / "maintenance_cases.csv"

    print("=" * 60)
    print("Maintenance Intelligence — Training Classifier")
    print("=" * 60)

    print("\n[1/6] Loading raw data...")
    df = load_raw_data(data_path)
    validate_columns(df)

    features = build_feature_dataframe(df)
    labels = build_label_dataframe(df)
    case_ids = df["case_id"]

    print("\n[2/6] Saving label mappings and feature schema...")
    label_maps = create_label_mappings(labels)
    save_label_mappings(label_maps)
    save_feature_schema(features)

    print("\n[3/6] Splitting dataset...")
    X_train, X_val, X_test, y_train, y_val, y_test = split_by_case(
        features, labels, case_ids
    )

    print("\n[4/6] Building and training pipeline...")
    preprocessor = build_preprocessor()
    pipeline = build_pipeline(preprocessor)
    pipeline.fit(X_train, y_train)
    print("Training complete.")

    print("\n[5/6] Evaluating on validation set...")
    from sklearn.metrics import accuracy_score, f1_score
    y_val_pred = pipeline.predict(X_val)
    accuracies = []
    f1_scores_macro = []
    for i, col in enumerate(TARGET_COLUMNS):
        acc = accuracy_score(y_val[col], y_val_pred[:, i])
        f1m = f1_score(y_val[col], y_val_pred[:, i], average="macro", zero_division=0)
        accuracies.append(acc)
        f1_scores_macro.append(f1m)
        print(f"  {col}: acc={acc:.4f}, macro_f1={f1m:.4f}")

    print(f"\nOverall Validation Accuracy: {sum(accuracies)/len(accuracies):.4f}")
    print(f"Overall Validation Macro-F1: {sum(f1_scores_macro)/len(f1_scores_macro):.4f}")

    print("\n[6/6] Saving model artifact...")
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

    manifest = {
        "model_name": "maintenance_classifier",
        "model_version": "0.1.0",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset_name": "maintenance_cases.csv",
        "dataset_version": "1.0.0",
        "algorithm": "TF-IDF + Logistic Regression",
        "python_version": platform.python_version(),
        "scikit_learn_version": sklearn.__version__,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "n_training_samples": len(X_train),
        "n_features": X_train.shape[1],
        "target_columns": list(labels.columns),
    }
    with open(MODEL_MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest saved to {MODEL_MANIFEST_PATH}")

    print("\n" + "=" * 60)
    print("Training pipeline complete!")
    print("=" * 60)

    return {
        "val_accuracy": sum(accuracies) / len(accuracies),
        "val_f1_macro": sum(f1_scores_macro) / len(f1_scores_macro),
        "n_train": len(X_train),
        "n_val": len(X_val),
        "n_test": len(X_test),
    }


if __name__ == "__main__":
    results = train()
    print(f"\nResults: {results}")
