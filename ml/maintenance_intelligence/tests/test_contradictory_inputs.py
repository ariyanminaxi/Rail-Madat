"""Contradictory input tests."""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.inference.classifier import classify_case
from app.maintenance_intelligence.prioritization.priority_engine import calculate_final_priority, priority_order
from app.maintenance_intelligence.io_schemas import ComplaintInput


class TestTCConflict001:
    def test_extreme_risk_overrides_text(self):
        complaint = ComplaintInput(complaint_text="No visible fault and everything is operating normally.",
                                   asset_type="Signal", asset_criticality="Safety-Critical",
                                   current_status="Escalated", safety_risk_level="Extreme",
                                   service_impact_level="Minor")
        classification = classify_case(complaint)
        context = {"asset_criticality": complaint.asset_criticality, "current_status": complaint.current_status,
                   "safety_risk_level": complaint.safety_risk_level}
        result = calculate_final_priority(classification, context)
        assert result["final_priority"] == "Emergency"

    def test_not_silently_low_priority(self):
        complaint = ComplaintInput(complaint_text="No visible fault.", asset_type="Signal",
                                   asset_criticality="Safety-Critical", current_status="Escalated",
                                   safety_risk_level="Extreme", service_impact_level="Minor")
        classification = classify_case(complaint)
        context = {"asset_criticality": complaint.asset_criticality, "current_status": complaint.current_status,
                   "safety_risk_level": complaint.safety_risk_level}
        result = calculate_final_priority(classification, context)
        assert result["final_priority"] not in ("Low", "Medium")


class TestTCConflict002:
    def test_extreme_safety_risk_takes_precedence(self):
        complaint = ComplaintInput(complaint_text="Critical track obstruction.", asset_type="Track",
                                   asset_criticality="Non-Critical", current_status="Completed",
                                   safety_risk_level="Extreme", service_impact_level="Major")
        classification = classify_case(complaint)
        context = {"asset_criticality": complaint.asset_criticality, "current_status": complaint.current_status,
                   "safety_risk_level": complaint.safety_risk_level}
        result = calculate_final_priority(classification, context)
        assert result["final_priority"] == "Emergency"


class TestTCConflict003:
    def test_interrupted_status_escalates(self):
        complaint = ComplaintInput(complaint_text="Work completed successfully.", asset_type="Signal",
                                   asset_criticality="Safety-Critical", current_status="Interrupted",
                                   safety_risk_level="High", service_impact_level="Major")
        classification = classify_case(complaint)
        context = {"asset_criticality": complaint.asset_criticality, "current_status": complaint.current_status,
                   "safety_risk_level": complaint.safety_risk_level}
        result = calculate_final_priority(classification, context)
        assert priority_order(result["final_priority"]) >= priority_order("High")


class TestTCConflict004:
    def test_structured_fields_take_precedence(self):
        complaint = ComplaintInput(complaint_text="No operational impact.", asset_type="Track",
                                   asset_criticality="Safety-Critical", safety_risk_level="Extreme",
                                   service_impact_level="Major")
        classification = classify_case(complaint)
        context = {"asset_criticality": complaint.asset_criticality, "current_status": complaint.current_status,
                   "safety_risk_level": complaint.safety_risk_level}
        result = calculate_final_priority(classification, context)
        assert result["final_priority"] == "Emergency"
