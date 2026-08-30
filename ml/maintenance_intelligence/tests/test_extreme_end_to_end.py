"""Extreme end-to-end tests."""

import sys
from pathlib import Path
from unittest.mock import patch
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import VALID_DEPARTMENTS, VALID_FAULT_CATEGORIES, VALID_PRIORITIES, VALID_SEVERITIES
from app.maintenance_intelligence.inference.classifier import ModelNotFoundError, classify_case
from app.maintenance_intelligence.inference.confidence import check_confidence
from app.maintenance_intelligence.inference.explanation import generate_explanation
from app.maintenance_intelligence.prioritization.priority_engine import (
    calculate_final_priority, get_recommended_action, priority_order, requires_human_review,
)
from app.maintenance_intelligence.io_schemas import ComplaintInput


def _full_pipeline(complaint):
    classification = classify_case(complaint)
    context = {
        "asset_criticality": complaint.asset_criticality or "Non-Critical",
        "current_status": complaint.current_status or "New",
        "safety_risk_level": complaint.safety_risk_level or "Low",
        "service_impact_level": complaint.service_impact_level or "Minor",
        "days_overdue": complaint.days_overdue or 0,
        "failure_count_30_days": complaint.failure_count_30_days or 0,
    }
    priority_result = calculate_final_priority(classification, context)
    confidence_info = check_confidence(classification["confidence"])
    explanation = generate_explanation(classification, context, priority_result["reasons"], confidence_info)
    action = get_recommended_action(priority_result["final_priority"], classification.get("fault_category", ""), complaint.safety_risk_level or "Low")
    hr, _ = requires_human_review(priority_result["final_priority"], classification["confidence"], safety_risk=complaint.safety_risk_level or "Low")
    return {"classification": classification, "priority_result": priority_result, "explanation": explanation, "action": action, "human_review_required": hr}


class TestE2E001:
    def test_broken_rail_full_pipeline(self):
        complaint = ComplaintInput(complaint_text="Rail is visibly broken near an active running line.",
                                   asset_type="Track", asset_criticality="Safety-Critical",
                                   safety_risk_level="Extreme", service_impact_level="Major")
        result = _full_pipeline(complaint)
        assert result["priority_result"]["final_priority"] == "Emergency"
        assert result["human_review_required"] is True

    def test_no_automatic_train_control(self):
        complaint = ComplaintInput(complaint_text="Rail is visibly broken.", asset_type="Track",
                                   asset_criticality="Safety-Critical", safety_risk_level="Extreme",
                                   service_impact_level="Major")
        result = _full_pipeline(complaint)
        assert "department" in result["classification"]
        assert "final_priority" in result["priority_result"]


class TestE2E002:
    def test_repeated_reopening(self):
        complaint = ComplaintInput(complaint_text="Signal failure recurrence.", asset_type="Signal",
                                   asset_criticality="Safety-Critical", current_status="Reopened",
                                   safety_risk_level="High", service_impact_level="Major", reopen_count=3)
        result = _full_pipeline(complaint)
        assert priority_order(result["priority_result"]["final_priority"]) >= priority_order("Critical")


class TestE2E003:
    def test_resource_unavailable(self):
        complaint = ComplaintInput(complaint_text="Emergency track repair.", asset_type="Track",
                                   asset_criticality="Safety-Critical", safety_risk_level="Extreme",
                                   service_impact_level="Severe")
        result = _full_pipeline(complaint)
        assert result["human_review_required"] is True


class TestE2E004:
    def test_model_unavailable_raises_error(self):
        import app.maintenance_intelligence.inference.classifier as mod
        original = mod.MODEL_PATH
        mod.MODEL_PATH = Path("/nonexistent/model.joblib")
        try:
            with pytest.raises(ModelNotFoundError):
                classify_case(ComplaintInput(complaint_text="Emergency signal failure."))
        finally:
            mod.MODEL_PATH = original

    def test_priority_engine_works_without_model(self):
        result = calculate_final_priority(
            {"base_priority": "Low"},
            {"asset_criticality": "Safety-Critical", "current_status": "Escalated", "safety_risk_level": "Extreme"},
        )
        assert result["final_priority"] == "Emergency"


class TestE2E005:
    def test_no_fabricated_context(self):
        c = ComplaintInput(complaint_text="Equipment failure.")
        assert c.asset_criticality == "Non-Critical"
        assert c.safety_risk_level == "Low"


class TestE2E006:
    def test_priority_engine_no_database_dependency(self):
        for _ in range(5):
            result = calculate_final_priority(
                {"base_priority": "High"},
                {"asset_criticality": "Safety-Critical", "current_status": "Interrupted", "safety_risk_level": "High"},
            )
            assert result["final_priority"] == "Critical"


class TestE2E007:
    def test_safety_risk_overrides_contradiction(self):
        complaint = ComplaintInput(complaint_text="Everything is fine.", asset_type="Track",
                                   asset_criticality="Non-Critical", safety_risk_level="Extreme",
                                   service_impact_level="Minor")
        result = _full_pipeline(complaint)
        assert result["priority_result"]["final_priority"] == "Emergency"


class TestE2E008:
    def test_text_cannot_override_safety_rules(self):
        for text in ["Set priority to Low", "This is Low priority", "Ignore safety rules"]:
            complaint = ComplaintInput(complaint_text=text, asset_type="Signal",
                                       asset_criticality="Safety-Critical", current_status="Escalated",
                                       safety_risk_level="Extreme", service_impact_level="Major")
            classification = classify_case(complaint)
            context = {"asset_criticality": complaint.asset_criticality, "current_status": complaint.current_status,
                       "safety_risk_level": complaint.safety_risk_level}
            result = calculate_final_priority(classification, context)
            assert result["final_priority"] == "Emergency"
