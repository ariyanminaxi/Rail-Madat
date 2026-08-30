"""Contradictory evidence tests.

Tests TC-CONFLICT-001 through TC-CONFLICT-003: the system must handle
cases where complaint text contradicts structured fields, or where
different structured fields contradict each other.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import VALID_PRIORITIES
from app.maintenance_intelligence.inference.classifier import classify_case
from app.maintenance_intelligence.inference.confidence import check_confidence
from app.maintenance_intelligence.inference.explanation import generate_explanation
from app.maintenance_intelligence.prioritization.priority_engine import (
    calculate_final_priority,
    priority_order,
    requires_human_review,
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
    explanation = generate_explanation(
        classification, context, priority_result["reasons"], confidence_info
    )
    hr_required, _ = requires_human_review(
        priority_result["final_priority"],
        classification["confidence"],
        safety_risk=complaint.safety_risk_level or "Low",
    )
    return {
        "classification": classification,
        "priority_result": priority_result,
        "explanation": explanation,
        "human_review_required": hr_required,
    }


# ===================================================================
# TC-CONFLICT-001: No visible fault + equipment failed
# ===================================================================

class TestTCConflict001NoVisibleFaultButFailed:
    """Text says no visible fault, but equipment failed during operation."""

    @pytest.fixture(scope="class")
    def result(self):
        complaint = ComplaintInput(
            complaint_text="No visible fault was found, but the equipment failed during operation.",
            asset_type="Signal",
            asset_criticality="Safety-Critical",
            current_status="Under Review",
            safety_risk_level="High",
            service_impact_level="Major",
        )
        return _full_pipeline(complaint)

    def test_human_review_required(self, result):
        assert result["human_review_required"] is True

    def test_explanation_mentions_conflicting_evidence(self, result):
        combined = " ".join(result["explanation"]).lower()
        assert (
            "conflict" in combined
            or "evidence" in combined
            or "review" in combined
            or "safety-critical" in combined
        )

    def test_priority_not_reduced_because_no_visible_fault(self, result):
        """Priority must NOT be reduced solely because no visible fault found."""
        fp = result["priority_result"]["final_priority"]
        assert priority_order(fp) >= priority_order("High")

    def test_structured_fields_dominance(self):
        """Direct priority engine: High safety risk → not Low."""
        result = calculate_final_priority(
            {"base_priority": "Medium"},
            {
                "asset_criticality": "Safety-Critical",
                "current_status": "Under Review",
                "safety_risk_level": "High",
            },
        )
        assert priority_order(result["final_priority"]) >= priority_order("High")


# ===================================================================
# TC-CONFLICT-002: No impact claim vs 45-minute delay
# ===================================================================

class TestTCConflict002NoImpactVsDelayRecord:
    """Reporter says no impact, but train delay is 45 minutes."""

    @pytest.fixture(scope="class")
    def result(self):
        complaint = ComplaintInput(
            complaint_text="The reporter says there is no operational impact, but train delay is recorded as 45 minutes.",
            asset_type="Track",
            asset_criticality="High",
            current_status="New",
            safety_risk_level="High",
            service_impact_level="Major",
        )
        return _full_pipeline(complaint)

    def test_structured_evidence_considered(self, result):
        """Structured service_impact_level should override free-text claim."""
        combined = " ".join(result["explanation"]).lower()
        assert "major" in combined or "impact" in combined or "high" in combined

    def test_contradiction_reported_or_review_required(self, result):
        assert result["human_review_required"] is True

    def test_system_does_not_choose_lower_risk(self, result):
        """Must not silently downgrade to Low/Medium when evidence is Major."""
        fp = result["priority_result"]["final_priority"]
        assert priority_order(fp) >= priority_order("High")


# ===================================================================
# TC-CONFLICT-003: Non-critical label vs safety restriction
# ===================================================================

class TestTCConflict003NonCriticalVsSafetyRestriction:
    """Asset labelled non-critical, but section is under safety restriction."""

    @pytest.fixture(scope="class")
    def result(self):
        complaint = ComplaintInput(
            complaint_text="Asset is labelled non-critical, but the section is currently under a safety restriction.",
            asset_type="Track",
            asset_criticality="Medium",
            current_status="New",
            safety_risk_level="High",
            service_impact_level="Minor",
        )
        return _full_pipeline(complaint)

    def test_safety_context_not_ignored(self, result):
        """High safety risk should not be ignored just because asset is Medium."""
        fp = result["priority_result"]["final_priority"]
        assert priority_order(fp) >= priority_order("High")

    def test_human_review_required(self, result):
        assert result["human_review_required"] is True

    def test_final_priority_not_low(self, result):
        assert result["priority_result"]["final_priority"] != "Low"

    def test_priority_engine_safety_overrides_medium_criticality(self):
        """Direct test: High safety risk → at least High, regardless of Medium criticality."""
        result = calculate_final_priority(
            {"base_priority": "Low"},
            {
                "asset_criticality": "Medium",
                "current_status": "New",
                "safety_risk_level": "High",
            },
        )
        assert priority_order(result["final_priority"]) >= priority_order("High")
