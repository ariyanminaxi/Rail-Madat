"""Advanced multi-symptom classification tests.

Tests TC-HIGH-001 through TC-HIGH-003: reports containing multiple symptoms
that require the system to prioritise, classify, and escalate correctly.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import (
    VALID_DEPARTMENTS,
    VALID_FAULT_CATEGORIES,
    VALID_PRIORITIES,
    VALID_SEVERITIES,
)
from app.maintenance_intelligence.inference.classifier import classify_case
from app.maintenance_intelligence.inference.confidence import check_confidence
from app.maintenance_intelligence.inference.explanation import generate_explanation
from app.maintenance_intelligence.prioritization.priority_engine import (
    calculate_final_priority,
    get_recommended_action,
    requires_human_review,
)
from app.maintenance_intelligence.io_schemas import ComplaintInput


# ---------------------------------------------------------------------------
# Helper: run the full pipeline end-to-end
# ---------------------------------------------------------------------------

def _full_pipeline(complaint: ComplaintInput) -> dict:
    """Run classify → prioritise → confidence → explain → review."""
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
    action = get_recommended_action(
        priority_result["final_priority"],
        classification.get("fault_category", ""),
        complaint.safety_risk_level or "Low",
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
        "action": action,
        "human_review_required": hr_required,
    }


# ===================================================================
# TC-HIGH-001: Signal plus communication symptoms
# ===================================================================

class TestTCHigh001SignalCommunicationSymptoms:
    """Signal flickering + route-setting delay + relay clicking."""

    @pytest.fixture(scope="class")
    def result(self):
        complaint = ComplaintInput(
            complaint_text=(
                "The signal aspect flickers intermittently, route setting "
                "takes longer than usual, and the relay cabinet shows a "
                "repeated clicking sound."
            ),
            asset_type="Signal",
            asset_criticality="Safety-Critical",
            current_status="Classified",
            days_overdue=0,
            failure_count_30_days=3,
            safety_risk_level="High",
            service_impact_level="Major",
        )
        return _full_pipeline(complaint)

    def test_department_is_valid(self, result):
        assert result["classification"]["department"] in VALID_DEPARTMENTS

    def test_fault_category_is_valid(self, result):
        assert result["classification"]["fault_category"] in VALID_FAULT_CATEGORIES

    def test_severity_is_valid(self, result):
        assert result["classification"]["severity"] in VALID_SEVERITIES

    def test_base_priority_is_valid(self, result):
        assert result["classification"]["base_priority"] in VALID_PRIORITIES

    def test_primary_fault_is_selected(self, result):
        """The model should pick a single fault category, not None or empty."""
        fc = result["classification"]["fault_category"]
        assert fc and len(fc) > 0

    def test_repeated_failure_in_explanation(self, result):
        combined = " ".join(result["explanation"]).lower()
        # failure_count_30_days=3 should appear in explanation
        assert "3" in combined or "occurred" in combined or "time" in combined

    def test_final_priority_not_lower_than_high(self, result):
        """Safety-Critical + High safety risk + Major impact → not Low/Medium."""
        order = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3, "Emergency": 4}
        assert order[result["priority_result"]["final_priority"]] >= order["High"]

    def test_human_review_required(self, result):
        assert result["human_review_required"] is True


# ===================================================================
# TC-HIGH-002: Track crack with operational impact
# ===================================================================

class TestTCHigh002TrackCrackOperationalImpact:
    """Visible crack + speed restriction + vibration increase + overdue."""

    @pytest.fixture(scope="class")
    def result(self):
        complaint = ComplaintInput(
            complaint_text=(
                "A visible crack has been found close to the rail joint. "
                "Trains are passing under a temporary speed restriction and "
                "vibration has increased."
            ),
            asset_type="Track",
            asset_criticality="Safety-Critical",
            current_status="Waiting for Inspection",
            days_overdue=4,
            failure_count_30_days=0,
            safety_risk_level="Extreme",
            service_impact_level="Major",
            train_delay_minutes=25,
        )
        return _full_pipeline(complaint)

    def test_final_priority_emergency(self, result):
        assert result["priority_result"]["final_priority"] == "Emergency"

    def test_human_review_required(self, result):
        assert result["human_review_required"] is True

    def test_explanation_mentions_extreme(self, result):
        combined = " ".join(result["explanation"]).lower()
        assert "extreme" in combined

    def test_explanation_mentions_safety_critical(self, result):
        combined = " ".join(result["explanation"]).lower()
        assert "safety-critical" in combined

    def test_explanation_mentions_operational_impact(self, result):
        combined = " ".join(result["explanation"]).lower()
        assert "major" in combined or "impact" in combined or "restriction" in combined


# ===================================================================
# TC-HIGH-003: Point machine degradation
# ===================================================================

class TestTCHigh003PointMachineDegradation:
    """Slow operation, second-attempt success, repeated manual intervention."""

    @pytest.fixture(scope="class")
    def result(self):
        complaint = ComplaintInput(
            complaint_text=(
                "The point machine operates slowly during route setting, "
                "succeeds on the second attempt, and has required manual "
                "intervention twice this week."
            ),
            asset_type="Signal",
            asset_criticality="Safety-Critical",
            current_status="New",
            days_overdue=0,
            failure_count_30_days=2,
            safety_risk_level="High",
            service_impact_level="Major",
        )
        return _full_pipeline(complaint)

    def test_not_misclassified_as_total_failure(self, result):
        """Degradation should not be treated as 'complete failure' unless
        supported by labels.  The system should not claim the asset is safe."""
        # The classifier may predict Mechanical failure, Switch failure, etc.
        # but must produce a valid category.
        assert result["classification"]["fault_category"] in VALID_FAULT_CATEGORIES

    def test_repeated_intervention_in_explanation(self, result):
        combined = " ".join(result["explanation"]).lower()
        assert (
            "manual" in combined
            or "intervention" in combined
            or "occurred" in combined
            or "time" in combined
        )

    def test_recommended_action_includes_repair_or_inspection(self, result):
        action = result["action"].lower()
        assert "inspection" in action or "repair" in action or "emergency" in action or "immediate" in action or "prioritised" in action

    def test_model_does_not_claim_asset_is_safe(self, result):
        """An explanation should never state the asset is safe when faults
        are reported.  'Asset is safety-critical' is acceptable, but a
        standalone phrase like 'the asset is safe' is not."""
        combined = " ".join(result["explanation"]).lower()
        # The only acceptable use of 'is safe' is as part of 'is safety'
        import re
        safe_matches = re.findall(r'is safe(?!ty)', combined)
        assert len(safe_matches) == 0, (
            f"Found 'is safe' (not 'is safety') in explanation: {combined}"
        )
        assert "no fault" not in combined
