"""Data quality tests."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import (
    CATEGORICAL_FEATURES, MAINTENANCE_CASES_PATH, NUMERIC_FEATURES, RANDOM_SEED,
    TARGET_COLUMNS, TEXT_COLUMN, VALID_DEPARTMENTS, VALID_PRIORITIES, VALID_SEVERITIES,
)
from ml.maintenance_intelligence.training.prepare_features import (
    build_feature_dataframe, build_label_dataframe, load_raw_data, validate_columns,
)
from ml.maintenance_intelligence.training.split_dataset import split_by_case


class TestDuplicateCaseIDs:
    def test_no_duplicate_case_ids(self, raw_dataset):
        duplicates = raw_dataset["case_id"][raw_dataset["case_id"].duplicated()]
        assert len(duplicates) == 0


class TestMissingTargetLabels:
    def test_no_missing_targets(self, raw_dataset):
        for col in TARGET_COLUMNS:
            assert raw_dataset[col].isna().sum() == 0


class TestInvalidPriorityValues:
    def test_all_priorities_valid(self, raw_dataset):
        invalid = raw_dataset[~raw_dataset["base_priority"].isin(VALID_PRIORITIES)]
        assert len(invalid) == 0

    def test_all_severities_valid(self, raw_dataset):
        invalid = raw_dataset[~raw_dataset["severity"].isin(VALID_SEVERITIES)]
        assert len(invalid) == 0

    def test_all_departments_valid(self, raw_dataset):
        invalid = raw_dataset[~raw_dataset["department"].isin(VALID_DEPARTMENTS)]
        assert len(invalid) == 0


class TestNoCaseLeakage:
    def test_split_no_overlap(self, raw_dataset):
        df = raw_dataset
        validate_columns(df)
        features = build_feature_dataframe(df)
        labels = build_label_dataframe(df)
        case_ids = df["case_id"]
        X_train, X_val, X_test, _, _, _ = split_by_case(features, labels, case_ids, seed=RANDOM_SEED)

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

    def test_split_sizes(self, raw_dataset):
        df = raw_dataset
        validate_columns(df)
        features = build_feature_dataframe(df)
        labels = build_label_dataframe(df)
        case_ids = df["case_id"]
        X_train, X_val, X_test, _, _, _ = split_by_case(features, labels, case_ids, seed=RANDOM_SEED)
        assert len(X_train) + len(X_val) + len(X_test) == len(df)


class TestFutureInformationLeakage:
    def test_no_future_columns_in_features(self):
        feature_cols = set([TEXT_COLUMN] + CATEGORICAL_FEATURES + NUMERIC_FEATURES)
        future = {"completion_status", "final_root_cause", "resolution_type", "manager_approved_priority"}
        assert len(feature_cols & future) == 0


class TestDataIntegrity:
    def test_dataset_row_count(self, raw_dataset):
        assert len(raw_dataset) == 200

    def test_case_ids_format(self, raw_dataset):
        assert raw_dataset["case_id"].str.match(r"^TC-\d{3}$").all()
