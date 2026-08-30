"""Training pipeline tests."""

import json
import sys
from pathlib import Path

import joblib
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import (
    MAINTENANCE_CASES_PATH, METRICS_PATH, MODEL_PATH, RANDOM_SEED, TARGET_COLUMNS,
)
from app.maintenance_intelligence.inference.classifier import classify_case
from app.maintenance_intelligence.io_schemas import ComplaintInput
from app.maintenance_intelligence.prioritization.priority_engine import calculate_final_priority
from ml.maintenance_intelligence.training.prepare_features import (
    build_feature_dataframe, build_label_dataframe, create_label_mappings, load_raw_data, validate_columns,
)
from ml.maintenance_intelligence.training.split_dataset import split_by_case
from ml.maintenance_intelligence.training.train_classifier import build_pipeline, build_preprocessor


class TestDataPreparation:
    def test_load_raw_data(self):
        df = load_raw_data()
        assert len(df) == 200

    def test_validate_columns_passes(self):
        df = load_raw_data()
        validate_columns(df)

    def test_build_features(self):
        df = load_raw_data()
        validate_columns(df)
        features = build_feature_dataframe(df)
        assert features.shape == (200, 8)

    def test_label_maps(self):
        df = load_raw_data()
        validate_columns(df)
        labels = build_label_dataframe(df)
        maps = create_label_mappings(labels)
        assert "department" in maps


class TestDatasetSplit:
    def test_split_sizes(self):
        df = load_raw_data()
        validate_columns(df)
        features = build_feature_dataframe(df)
        labels = build_label_dataframe(df)
        case_ids = df["case_id"]
        X_train, X_val, X_test, _, _, _ = split_by_case(features, labels, case_ids, seed=RANDOM_SEED)
        total = len(X_train) + len(X_val) + len(X_test)
        assert total == 200


class TestModelEvaluation:
    def test_metrics_file_exists(self):
        assert METRICS_PATH.exists()

    def test_metrics_valid_json(self):
        with open(METRICS_PATH) as f:
            metrics = json.load(f)
        assert isinstance(metrics, dict)

    def test_department_accuracy_high(self):
        with open(METRICS_PATH) as f:
            metrics = json.load(f)
        dept_acc = metrics["per_class_metrics"]["department"]["accuracy"]
        assert dept_acc >= 0.85


class TestCriticalCaseAnalysis:
    def test_critical_emergency_recall(self):
        with open(METRICS_PATH) as f:
            metrics = json.load(f)
        bp = metrics["per_class_metrics"]["base_priority"]
        if "Emergency" in bp:
            assert bp["Emergency"].get("recall", 0.0) > 0.0

    def test_no_false_low_for_extreme_cases(self):
        complaint = ComplaintInput(
            complaint_text="Complete signal system failure.",
            asset_type="Signal",
            asset_criticality="Safety-Critical",
            current_status="Interrupted",
            safety_risk_level="Extreme",
            service_impact_level="Severe",
        )
        classification = classify_case(complaint)
        priority_result = calculate_final_priority(
            classification,
            {"asset_criticality": complaint.asset_criticality, "current_status": complaint.current_status,
             "safety_risk_level": complaint.safety_risk_level},
        )
        assert priority_result["final_priority"] in ("Critical", "Emergency")


class TestPreprocessingSafety:
    def test_build_preprocessor_returns_transformer(self):
        from sklearn.compose import ColumnTransformer
        assert isinstance(build_preprocessor(), ColumnTransformer)

    def test_preprocessor_not_fitted(self):
        p = build_preprocessor()
        assert not hasattr(p, "transformers_")
