"""Safety-critical false negative tests.

For every test case where safety_risk_level = Extreme or
asset_criticality = Safety-Critical, verify:
  - predicted final_priority is not Low
  - predicted final_priority is not Medium
  - human_review_required = true

Produce a structured report of dangerous false negatives.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import VALID_PRIORITIES
from app.maintenance_intelligence.inference.classifier import classify_case
from app.maintenance_intelligence.prioritization.priority_engine import (
    calculate_final_priority,
    priority_order,
    requires_human_review,
)
from app.maintenance_intelligence.io_schemas import ComplaintInput


# ---------------------------------------------------------------------------
# All safety-critical / extreme-risk test vectors
# ---------------------------------------------------------------------------

SAFETY_CRITICAL_CASES = [
    {
        "id": "TC-SAFETY-001",
        "complaint_text": "Complete signal system failure at junction J-10.",
        "asset_type": "Signal",
        "asset_criticality": "Safety-Critical",
        "current_status": "Escalated",
        "safety_risk_level": "Extreme",
        "service_impact_level": "Severe",
    },
    {
        "id": "TC-SAFETY-002",
        "complaint_text": "Rail is visibly broken near an active running line.",
        "asset_type": "Track",
        "asset_criticality": "Safety-Critical",
        "current_status": "New",
        "safety_risk_level": "Extreme",
        "service_impact_level": "Major",
    },
    {
        "id": "TC-SAFETY-003",
        "complaint_text": "Signal repair was interrupted because testing equipment failed.",
        "asset_type": "Signal",
        "asset_criticality": "Safety-Critical",
        "current_status": "Interrupted",
        "safety_risk_level": "High",
        "service_impact_level": "Major",
    },
    {
        "id": "TC-SAFETY-004",
        "complaint_text": "Signal fault reappears after repeated deferral.",
        "asset_type": "Signal",
        "asset_criticality": "Safety-Critical",
        "current_status": "Reopened",
        "days_overdue": 14,
        "safety_risk_level": "High",
    },
    {
        "id": "TC-SAFETY-005",
        "complaint_text": "A visible crack has been found close to the rail joint. Trains passing under speed restriction.",
        "asset_type": "Track",
        "asset_criticality": "Safety-Critical",
        "current_status": "Waiting for Inspection",
        "days_overdue": 4,
        "safety_risk_level": "Extreme",
        "service_impact_level": "Major",
    },
    {
        "id": "TC-SAFETY-006",
        "complaint_text": "Track crack found near rail joint.",
        "asset_type": "Track",
        "asset_criticality": "Safety-Critical",
        "current_status": "New",
        "safety_risk_level": "High",
        "service_impact_level": "Major",
    },
    {
        "id": "TC-SAFETY-007",
        "complaint_text": "Point machine operates slowly and requires manual intervention.",
        "asset_type": "Signal",
        "asset_criticality": "Safety-Critical",
        "current_status": "New",
        "safety_risk_level": "High",
        "failure_count_30_days": 3,
        "service_impact_level": "Major",
    },
    {
        "id": "TC-SAFETY-008",
        "complaint_text": "Signal flickering with relay clicking sound.",
        "asset_type": "Signal",
        "asset_criticality": "Safety-Critical",
        "current_status": "Classified",
        "safety_risk_level": "High",
        "service_impact_level": "Major",
    },
    {
        "id": "TC-SAFETY-009",
        "complaint_text": "Broken rail on running line.",
        "asset_type": "Track",
        "asset_criticality": "Safety-Critical",
        "current_status": "Escalated",
        "safety_risk_level": "Extreme",
        "service_impact_level": "Severe",
    },
    {
        "id": "TC-SAFETY-010",
        "complaint_text": "Equipment not responding, manual override required.",
        "asset_type": "Signal",
        "asset_criticality": "Safety-Critical",
        "current_status": "Interrupted",
        "safety_risk_level": "High",
        "service_impact_level": "Major",
    },
]


def _run_full_pipeline(case):
    """Run classification + prioritisation + human review check."""
    kwargs = {k: v for k, v in case.items() if k != "id"}
    complaint = ComplaintInput(**kwargs)
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
    hr_required, _ = requires_human_review(
        priority_result["final_priority"],
        classification["confidence"],
        safety_risk=complaint.safety_risk_level or "Low",
    )
    return {
        "case_id": case["id"],
        "classification": classification,
        "final_priority": priority_result["final_priority"],
        "human_review_required": hr_required,
    }


# ===================================================================
# Parametrized tests
# ===================================================================

class TestSafetyFalseNegatives:
    """Verify no dangerous under-prioritisation for safety-critical cases."""

    @pytest.mark.parametrize("case", SAFETY_CRITICAL_CASES, ids=[c["id"] for c in SAFETY_CRITICAL_CASES])
    def test_extreme_risk_not_low_or_medium(self, case):
        """Extreme safety risk must never produce Low or Medium final priority."""
        if case.get("safety_risk_level") != "Extreme":
            pytest.skip("Not an Extreme case")
        result = _run_full_pipeline(case)
        assert result["final_priority"] not in ("Low", "Medium"), (
            f"{case['id']}: Extreme risk produced {result['final_priority']}"
        )

    @pytest.mark.parametrize("case", SAFETY_CRITICAL_CASES, ids=[c["id"] for c in SAFETY_CRITICAL_CASES])
    def test_safety_critical_not_low(self, case):
        """Safety-Critical asset must never produce Low final priority."""
        if case.get("asset_criticality") != "Safety-Critical":
            pytest.skip("Not a Safety-Critical case")
        result = _run_full_pipeline(case)
        assert result["final_priority"] != "Low", (
            f"{case['id']}: Safety-Critical produced Low priority"
        )

    @pytest.mark.parametrize("case", SAFETY_CRITICAL_CASES, ids=[c["id"] for c in SAFETY_CRITICAL_CASES])
    def test_safety_critical_interrupted_not_low(self, case):
        """Safety-Critical + Interrupted must not be Low."""
        if not (case.get("asset_criticality") == "Safety-Critical" and case.get("current_status") == "Interrupted"):
            pytest.skip("Not a Safety-Critical + Interrupted case")
        result = _run_full_pipeline(case)
        assert result["final_priority"] != "Low"

    @pytest.mark.parametrize("case", SAFETY_CRITICAL_CASES, ids=[c["id"] for c in SAFETY_CRITICAL_CASES])
    def test_safety_critical_reopened_not_medium(self, case):
        """Safety-Critical + Reopened must not be Medium."""
        if not (case.get("asset_criticality") == "Safety-Critical" and case.get("current_status") == "Reopened"):
            pytest.skip("Not a Safety-Critical + Reopened case")
        result = _run_full_pipeline(case)
        assert priority_order(result["final_priority"]) >= priority_order("Critical"), (
            f"{case['id']}: Safety-Critical + Reopened produced {result['final_priority']}"
        )

    @pytest.mark.parametrize("case", SAFETY_CRITICAL_CASES, ids=[c["id"] for c in SAFETY_CRITICAL_CASES])
    def test_human_review_always_required(self, case):
        """All safety-critical / extreme-risk cases must require human review."""
        result = _run_full_pipeline(case)
        assert result["human_review_required"] is True, (
            f"{case['id']}: human review not required for safety-critical case"
        )


# ===================================================================
# Explicit dangerous false negative scenarios
# ===================================================================

class TestExplicitDangerousScenarios:
    """Directly test the documented dangerous false negative patterns."""

    def test_extreme_does_not_produce_low(self):
        result = calculate_final_priority(
            {"base_priority": "Low"},
            {"asset_criticality": "Non-Critical", "current_status": "New", "safety_risk_level": "Extreme"},
        )
        assert result["final_priority"] != "Low"

    def test_extreme_does_not_produce_medium(self):
        result = calculate_final_priority(
            {"base_priority": "Low"},
            {"asset_criticality": "Non-Critical", "current_status": "New", "safety_risk_level": "Extreme"},
        )
        assert result["final_priority"] != "Medium"

    def test_safety_critical_interrupted_not_low(self):
        result = calculate_final_priority(
            {"base_priority": "Low"},
            {"asset_criticality": "Safety-Critical", "current_status": "Interrupted", "safety_risk_level": "Low"},
        )
        assert result["final_priority"] != "Low"

    def test_safety_critical_reopened_not_medium(self):
        result = calculate_final_priority(
            {"base_priority": "Low"},
            {"asset_criticality": "Safety-Critical", "current_status": "Reopened", "safety_risk_level": "Low"},
        )
        assert priority_order(result["final_priority"]) >= priority_order("Critical")

    def test_all_extreme_cases_emergency(self):
        for base in ["Low", "Medium", "High", "Critical"]:
            result = calculate_final_priority(
                {"base_priority": base},
                {"asset_criticality": "Non-Critical", "current_status": "New", "safety_risk_level": "Extreme"},
            )
            assert result["final_priority"] == "Emergency"


# ===================================================================
# Report generation
# ===================================================================

class TestSafetyReport:
    """Produce the required safety false negative report."""

    def test_report_format(self):
        results = [_run_full_pipeline(c) for c in SAFETY_CRITICAL_CASES]

        dangerous_fn = 0
        review_failures = 0

        for r in results:
            fp = r["final_priority"]
            # Check for dangerous false negatives
            if fp in ("Low", "Medium"):
                dangerous_fn += 1
            if not r["human_review_required"]:
                review_failures += 1

        critical_cases = [r for r in results if r["final_priority"] in ("Critical", "Emergency")]
        emergency_cases = [r for r in results if r["final_priority"] == "Emergency"]

        report = {
            "dangerous_false_negatives": dangerous_fn,
            "critical_case_recall": len(critical_cases) / len(results) if results else 0.0,
            "emergency_case_recall": len(emergency_cases) / len(results) if results else 0.0,
            "review_required_failures": review_failures,
        }

        # All should be zero or acceptable
        assert report["dangerous_false_negatives"] == 0
        assert report["review_required_failures"] == 0
        assert report["emergency_case_recall"] > 0

        # Print report for visibility
        print(json.dumps(report, indent=2))
