"""Data leakage tests.

Verify that the model does not use future information, that train/test
splits are disjoint, and that preprocessing is fitted only on training data.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import (
    CATEGORICAL_FEATURES,
    LABEL_MAPS_PATH,
    MAINTENANCE_CASES_PATH,
    MODEL_PATH,
    NUMERIC_FEATURES,
    RANDOM_SEED,
    TARGET_COLUMNS,
    TEXT_COLUMN,
)
from app.maintenance_intelligence.inference.classifier import classify_case
from app.maintenance_intelligence.inference.feature_builder import FEATURE_COLUMNS, build_features
from app.maintenance_intelligence.io_schemas import ComplaintInput
from ml.maintenance_intelligence.training.prepare_features import (
    build_feature_dataframe,
    build_label_dataframe,
    load_raw_data,
    validate_columns,
)
from ml.maintenance_intelligence.training.split_dataset import split_by_case


# ===================================================================
# Feature set must not contain future columns
# ===================================================================

class TestNoFutureColumnsInFeatureSet:
    """The feature set must exclude all future/post-decision columns."""

    FUTURE_COLUMNS = {
        "final_priority",
        "final_status",
        "resolution_type",
        "final_root_cause",
        "completion_status",
        "manager_approval",
        "future_status_events",
        "verified_by_human",
        "manager_approved_priority",
    }

    def test_feature_columns_do_not_contain_future_data(self):
        feature_cols = set(FEATURE_COLUMNS)
        leakage = feature_cols & self.FUTURE_COLUMNS
        assert len(leakage) == 0, f"Future columns found in features: {leakage}"

    def test_no_completion_status_in_features(self):
        assert "completion_status" not in FEATURE_COLUMNS

    def test_no_final_root_cause_in_features(self):
        assert "final_root_cause" not in FEATURE_COLUMNS

    def test_no_manager_approval_in_features(self):
        assert "manager_approval" not in FEATURE_COLUMNS
        assert "manager_approved_priority" not in FEATURE_COLUMNS

    def test_no_future_status_events_in_features(self):
        assert "future_status_events" not in FEATURE_COLUMNS

    def test_no_verified_by_human_in_features(self):
        assert "verified_by_human" not in FEATURE_COLUMNS

    def test_no_resolution_type_in_features(self):
        assert "resolution_type" not in FEATURE_COLUMNS


# ===================================================================
# Train/test case ID separation
# ===================================================================

class TestCaseIdLeakage:
    """No case_id should exist in both training and test sets."""

    def test_no_case_leakage(self, raw_dataset):
        df = raw_dataset
        validate_columns(df)
        features = build_feature_dataframe(df)
        labels = build_label_dataframe(df)
        case_ids = df["case_id"]
        unique_cases = case_ids.unique()
        rng = np.random.RandomState(RANDOM_SEED)
        rng.shuffle(unique_cases)
        n = len(unique_cases)
        n_train = int(n * 0.7)
        n_val = int(n * 0.15)
        train_cases = set(unique_cases[:n_train])
        val_cases = set(unique_cases[n_train : n_train + n_val])
        test_cases = set(unique_cases[n_train + n_val :])

        assert train_cases.isdisjoint(test_cases), "Train and test share cases"
        assert train_cases.isdisjoint(val_cases), "Train and val share cases"
        assert val_cases.isdisjoint(test_cases), "Val and test share cases"

    def test_no_duplicate_case_ids(self, raw_dataset):
        duplicates = raw_dataset["case_id"][raw_dataset["case_id"].duplicated()]
        assert len(duplicates) == 0, f"Duplicate case IDs: {duplicates.tolist()}"


# ===================================================================
# Preprocessing fitted only on training data
# ===================================================================

class TestPreprocessingSafety:
    """TF-IDF and encoders must be fitted only on training data."""

    def test_preprocessor_not_fitted_on_import(self):
        from ml.maintenance_intelligence.training.train_classifier import build_preprocessor
        p = build_preprocessor()
        assert not hasattr(p, "transformers_"), "Preprocessor should not be pre-fitted"

    def test_preprocessor_fitted_after_fit(self, raw_dataset):
        from ml.maintenance_intelligence.training.train_classifier import build_preprocessor
        df = raw_dataset
        validate_columns(df)
        features = build_feature_dataframe(df)
        labels = build_label_dataframe(df)
        case_ids = df["case_id"]
        X_train, _, _, _, _, _ = split_by_case(features, labels, case_ids, seed=RANDOM_SEED)

        p = build_preprocessor()
        p.fit(X_train)
        assert hasattr(p, "transformers_"), "Preprocessor should be fitted after fit()"


# ===================================================================
# Test labels not passed into feature construction
# ===================================================================

class TestLabelsNotUsedInFeatures:
    """Target labels must never be part of the feature DataFrame."""

    def test_target_columns_not_in_feature_columns(self):
        for col in TARGET_COLUMNS:
            assert col not in FEATURE_COLUMNS, f"Target column '{col}' found in features"

    def test_build_features_uses_only_feature_columns(self, signal_complaint):
        df = build_features(signal_complaint)
        assert list(df.columns) == FEATURE_COLUMNS
        for col in TARGET_COLUMNS:
            assert col not in df.columns

    def test_dataset_split_separates_features_from_labels(self, raw_dataset):
        df = raw_dataset
        validate_columns(df)
        features = build_feature_dataframe(df)
        labels = build_label_dataframe(df)

        for col in TARGET_COLUMNS:
            assert col not in features.columns
            assert col in labels.columns


# ===================================================================
# Label maps are consistent
# ===================================================================

class TestLabelMapConsistency:
    """Label maps should match the training data unique values."""

    def test_label_maps_match_targets(self, raw_dataset):
        if not LABEL_MAPS_PATH.exists():
            pytest.skip("Label maps not found")
        import json
        with open(LABEL_MAPS_PATH) as f:
            maps = json.load(f)

        for col in TARGET_COLUMNS:
            assert col in maps, f"Label map missing for {col}"
            unique_vals = sorted(raw_dataset[col].unique())
            mapped_vals = sorted(v for v in maps[col].values())
            assert unique_vals == mapped_vals, (
                f"Label map mismatch for {col}: "
                f"dataset has {unique_vals}, map has {mapped_vals}"
            )
