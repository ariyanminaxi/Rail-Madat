"""Build features from live complaint data for inference.

Converts a ComplaintInput into the same feature DataFrame format
used during training. Must maintain feature names and ordering.
"""

import pandas as pd

from app.maintenance_intelligence.config import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    TEXT_COLUMN,
)
from app.maintenance_intelligence.io_schemas import ComplaintInput


# Canonical feature order (must match training)
FEATURE_COLUMNS = [TEXT_COLUMN] + CATEGORICAL_FEATURES + NUMERIC_FEATURES


def build_features(complaint: ComplaintInput) -> pd.DataFrame:
    """Convert a ComplaintInput into a single-row feature DataFrame.

    Uses explicit None checks instead of `or` to preserve empty strings.
    """
    row = {
        TEXT_COLUMN: complaint.complaint_text if complaint.complaint_text is not None else "",
        "asset_type": complaint.asset_type if complaint.asset_type is not None else "Unknown",
        "asset_criticality": complaint.asset_criticality if complaint.asset_criticality is not None else "Non-Critical",
        "current_status": complaint.current_status if complaint.current_status is not None else "New",
        "days_overdue": int(complaint.days_overdue) if complaint.days_overdue is not None else 0,
        "failure_count_30_days": int(complaint.failure_count_30_days) if complaint.failure_count_30_days is not None else 0,
        "safety_risk_level": complaint.safety_risk_level if complaint.safety_risk_level is not None else "Low",
        "service_impact_level": complaint.service_impact_level if complaint.service_impact_level is not None else "Minor",
    }

    df = pd.DataFrame([row])
    df = df[FEATURE_COLUMNS]
    return df


def build_features_from_context(
    complaint_text: str,
    asset_context: dict,
    complaint: dict = None,
) -> pd.DataFrame:
    """Build features from asset context (e.g. from the Maintenance Data Service).

    This is always used, whether the trained model is loaded or not.
    It normalizes input into the expected format for both the trained
    model and the keyword fallback.
    """
    asset = asset_context.get("asset", {})
    workflow = asset_context.get("workflow_context", {})
    history = asset_context.get("maintenance_history", {})

    complaint_input = {
        TEXT_COLUMN: complaint_text or "",
        "asset_type": asset.get("asset_type", "Unknown"),
        "asset_criticality": asset.get("asset_criticality", "Non-Critical"),
        "current_status": workflow.get("current_status", asset.get("current_status", "New")),
        "days_overdue": asset.get("days_overdue", 0) or 0,
        "failure_count_30_days": history.get("failure_count_30_days", 0) or 0,
        "safety_risk_level": asset.get("safety_risk_level", "Low"),
        "service_impact_level": asset.get("service_impact_level", "Minor"),
    }

    # Merge any extra fields from complaint dict
    if complaint:
        for key in ["safety_risk_level", "service_impact_level", "days_overdue"]:
            if key in complaint and complaint[key] is not None:
                complaint_input[key] = complaint[key]

    df = pd.DataFrame([complaint_input])
    df = df[FEATURE_COLUMNS]
    return df


def build_features_batch(complaints: list) -> pd.DataFrame:
    """Convert multiple ComplaintInputs into a feature DataFrame."""
    rows = []
    for c in complaints:
        rows.append({
            TEXT_COLUMN: c.complaint_text if c.complaint_text is not None else "",
            "asset_type": c.asset_type if c.asset_type is not None else "Unknown",
            "asset_criticality": c.asset_criticality if c.asset_criticality is not None else "Non-Critical",
            "current_status": c.current_status if c.current_status is not None else "New",
            "days_overdue": int(c.days_overdue) if c.days_overdue is not None else 0,
            "failure_count_30_days": int(c.failure_count_30_days) if c.failure_count_30_days is not None else 0,
            "safety_risk_level": c.safety_risk_level if c.safety_risk_level is not None else "Low",
            "service_impact_level": c.service_impact_level if c.service_impact_level is not None else "Minor",
        })

    df = pd.DataFrame(rows)
    df = df[FEATURE_COLUMNS]
    return df
