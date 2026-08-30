"""
classifier.py
RailMaintain — AI/ML Complaint Classification

Purpose
-------
Trained scikit-learn model (TF-IDF + Logistic Regression) for fault
classification. A keyword-based fallback is used when the model is
unavailable or confidence is low.

The AI never authorizes a railway block or a final safety decision.
Low-confidence or emergency complaints are always routed to human review
via emergency_rules.py.

Model loading:
  1. Try to load the trained .joblib pipeline.
  2. Use model.predict() + predict_proba() for classification.
  3. On any failure, fall back to keyword rules.
"""

from typing import Dict, List, Optional

from emergency_rules import evaluate_emergency
from app.maintenance_intelligence.config import CONFIDENCE_THRESHOLD

# Attempt to load the trained model at module import time.
_trained_model = None
_label_maps = None
try:
    from app.maintenance_intelligence.inference.model_loader import (
        load_model,
        load_label_maps,
    )
    _trained_model = load_model()
    _label_maps = load_label_maps()
except Exception:
    # Model unavailable — keyword fallback will be used.
    _trained_model = None



# ---------------------------------------------------------------------------
# 1. Label sets (must match 03 Keywords & Data Dictionary exactly)
# ---------------------------------------------------------------------------
ASSET_TYPES = ["Track", "Signal", "Electrical Equipment", "Point Machine", "Station Machinery"]
DEPARTMENTS = ["Track", "Signalling", "Electrical"]
SEVERITIES = ["Low", "Medium", "High", "Critical"]

# department each asset type reports to
ASSET_TYPE_TO_DEPARTMENT = {
    "Track": "Track",
    "Signal": "Signalling",
    "Electrical Equipment": "Electrical",
    "Point Machine": "Signalling",
    "Station Machinery": "Electrical",
}


# ---------------------------------------------------------------------------
# 2. Keyword rules — asset type detection
# ---------------------------------------------------------------------------
# Ordered by specificity where it matters (checked as separate independent
# rules; first strong match wins based on match count in _score_asset_type).
ASSET_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "Signal": [
        "signal", "signalling", "signal light", "flickering", "aspect",
        "signal failure", "signal malfunction",
    ],
    "Track": [
        "track", "rail", "joint", "sleeper", "ballast", "gauge",
        "broken rail", "track obstruction", "crack",
    ],
    "Electrical Equipment": [
        "electrical", "electricity", "spark", "sparks", "sparking",
        "wire", "wiring", "ohe", "overhead", "power", "short circuit",
        "electrical danger",
    ],
    "Point Machine": [
        "point machine", "points", "point", "switch", "turnout",
    ],
    "Station Machinery": [
        "escalator", "elevator", "lift", "station machinery", "ac unit",
        "water cooler", "platform equipment", "announcement system",
    ],
}


# ---------------------------------------------------------------------------
# 3. Keyword rules — fault category detection (per asset type)
# ---------------------------------------------------------------------------
FAULT_CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Signal malfunction": ["flickering", "not working", "signal failure", "signal down", "dead signal"],
    "Track damage": ["damaged", "crack", "broken", "worn", "misaligned"],
    "Electrical fault": ["spark", "sparking", "short circuit", "power failure", "no power"],
    "Point machine failure": ["not operating", "stuck", "jammed", "not moving"],
    "Machinery breakdown": ["not working", "broken down", "malfunction", "out of order"],
    "Obstruction": ["obstruction", "blocked", "debris", "object on track"],
}


# ---------------------------------------------------------------------------
# 4. Severity keyword rules
# ---------------------------------------------------------------------------
SEVERITY_KEYWORDS: Dict[str, List[str]] = {
    "Critical": [
        "urgent", "immediately", "danger", "dangerous", "unsafe", "critical",
        "derailment", "collision", "fire", "broken rail", "electrical danger",
        "signal failure", "track obstruction",
    ],
    "High": [
        "trains are slowing", "delay", "delayed", "major", "significant",
        "not operating", "not working",
    ],
    "Medium": ["flickering", "intermittent", "minor damage", "worn"],
    "Low": ["cosmetic", "minor", "routine", "small issue"],
}

SEVERITY_RANK = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}


# ---------------------------------------------------------------------------
# 5. Suggested action per severity
# ---------------------------------------------------------------------------
SUGGESTED_ACTION_BY_SEVERITY = {
    "Critical": "Immediate inspection",
    "High": "Priority inspection within 24 hours",
    "Medium": "Schedule inspection within a few days",
    "Low": "Add to routine maintenance queue",
}


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _score_keywords(text: str, keyword_map: Dict[str, List[str]]) -> Dict[str, int]:
    """
    Count keyword hits per label. Returns {label: hit_count} for labels
    with at least one hit.
    """
    scores: Dict[str, int] = {}
    for label, keywords in keyword_map.items():
        count = sum(1 for kw in keywords if kw in text)
        if count > 0:
            scores[label] = count
    return scores


