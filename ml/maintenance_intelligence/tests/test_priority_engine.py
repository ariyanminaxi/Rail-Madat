"""Priority engine tests."""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import CONFIDENCE_THRESHOLD
from app.maintenance_intelligence.prioritization.priority_engine import (
    calculate_final_priority, get_recommended_action, priority_order, requires_human_review,
)


class TestParametrizedPriorityScenarios:
    @pytest.mark.parametrize(
        "base, criticality, status, safety_risk, expected, needs_review",
        [
            ("Low", "Operational", "New", "Low", "Low", False),
            ("High", "Safety-Critical", "New", "High", "High", False),
            ("High", "Safety-Critical", "Interrupted", "High", "Critical", True),
            ("Medium", "Important", "Reopened", "High", "High", False),
            ("Medium", "Important", "In Progress", "Medium", "Medium", False),
            ("High", "Safety-Critical", "In Progress", "High", "High", False),
            ("High", "Operational", "Escalated", "High", "Critical", True),
            ("Low", "Non-Critical", "New", "Extreme", "Emergency", True),
            ("High", "Safety-Critical", "Reopened", "Extreme", "Emergency", True),
            ("Low", "Non-Critical", "Completed", "Low", "Low", False),
        ],
    )
    def test_priority_and_review(self, base, criticality, status, safety_risk, expected, needs_review):
        prediction = {"base_priority": base}
        context = {
            "asset_criticality": criticality,
            "current_status": status,
            "safety_risk_level": safety_risk,
        }
        result = calculate_final_priority(prediction, context)
        assert result["final_priority"] == expected

    @pytest.mark.parametrize("base, criticality, status, safety_risk", [
        ("Low", "Non-Critical", "New", "Low"),
        ("Medium", "Operational", "In Progress", "Medium"),
        ("High", "Safety-Critical", "Interrupted", "High"),
    ])
    def test_final_never_below_base(self, base, criticality, status, safety_risk):
        prediction = {"base_priority": base}
        context = {
            "asset_criticality": criticality,
            "current_status": status,
            "safety_risk_level": safety_risk,
        }
        result = calculate_final_priority(prediction, context)
        assert priority_order(result["final_priority"]) >= priority_order(base)


class TestSafetyOverrides:
    def test_extreme_overrides_everything(self):
        for base in ["Low", "Medium", "High", "Critical"]:
            result = calculate_final_priority(
                {"base_priority": base},
                {"asset_criticality": "Non-Critical", "current_status": "New", "safety_risk_level": "Extreme"},
            )
            assert result["final_priority"] == "Emergency"

    def test_safety_critical_interrupted_escalation(self):
        result = calculate_final_priority(
            {"base_priority": "Low"},
            {"asset_criticality": "Safety-Critical", "current_status": "Interrupted", "safety_risk_level": "Low"},
        )
        assert result["final_priority"] == "Critical"

    def test_escalated_always_critical(self):
        for base in ["Low", "Medium"]:
            result = calculate_final_priority(
                {"base_priority": base},
                {"asset_criticality": "Non-Critical", "current_status": "Escalated", "safety_risk_level": "Low"},
            )
            assert result["final_priority"] == "Critical"

    def test_high_safety_risk_escalates_low_to_high(self):
        result = calculate_final_priority(
            {"base_priority": "Low"},
            {"asset_criticality": "Non-Critical", "current_status": "New", "safety_risk_level": "High"},
        )
        assert result["final_priority"] == "High"


class TestRecommendedActions:
    @pytest.mark.parametrize("priority, expected_keyword", [
        ("Emergency", "emergency"),
        ("Critical", "immediate"),
        ("High", "prioritised"),
        ("Medium", "standard"),
        ("Low", "routine"),
    ])
    def test_action_matches_priority(self, priority, expected_keyword):
        action = get_recommended_action(priority, "Track defect", "Low")
        assert expected_keyword.lower() in action.lower()


class TestRequiresHumanReview:
    def test_critical_needs_review(self):
        hr, _ = requires_human_review("Critical", confidence=0.9)
        assert hr is True

    def test_emergency_needs_review(self):
        hr, _ = requires_human_review("Emergency", confidence=0.95)
        assert hr is True

    def test_low_confidence_needs_review(self):
        hr, _ = requires_human_review("Medium", confidence=0.5)
        assert hr is True

    def test_extreme_needs_review(self):
        hr, _ = requires_human_review("Low", confidence=0.99, safety_risk="Extreme")
        assert hr is True

    def test_high_confidence_safe_no_review(self):
        hr, _ = requires_human_review("Medium", confidence=0.9, safety_risk="Low")
        assert hr is False

    def test_boundary_confidence(self):
        hr, _ = requires_human_review("Medium", confidence=0.75)
        assert hr is False

    def test_just_below_boundary(self):
        hr, _ = requires_human_review("Medium", confidence=0.749)
        assert hr is True


class TestPriorityOrderFunction:
    def test_order_values(self):
        assert priority_order("Low") == 0
        assert priority_order("Emergency") == 4

    def test_invalid_priority_defaults_to_medium(self):
        assert priority_order("Invalid") == 1

    def test_ordering_consistency(self):
        priorities = ["Low", "Medium", "High", "Critical", "Emergency"]
        for i in range(len(priorities) - 1):
            assert priority_order(priorities[i]) < priority_order(priorities[i + 1])


class TestMissingContextKeys:
    def test_empty_context_uses_defaults(self):
        result = calculate_final_priority({"base_priority": "High"}, {})
        assert "final_priority" in result
        assert isinstance(result["reasons"], list)

    def test_invalid_priority_defaults(self):
        result = calculate_final_priority(
            {"base_priority": "Bogus"},
            {"asset_criticality": "Non-Critical", "current_status": "New", "safety_risk_level": "Low"},
        )
        assert result["final_priority"] in ("Medium", "High", "Critical", "Emergency")
        assert any("Invalid" in r for r in result["reasons"])
