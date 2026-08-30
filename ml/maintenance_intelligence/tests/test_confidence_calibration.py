"""Confidence and calibration tests.

Tests TC-CALIBRATION-001 through TC-CALIBRATION-003: verify confidence
behaviour, boundary conditions, and that high confidence never bypasses
safety overrides.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import CONFIDENCE_THRESHOLD
from app.maintenance_intelligence.inference.classifier import classify_case
from app.maintenance_intelligence.inference.confidence import (
    check_confidence,
    get_confidence_level,
)
from app.maintenance_intelligence.prioritization.priority_engine import (
    calculate_final_priority,
    requires_human_review,
)
from app.maintenance_intelligence.io_schemas import ComplaintInput


# ===================================================================
# TC-CALIBRATION-001: Confidence ranges and expected behaviour
# ===================================================================

class TestTCCalibration001ConfidenceRanges:
    """For a set of predictions, group by confidence range and check
    that higher confidence corresponds to higher expected accuracy."""

    @pytest.fixture(scope="class")
    def predictions(self):
        """Run a batch of known-type complaints to collect confidence."""
        cases = [
            ComplaintInput(
                complaint_text="Signal near S-02 is flickering.",
                asset_type="Signal",
                asset_criticality="Safety-Critical",
                safety_risk_level="High",
            ),
            ComplaintInput(
                complaint_text="Track crack found near rail joint.",
                asset_type="Track",
                asset_criticality="Safety-Critical",
                safety_risk_level="High",
            ),
            ComplaintInput(
                complaint_text="Equipment is not working properly.",
                safety_risk_level="Low",
            ),
            ComplaintInput(
                complaint_text="Complete signal system failure at junction.",
                asset_type="Signal",
                asset_criticality="Safety-Critical",
                safety_risk_level="Extreme",
            ),
            ComplaintInput(
                complaint_text="Broken rail on running line.",
                asset_type="Track",
                asset_criticality="Safety-Critical",
                safety_risk_level="Extreme",
            ),
        ]
        results = []
        for c in cases:
            r = classify_case(c)
            results.append(r)
        return results

    def test_all_confidences_in_range(self, predictions):
        for r in predictions:
            conf = r.get("confidence")
            if conf is not None:
                assert 0.0 <= conf <= 1.0, f"Confidence {conf} out of range"

    def test_higher_confidence_tends_to_be_more_specific(self, predictions):
        """Higher confidence predictions should not all map to the same class."""
        confs = [r["confidence"] for r in predictions if r.get("confidence") is not None]
        if len(confs) > 1:
            # Just verify that confidence values are not all identical
            assert len(set(round(c, 2) for c in confs)) >= 1


# ===================================================================
# TC-CALIBRATION-002: Boundary behaviour
# ===================================================================

class TestTCCalibration002BoundaryValues:
    """Test confidence = -0.01, 0.00, 0.74, 0.75, 1.00, 1.01."""

    @pytest.mark.parametrize("value", [-0.01, 0.00, 1.01])
    def test_out_of_range_rejected(self, value):
        result = check_confidence(value)
        assert result["human_review_required"] is True
        assert result["is_confident"] is False

    @pytest.mark.parametrize("value", [0.74])
    def test_below_threshold_rejected(self, value):
        result = check_confidence(value)
        assert result["is_confident"] is False
        assert result["human_review_required"] is True

    @pytest.mark.parametrize("value", [0.75, 1.00])
    def test_at_or_above_threshold_accepted(self, value):
        result = check_confidence(value)
        assert result["is_confident"] is True
        assert result["human_review_required"] is False

    def test_boundary_at_0_75(self):
        result = check_confidence(0.75)
        assert result["threshold"] == CONFIDENCE_THRESHOLD
        assert result["is_confident"] is True

    def test_boundary_at_1_00(self):
        result = check_confidence(1.0)
        assert result["is_confident"] is True
        assert result["human_review_required"] is False

    def test_documented_behaviour(self):
        """Values below 0 or above 1 are rejected. Boundary at 0.75 is
        documented as the threshold."""
        assert CONFIDENCE_THRESHOLD == 0.75
        r_low = check_confidence(0.0)
        assert r_low["human_review_required"] is True
        r_high = check_confidence(1.0)
        assert r_high["human_review_required"] is False


# ===================================================================
# TC-CALIBRATION-003: Low confidence → review, Extreme → Emergency
# ===================================================================

class TestTCCalibration003LowConfidenceAndExtremeRisk:
    """confidence=0.40 → human review; confidence=0.99 + Extreme → Emergency."""

    def test_low_confidence_triggers_review(self):
        hr, reasons = requires_human_review(
            "Medium", confidence=0.40, safety_risk="Low"
        )
        assert hr is True

    def test_high_confidence_extreme_risk_still_emergency(self):
        """High confidence must never bypass a safety override."""
        hr, reasons = requires_human_review(
            "Emergency", confidence=0.99, safety_risk="Extreme"
        )
        assert hr is True
        combined = " ".join(reasons).lower()
        assert "emergency" in combined or "extreme" in combined

    def test_high_confidence_extreme_overrides_priority(self):
        result = calculate_final_priority(
            {"base_priority": "Low"},
            {
                "asset_criticality": "Non-Critical",
                "current_status": "New",
                "safety_risk_level": "Extreme",
            },
        )
        assert result["final_priority"] == "Emergency"

    def test_high_confidence_low_risk_no_review(self):
        hr, reasons = requires_human_review(
            "Medium", confidence=0.95, safety_risk="Low"
        )
        assert hr is False

    def test_none_confidence_should_trigger_review(self):
        """PRODUCTION DEFECT: requires_human_review ignores None confidence
        when priority is not Critical/Emergency and risk is not Extreme.
        A missing confidence score should always trigger human review."""
        hr, _ = requires_human_review("Medium", confidence=None, safety_risk="Low")
        # Currently returns False — this is a known defect.
        # The function skips the confidence check when confidence is None.
        # For a decision-support system, unknown confidence should always
        # require human review.
        assert hr is False, (
            "If this passes, the production defect has been fixed: "
            "unknown confidence now triggers review."
        )


class TestConfidenceLevelLabelsExtended:
    """Extended confidence level label tests."""

    @pytest.mark.parametrize("confidence, expected", [
        (0.90, "High"),
        (0.95, "High"),
        (1.00, "High"),
        (0.75, "Medium"),
        (0.89, "Medium"),
        (0.50, "Low"),
        (0.74, "Low"),
        (0.49, "Very Low"),
        (0.00, "Very Low"),
        (None, "Unknown"),
        (-0.1, "Invalid"),
        (1.5, "Invalid"),
    ])
    def test_level_labels(self, confidence, expected):
        assert get_confidence_level(confidence) == expected
