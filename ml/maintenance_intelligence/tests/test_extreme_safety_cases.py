"""Extreme safety case tests."""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import VALID_PRIORITIES
from app.maintenance_intelligence.inference.classifier import classify_case
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
    hr_required, _ = requires_human_review(priority_result["final_priority"], classification["confidence"], safety_risk=complaint.safety_risk_level or "Low")
    return {"classification": classification, "priority_result": priority_result, "explanation": explanation, "action": action, "human_review_required": hr_required}


class TestTCExtreme001:
    def test_final_priority_emergency(self):
        complaint = ComplaintInput(complaint_text="Rail is visibly broken near an active running line.",
                                   asset_type="Track", asset_criticality="Safety-Critical",
                                   safety_risk_level="Extreme", service_impact_level="Major")
        result = _full_pipeline(complaint)
        assert result["priority_result"]["final_priority"] == "Emergency"

    def test_human_review_required(self):
        complaint = ComplaintInput(complaint_text="Rail is visibly broken near an active running line.",
                                   asset_type="Track", asset_criticality="Safety-Critical",
                                   safety_risk_level="Extreme", service_impact_level="Major")
        result = _full_pipeline(complaint)
        assert result["human_review_required"] is True

    def test_explanation_mentions_extreme(self):
        complaint = ComplaintInput(complaint_text="Rail is visibly broken near an active running line.",
                                   asset_type="Track", asset_criticality="Safety-Critical",
                                   safety_risk_level="Extreme", service_impact_level="Major")
        result = _full_pipeline(complaint)
        combined = " ".join(result["explanation"]).lower()
        assert "extreme" in combined


class TestTCExtreme002:
    def test_high_confidence_does_not_bypass_review(self):
        hr, reasons = requires_human_review("Emergency", confidence=0.99, safety_risk="Extreme")
        assert hr is True

    def test_priority_engine_overrides_high_confidence(self):
        result = calculate_final_priority(
            {"base_priority": "Low"},
            {"asset_criticality": "Non-Critical", "current_status": "New", "safety_risk_level": "Extreme"},
        )
        assert result["final_priority"] == "Emergency"


class TestTCExtreme003:
    @pytest.mark.parametrize("base", ["Low", "Medium", "High"])
    def test_interrupted_escalates(self, base):
        result = calculate_final_priority(
            {"base_priority": base},
            {"asset_criticality": "Safety-Critical", "current_status": "Interrupted", "safety_risk_level": "High"},
        )
        assert priority_order(result["final_priority"]) >= priority_order("Critical")


class TestTCExtreme004:
    def test_reopened_safety_critical(self):
        result = calculate_final_priority(
            {"base_priority": "High"},
            {"asset_criticality": "Safety-Critical", "current_status": "Reopened", "safety_risk_level": "High"},
        )
        assert priority_order(result["final_priority"]) >= priority_order("Critical")


class TestTCExtreme005:
    def test_extreme_always_wins(self):
        for base in ["Low", "Medium", "High", "Critical"]:
            result = calculate_final_priority(
                {"base_priority": base},
                {"asset_criticality": "Safety-Critical", "current_status": "Reopened",
                 "safety_risk_level": "Extreme", "service_impact_level": "Major"},
            )
            assert result["final_priority"] == "Emergency"
