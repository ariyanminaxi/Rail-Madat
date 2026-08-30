"""Maintenance Intelligence Service configuration constants."""

import os
from pathlib import Path

# Base paths
SERVICE_ROOT = Path(__file__).resolve().parent
ML_ROOT = SERVICE_ROOT.parent.parent / "ml" / "maintenance_intelligence"
ARTIFACTS_DIR = ML_ROOT / "model_artifacts"
DATASETS_DIR = ML_ROOT / "datasets"

# Model artifact paths
MODEL_PATH = ARTIFACTS_DIR / "maintenance_classifier.joblib"
LABEL_MAPS_PATH = ARTIFACTS_DIR / "label_maps.json"
MODEL_MANIFEST_PATH = ARTIFACTS_DIR / "model_manifest.json"
METRICS_PATH = ARTIFACTS_DIR / "metrics.json"
FEATURE_SCHEMA_PATH = ARTIFACTS_DIR / "feature_schema.json"

# Training data paths
MAINTENANCE_CASES_PATH = DATASETS_DIR / "maintenance_cases.csv"
STATUS_HISTORY_PATH = DATASETS_DIR / "workflow_history.csv"
DATASET_MANIFEST_PATH = DATASETS_DIR / "dataset_manifest.json"

# Model settings
CONFIDENCE_THRESHOLD = float(os.environ.get("MAINTENANCE_CONFIDENCE_THRESHOLD", "0.75"))
RANDOM_SEED = 42

# Text features used by the classifier
TEXT_COLUMN = "complaint_text"

# Categorical features
CATEGORICAL_FEATURES = [
    "asset_type",
    "asset_criticality",
    "current_status",
    "safety_risk_level",
    "service_impact_level",
]

# Numeric features
NUMERIC_FEATURES = [
    "days_overdue",
    "failure_count_30_days",
]

# Target labels the classifier predicts
TARGET_COLUMNS = [
    "department",
    "fault_category",
    "severity",
    "base_priority",
]

# Valid values (for validation)
VALID_DEPARTMENTS = ["Track", "Signalling", "Electrical", "Mechanical", "Civil", "Telecom"]
VALID_FAULT_CATEGORIES = [
    "Signal malfunction",
    "Track defect",
    "Electrical fault",
    "Structural damage",
    "Mechanical failure",
    "Communication failure",
    "Ballast issue",
    "Switch failure",
]
VALID_SEVERITIES = ["Low", "Medium", "High", "Critical"]
VALID_PRIORITIES = ["Low", "Medium", "High", "Critical", "Emergency"]

# Workflow status escalation thresholds
EMERGENCY_STATUSES = {"Escalated"}
CRITICAL_STATUSES = {"Interrupted", "Reopened"}
