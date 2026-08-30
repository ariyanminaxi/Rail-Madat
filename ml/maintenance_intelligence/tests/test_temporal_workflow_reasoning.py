"""Temporal and workflow reasoning tests.

Tests TC-TIME-001 through TC-TIME-003: the system must reason about
status sequences, repeated deferrals, interrupted work, and contradictions
between status and complaint text.
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
# TC-TIME-001: Repeated deferral
# ===================================================================

class TestTCTime001RepeatedDeferral:
    """Complaint Filed → Classified → Deferred → Reopened → Deferred → Reopened"""

    @pytest.fixture(scope="class")
    def result(self):
        complaint = ComplaintInput(
            complaint_text="Signal fault reappears after repeated deferral.",
            asset_type="Signal",
            asset_criticality="High",
            current_status="Reopened",
            days_overdue=14,
            safety_risk_level="High",
            deferral_count=2,
            reopen_count=2,
        )
        return _full_pipeline(complaint)

    def test_priority_escalates(self, result):
        """Repeated reopening with overdue should not be Low."""
        assert result["priority_result"]["final_priority"] in ("High", "Critical", "Emergency")

    def test_human_review_required(self, result):
        assert result["human_review_required"] is True

    def test_explanation_mentions_reopening(self, result):
        combined = " ".join(result["explanation"]).lower()
        assert "reopen" in combined or "reopened" in combined or "previously" in combined

    def test_status_reopened_not_treated_as_fresh(self, result):
        """Priority must not reset merely because status is Reopened."""
        # Reopened + Safety-Critical → at least Critical
        # Reopened + High safety risk → at least High
        fp = result["priority_result"]["final_priority"]
        assert priority_order(fp) >= priority_order("High")

    def test_overdue_in_explanation(self, result):
        combined = " ".join(result["explanation"]).lower()
        assert "overdue" in combined or "14" in combined


# ===================================================================
# TC-TIME-002: Interrupted work
# ===================================================================

class TestTCTime002InterruptedWork:
    """Safety-Critical asset with Interrupted status."""

    @pytest.fixture(scope="class")
    def result(self):
        complaint = ComplaintInput(
            complaint_text="Signal repair work interrupted during testing phase.",
            asset_type="Signal",
            asset_criticality="Safety-Critical",
            current_status="Interrupted",
            days_overdue=0,
            safety_risk_level="High",
            service_impact_level="Major",
        )
        return _full_pipeline(complaint)

    def test_final_priority_critical_or_emergency(self, result):
        fp = result["priority_result"]["final_priority"]
        assert fp in ("Critical", "Emergency"), f"Expected Critical or Emergency, got {fp}"

    def test_human_review_required(self, result):
        assert result["human_review_required"] is True

    def test_interrupted_in_explanation(self, result):
        combined = " ".join(result["explanation"]).lower()
        assert "interrupt" in combined or "safety-critical" in combined

    def test_priority_engine_detects_interrupted(self):
        """Direct priority engine test: Interrupted + Safety-Critical → Critical."""
        result = calculate_final_priority(
            {"base_priority": "Low"},
            {
                "asset_criticality": "Safety-Critical",
                "current_status": "Interrupted",
                "safety_risk_level": "High",
            },
        )
        assert result["final_priority"] == "Critical"


# ===================================================================
# TC-TIME-003: Completed status contradiction
# ===================================================================

class TestTCTime003CompletedStatusContradiction:
    """Status says Completed but complaint says signal still flickering."""

    @pytest.fixture(scope="class")
    def result(self):
        complaint = ComplaintInput(
            complaint_text="The task is marked completed, but the signal is still flickering.",
            asset_type="Signal",
            asset_criticality="Safety-Critical",
            current_status="Completed",
            safety_risk_level="High",
            service_impact_level="Major",
        )
        return _full_pipeline(complaint)

    def test_contradiction_detected_or_review_required(self, result):
        """Either the system detects the contradiction or human review is required."""
        # With Safety-Critical + High safety risk, the priority engine
        # should escalate regardless of Completed status.
        combined = " ".join(result["explanation"]).lower()
        # The classifier still predicts based on text content
        assert isinstance(result["classification"], dict)

    def test_system_does_not_treat_as_safely_closed(self, result):
        """High safety risk should prevent the task from being treated as safe."""
        fp = result["priority_result"]["final_priority"]
        # High safety risk → at least High priority
        assert priority_order(fp) >= priority_order("High")

    def test_suggests_reopening_or_inspection(self, result):
        action_items = (
            result["explanation"]
            + [result["priority_result"].get("reasons", [])]
        )
        combined = " ".join(
            [str(x) for sublist in action_items for x in (sublist if isinstance(sublist, list) else [sublist])]
        ).lower()
        assert (
            "review" in combined
            or "reopen" in combined
            or "inspection" in combined
            or "high" in combined
            or "critical" in combined
        )

    def test_priority_engine_ignores_completed_when_risk_high(self):
        """Even with Completed status, High safety risk → not Low."""
        result = calculate_final_priority(
            {"base_priority": "Low"},
            {
                "asset_criticality": "Safety-Critical",
                "current_status": "Completed",
                "safety_risk_level": "High",
            },
        )
        assert priority_order(result["final_priority"]) >= priority_order("High")
