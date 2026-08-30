"""Prepare features from raw maintenance case data for model training."""

import json
from pathlib import Path
from typing import Tuple

import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import (
    CATEGORICAL_FEATURES,
    DATASETS_DIR,
    LABEL_MAPS_PATH,
    MAINTENANCE_CASES_PATH,
    NUMERIC_FEATURES,
    TARGET_COLUMNS,
    TEXT_COLUMN,
)


def load_raw_data(path: Path = MAINTENANCE_CASES_PATH) -> pd.DataFrame:
    """Load the raw maintenance cases CSV."""
    if not path.exists():
        raise FileNotFoundError(
            f"Maintenance cases data not found at {path}. "
            "Ensure the Maintenance Data Service has provided the dataset."
        )
    df = pd.read_csv(path)
    print(f"Loaded {len(df)} cases from {path.name}")
    return df


def validate_columns(df: pd.DataFrame) -> None:
    """Verify required columns exist and dataset is not empty."""
    required = (
        [TEXT_COLUMN]
        + CATEGORICAL_FEATURES
        + NUMERIC_FEATURES
        + TARGET_COLUMNS
    )
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if len(df) == 0:
        raise ValueError("Dataset is empty — cannot train on zero rows")


def build_feature_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Extract the feature columns into a clean DataFrame."""
    feature_cols = [TEXT_COLUMN] + CATEGORICAL_FEATURES + NUMERIC_FEATURES
    features = df[feature_cols].copy()

    features[TEXT_COLUMN] = features[TEXT_COLUMN].fillna("")

    for col in NUMERIC_FEATURES:
        features[col] = pd.to_numeric(features[col], errors="coerce").fillna(0).astype(int)

    for col in CATEGORICAL_FEATURES:
        features[col] = features[col].fillna("Unknown")

    return features


def build_label_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Extract the target label columns."""
    labels = df[TARGET_COLUMNS].copy()
    for col in TARGET_COLUMNS:
        labels[col] = labels[col].fillna("Unknown")
    return labels


def create_label_mappings(labels: pd.DataFrame) -> dict:
    """Create integer-to-string mappings for each target column."""
    label_maps = {}
    for col in labels.columns:
        unique_vals = sorted(labels[col].unique())
        label_maps[col] = {str(i): v for i, v in enumerate(unique_vals)}
    return label_maps


def save_label_mappings(label_maps: dict, path: Path = LABEL_MAPS_PATH) -> None:
    """Save label mappings to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(label_maps, f, indent=2)
    print(f"Saved label mappings to {path}")


def save_feature_schema(
    feature_df: pd.DataFrame, path: Path = None
) -> None:
    """Save the feature schema to JSON."""
    if path is None:
        from app.maintenance_intelligence.config import FEATURE_SCHEMA_PATH
        path = FEATURE_SCHEMA_PATH

    schema = {
        "features": [],
        "text_column": TEXT_COLUMN,
        "categorical_features": CATEGORICAL_FEATURES,
        "numeric_features": NUMERIC_FEATURES,
    }

    for col in feature_df.columns:
        dtype = str(feature_df[col].dtype)
        if col == TEXT_COLUMN:
            feature_type = "text"
        elif col in NUMERIC_FEATURES:
            feature_type = "numeric"
        else:
            feature_type = "categorical"
        schema["features"].append({
            "name": col,
            "type": feature_type,
            "dtype": dtype,
            "unique_count": int(feature_df[col].nunique()),
        })

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(schema, f, indent=2)
    print(f"Saved feature schema to {path}")


def prepare_all(
    data_path: Path = MAINTENANCE_CASES_PATH,
) -> Tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Run full feature preparation pipeline."""
    df = load_raw_data(data_path)
    validate_columns(df)

    features = build_feature_dataframe(df)
    labels = build_label_dataframe(df)
    label_maps = create_label_mappings(labels)

    save_label_mappings(label_maps)
    save_feature_schema(features)

    print(f"Prepared {len(features)} samples with {len(features.columns)} features")
    return features, labels, label_maps


if __name__ == "__main__":
    prepare_all()