def predict_asset_type(text: str) -> Optional[str]:
    scores = _score_keywords(text, ASSET_TYPE_KEYWORDS)
    if not scores:
        return None
    # highest hit count wins; ties broken by keyword-list order
    return max(scores, key=lambda label: (scores[label], -list(ASSET_TYPE_KEYWORDS).index(label)))


def predict_department(asset_type: Optional[str]) -> Optional[str]:
    if asset_type is None:
        return None
    return ASSET_TYPE_TO_DEPARTMENT.get(asset_type)


def predict_fault_category(text: str) -> Optional[str]:
    scores = _score_keywords(text, FAULT_CATEGORY_KEYWORDS)
    if not scores:
        return None
    return max(scores, key=lambda label: scores[label])


def predict_severity(text: str) -> str:
    """
    Defaults to 'Medium' if nothing matches, since an unclassified fault
    should not be silently treated as Low priority.
    """
    scores = _score_keywords(text, SEVERITY_KEYWORDS)
    if not scores:
        return "Medium"
    # pick the highest-severity label among matches, not just the most hits,
    # since a single critical word (e.g. "fire") should outrank several
    # low-severity words.
    return max(scores.keys(), key=lambda label: SEVERITY_RANK[label])


def calculate_confidence(
    asset_type: Optional[str],
    fault_category: Optional[str],
    severity_matched: bool,
    is_emergency: bool,
) -> float:
    """
    Simple, explainable confidence score for the keyword-rule baseline.
    Not a statistical probability — a transparent heuristic:
        +0.4 asset type matched
        +0.3 fault category matched
        +0.2 severity keyword matched (vs. default fallback)
        +0.1 base
    Emergency-flagged complaints are capped at 0.6 confidence, since an
    emergency keyword hit means the situation is too important to let a
    keyword rule be fully confident on its own — it always needs a human.
    """
    score = 0.1
    if asset_type is not None:
        score += 0.4
    if fault_category is not None:
        score += 0.3
    if severity_matched:
        score += 0.2

    score = min(score, 1.0)
    if is_emergency:
        score = min(score, 0.6)
    return round(score, 2)


def _classify_with_model(features_df, complaint_id: str, description: str) -> Optional[Dict]:
    """Attempt classification using the trained scikit-learn model.

    Returns None if the model is unavailable or prediction fails.
    """
    if _trained_model is None:
        return None

    try:
        import pandas as pd

        # The trained pipeline expects the same feature columns used in training.
        prediction = _trained_model.predict(features_df)

        # prediction is an array of target values; decode via label maps.
        if _label_maps and len(prediction.shape) == 2:
            decoded = {}
            for idx, target in enumerate(["department", "fault_category", "severity", "base_priority"]):
                inv_map = {v: k for k, v in _label_maps.get(target, {}).items()}
                decoded[target] = inv_map.get(int(prediction[0][idx]), prediction[0][idx])
        else:
            # Single-output model — best effort decode.
            decoded = {
                "department": str(prediction[0]),
                "fault_category": "Unknown",
                "severity": "Medium",
                "base_priority": "Medium",
            }

        # Model probability for confidence.
        try:
            proba = _trained_model.predict_proba(features_df)
            confidence = float(max(max(p) for p in proba))
        except Exception:
            confidence = None

        return {"prediction": decoded, "confidence": confidence}
    except Exception:
        return None


