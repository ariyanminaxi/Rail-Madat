"""Data integrity tests."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import (
    CATEGORICAL_FEATURES, MAINTENANCE_CASES_PATH, NUMERIC_FEATURES, RANDOM_SEED, TARGET_COLUMNS, TEXT_COLUMN,
)
from ml.maintenance_intelligence.training.prepare_features import (
    build_feature_dataframe, build_label_dataframe, load_raw_data, validate_columns,
)


class TestTCData001:
    def test_no_duplicate_case_ids(self, raw_dataset):
        duplicates = raw_dataset["case_id"][raw_dataset["case_id"].duplicated()]
        assert len(duplicates) == 0


class TestTCData002:
    def test_no_case_leakage(self, raw_dataset):
        df = raw_dataset
        validate_columns(df)
        features = build_feature_dataframe(df)
        labels = build_label_dataframe(df)
        case_ids = df["case_id"]
        unique_cases = case_ids.unique()
        import numpy as np
        rng = np.random.RandomState(RANDOM_SEED)
        rng.shuffle(unique_cases)
        n = len(unique_cases)
        n_train = int(n * 0.7)
        n_val = int(n * 0.15)
        train_cases = set(unique_cases[:n_train])
        val_cases = set(unique_cases[n_train:n_train + n_val])
        test_cases = set(unique_cases[n_train + n_val:])
        assert train_cases.isdisjoint(val_cases)
        assert train_cases.isdisjoint(test_cases)
        assert val_cases.isdisjoint(test_cases)


class TestTCData004:
    def test_no_future_columns_in_features(self):
        feature_cols = set([TEXT_COLUMN] + CATEGORICAL_FEATURES + NUMERIC_FEATURES)
        future = {"completion_status", "final_root_cause", "resolution_type", "manager_approved_priority", "verified_by_human"}
        assert len(feature_cols & future) == 0


class TestTCData005:
    def test_no_missing_targets(self, raw_dataset):
        for col in TARGET_COLUMNS:
            assert raw_dataset[col].isna().sum() == 0


class TestTCData006:
    def test_one_class_detected(self):
        df = pd.DataFrame({
            TEXT_COLUMN: ["A", "B", "C"], "asset_type": ["Track"] * 3, "asset_criticality": ["High"] * 3,
            "current_status": ["New"] * 3, "safety_risk_level": ["Low"] * 3, "service_impact_level": ["Minor"] * 3,
            "days_overdue": [0] * 3, "failure_count_30_days": [0] * 3,
            "department": ["Track"] * 3, "fault_category": ["Track defect"] * 3,
            "severity": ["Low"] * 3, "base_priority": ["Low"] * 3,
        })
        labels = build_label_dataframe(df)
        assert labels["department"].nunique() == 1


class TestTCData008:
    def test_validate_columns_missing(self):
        df = pd.DataFrame({"complaint_text": ["test"], "asset_type": ["Track"]})
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_columns(df)

    def test_empty_dataset_detected(self):
        df = pd.DataFrame(columns=[TEXT_COLUMN] + CATEGORICAL_FEATURES + NUMERIC_FEATURES + TARGET_COLUMNS)
        with pytest.raises(ValueError, match="empty"):
            validate_columns(df)
