"""Shared pytest fixtures for Maintenance Intelligence test suite."""

import json
import sys
from pathlib import Path

import joblib
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import (
    ARTIFACTS_DIR,
    CONFIDENCE_THRESHOLD,
    CATEGORICAL_FEATURES,
    LABEL_MAPS_PATH,
    MAINTENANCE_CASES_PATH,
    MODEL_MANIFEST_PATH,
    MODEL_PATH,
    NUMERIC_FEATURES,
    RANDOM_SEED,
    TARGET_COLUMNS,
    TEXT_COLUMN,
    VALID_DEPARTMENTS,
    VALID_FAULT_CATEGORIES,
    VALID_PRIORITIES,
    VALID_SEVERITIES,
)
from app.maintenance_intelligence.inference.classifier import classify_case
from app.maintenance_intelligence.inference.confidence import check_confidence
from app.maintenance_intelligence.inference.explanation import generate_explanation
from app.maintenance_intelligence.inference.feature_builder import FEATURE_COLUMNS, build_features
from app.maintenance_intelligence.prioritization.priority_engine import (
    calculate_final_priority,
    requires_human_review,
)
from app.maintenance_intelligence.io_schemas import ComplaintInput


@pytest.fixture
def signal_complaint():
    return ComplaintInput(
        complaint_text="Signal near S-02 is flickering.",
        asset_type="Signal",
        asset_criticality="Safety-Critical",
        current_status="Interrupted",
        days_overdue=2,
        failure_count_30_days=2,
        safety_risk_level="High",
        service_impact_level="Major",
    )


@pytest.fixture
def track_complaint():
    return ComplaintInput(
        complaint_text="Visible crack found near the rail joint in Section S-02.",
        asset_type="Track",
        asset_criticality="Safety-Critical",
        current_status="New",
        days_overdue=0,
        failure_count_30_days=0,
        safety_risk_level="High",
        service_impact_level="Major",
    )


@pytest.fixture
def ambiguous_complaint():
    return ComplaintInput(complaint_text="Equipment is not working properly.")


@pytest.fixture
def extreme_risk_complaint():
    return ComplaintInput(
        complaint_text="Complete signal system failure at junction J-10.",
        asset_type="Signal",
        asset_criticality="Safety-Critical",
        current_status="Escalated",
        days_overdue=5,
        failure_count_30_days=4,
        safety_risk_level="Extreme",
        service_impact_level="Severe",
    )


@pytest.fixture
def interrupted_critical_complaint():
    return ComplaintInput(
        complaint_text="Signal repair was interrupted because testing equipment failed.",
        asset_type="Signal",
        asset_criticality="Safety-Critical",
        current_status="Interrupted",
        days_overdue=3,
        failure_count_30_days=1,
        safety_risk_level="High",
        service_impact_level="Major",
    )


@pytest.fixture
def full_context(signal_complaint):
    return {
        "asset_criticality": signal_complaint.asset_criticality,
        "current_status": signal_complaint.current_status,
        "safety_risk_level": signal_complaint.safety_risk_level,
        "service_impact_level": signal_complaint.service_impact_level,
        "days_overdue": signal_complaint.days_overdue,
        "failure_count_30_days": signal_complaint.failure_count_30_days,
    }


@pytest.fixture(scope="session")
def trained_model():
    if not MODEL_PATH.exists():
        pytest.skip("Model artifact not found")
    return joblib.load(MODEL_PATH)


@pytest.fixture(scope="session")
def label_maps():
    if not LABEL_MAPS_PATH.exists():
        pytest.skip("Label maps not found")
    with open(LABEL_MAPS_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def model_manifest():
    if not MODEL_MANIFEST_PATH.exists():
        pytest.skip("Model manifest not found")
    with open(MODEL_MANIFEST_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def feature_schema():
    schema_path = ARTIFACTS_DIR / "feature_schema.json"
    if not schema_path.exists():
        pytest.skip("Feature schema not found")
    with open(schema_path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def raw_dataset():
    if not MAINTENANCE_CASES_PATH.exists():
        pytest.skip("Training data not found")
    return pd.read_csv(MAINTENANCE_CASES_PATH)


@pytest.fixture
def confidence_threshold():
    return CONFIDENCE_THRESHOLD