def classify_complaint(complaint: Dict) -> Dict:
    """
    Main entry point for the backend API.

    Classification strategy:
      1. Emergency screening always runs first.
      2. Try the trained scikit-learn model if available.
      3. Fall back to keyword rules if the model is unavailable or
         returns low confidence.

    Parameters
    ----------
    complaint : dict, e.g.
        {
            "complaint_id": "C-201",
            "description": "Signal near S-02 is flickering and trains are slowing down.",
            "asset_id": "SIG-S02-04",
            "asset_type": "Signal",       # optional, provided by reporter
            "section_id": "S-02"
        }

    Returns
    -------
    dict matching the ai_classification contract:
        complaint_id, asset_type, department, fault_category, base_priority,
        confidence, human_review_required, reason, suggested_action
    """
    complaint_id = complaint.get("complaint_id", "UNKNOWN")
    description = complaint.get("description", "")
    text = _normalize(description)

    # 1. Emergency / exception screening always runs first
    emergency_result = evaluate_emergency(complaint_id, description)

    # 2. Keyword-rule predictions (used as fallback and for emergency overrides)
    predicted_asset_type = predict_asset_type(text)
    reported_asset_type = complaint.get("asset_type")
    asset_type = reported_asset_type if reported_asset_type in ASSET_TYPES else predicted_asset_type

    department = predict_department(asset_type)
    fault_category = predict_fault_category(text)
    severity = predict_severity(text)
    severity_matched = any(kw in text for kws in SEVERITY_KEYWORDS.values() for kw in kws)

    # Emergency keyword hits always force at least Critical severity
    if emergency_result["is_emergency_flagged"]:
        severity = "Critical"

    # 3. Try the trained model first, fall back to keyword rules
    model_result = None
    using_model = False
    try:
        from app.maintenance_intelligence.inference.feature_builder import build_features
        from app.maintenance_intelligence.io_schemas import ComplaintInput

        complaint_input = ComplaintInput(
            complaint_text=description,
            asset_type=asset_type or "Unknown",
            asset_criticality=complaint.get("asset_criticality", "Non-Critical"),
            current_status=complaint.get("current_status", "New"),
            days_overdue=complaint.get("days_overdue", 0),
            failure_count_30_days=complaint.get("failure_count_30_days", 0),
            safety_risk_level=complaint.get("safety_risk_level", "Low"),
            service_impact_level=complaint.get("service_impact_level", "Minor"),
        )
        features_df = build_features(complaint_input)
        model_result = _classify_with_model(features_df, complaint_id, description)
    except Exception:
        model_result = None

    if model_result is not None and model_result["confidence"] is not None:
        # Model is available and produced a prediction
        using_model = True
        pred = model_result["prediction"]
        model_asset_type = pred.get("department", department)
        # Prefer reporter-provided asset_type, then model, then keyword
        if asset_type is None:
            asset_type = pred.get("asset_type")
        if department is None:
            department = pred.get("department")
        if fault_category is None or fault_category == "Unknown":
            fault_category = pred.get("fault_category", fault_category)
        severity = pred.get("severity", severity)
        confidence = model_result["confidence"]

        if emergency_result["is_emergency_flagged"]:
            severity = "Critical"
    else:
        # Keyword fallback
        confidence = calculate_confidence(
            asset_type=asset_type,
            fault_category=fault_category,
            severity_matched=severity_matched,
            is_emergency=emergency_result["is_emergency_flagged"],
        )

    # 4. Human review trigger: emergency OR low confidence OR critical severity
    #    OR missing asset_type/department (can't safely auto-route without them)
    low_confidence = confidence < CONFIDENCE_THRESHOLD
    missing_core_fields = asset_type is None or department is None
    human_review_required = (
        emergency_result["human_review_required"]
        or low_confidence
        or severity == "Critical"
        or missing_core_fields
    )

    # 5. Build explanation string
    reason_parts = []
    if emergency_result["is_emergency_flagged"]:
        reason_parts.append(emergency_result["reason"])
    if emergency_result["exception_types"]:
        reason_parts.append(f"Exception type(s) detected: {', '.join(emergency_result['exception_types'])}.")
    if missing_core_fields:
        reason_parts.append("Asset type or department could not be confidently determined.")
    if low_confidence and not emergency_result["is_emergency_flagged"]:
        reason_parts.append(f"Confidence ({confidence:.2f}) is below threshold ({CONFIDENCE_THRESHOLD}) — human review recommended.")
    if using_model:
        reason_parts.append(f"Classified via trained model with confidence {confidence:.2f}.")
    elif not reason_parts:
        reason_parts.append(f"Classified via keyword rules with confidence {confidence:.2f}.")

    reason = " ".join(reason_parts)

    suggested_action = SUGGESTED_ACTION_BY_SEVERITY.get(severity, "Schedule inspection")

    return {
        "complaint_id": complaint_id,
        "asset_type": asset_type,
        "department": department,
        "fault_category": fault_category,
        "base_priority": severity,
        "confidence": confidence,
        "human_review_required": human_review_required,
        "reason": reason,
        "suggested_action": suggested_action,
    }


# ---------------------------------------------------------------------------
# Quick manual smoke test (run: python classifier.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json

    samples = [
        {"complaint_id": "C-201", "description": "Signal near S-02 is flickering and trains are slowing down.", "asset_id": "SIG-S02-04", "section_id": "S-02"},
        {"complaint_id": "C-202", "description": "Track joint is damaged near the station.", "asset_id": "TRK-S01-02", "section_id": "S-01"},
        {"complaint_id": "C-203", "description": "Electrical equipment is producing sparks.", "asset_id": "ELE-S03-01", "section_id": "S-03"},
        {"complaint_id": "C-204", "description": "Point machine is not operating.", "asset_id": "PM-S02-01", "section_id": "S-02"},
        {"complaint_id": "C-205", "description": "There has been a derailment near platform 3, urgent help needed.", "asset_id": "TRK-S04-01", "section_id": "S-04"},
        {"complaint_id": "C-206", "description": "Escalator at the station is out of order.", "asset_id": "STM-S01-01", "section_id": "S-01"},
        {"complaint_id": "C-207", "description": "Something seems off near the yard.", "asset_id": "UNK-S02-01", "section_id": "S-02"},
    ]

    for sample in samples:
        result = classify_complaint(sample)
        print(json.dumps(result, indent=2))
        print("-" * 60)
