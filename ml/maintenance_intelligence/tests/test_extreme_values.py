"""Extreme value robustness tests.

Test the system with negative, zero, extreme, and unusual numeric values
to ensure no crashes, silent conversions, or dangerous misclassifications.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import VALID_PRIORITIES
from app.maintenance_intelligence.inference.classifier import classify_case
from app.maintenance_intelligence.inference.confidence import check_confidence
from app.maintenance_intelligence.inference.feature_builder import build_features
from app.maintenance_intelligence.prioritization.priority_engine import calculate_final_priority
from app.maintenance_intelligence.io_schemas import ComplaintInput


# ===================================================================
# days_overdue boundaries
# ===================================================================

class TestDaysOverdueExtremeValues:
    @pytest.mark.parametrize("value", [-1, -999, 0, 1, 36500, 99999])
    def test_no_crash(self, value):
        c = ComplaintInput(complaint_text="Test fault", days_overdue=value)
        df = build_features(c)
        assert df["days_overdue"].iloc[0] == value

    @pytest.mark.parametrize("value", [-1, 99999])
    def test_extreme_values_dont_crash_classifier(self, value):
        c = ComplaintInput(
            complaint_text="Test fault",
            asset_type="Track",
            days_overdue=value,
        )
        result = classify_case(c)
        assert isinstance(result, dict)

    def test_negative_days_overdue_not_silently_converted(self):
        c = ComplaintInput(complaint_text="Test", days_overdue=-5)
        df = build_features(c)
        assert df["days_overdue"].iloc[0] == -5  # Preserved, not zeroed


# ===================================================================
# failure_count_30_days boundaries
# ===================================================================

class TestFailureCountExtremeValues:
    @pytest.mark.parametrize("value", [-1, 0, 999999])
    def test_no_crash(self, value):
        c = ComplaintInput(complaint_text="Test fault", failure_count_30_days=value)
        df = build_features(c)
        assert df["failure_count_30_days"].iloc[0] == value

    @pytest.mark.parametrize("value", [-1, 999999])
    def test_extreme_values_dont_crash_classifier(self, value):
        c = ComplaintInput(
            complaint_text="Test fault",
            asset_type="Track",
            failure_count_30_days=value,
        )
        result = classify_case(c)
        assert isinstance(result, dict)

    def test_negative_failure_count_preserved(self):
        c = ComplaintInput(complaint_text="Test", failure_count_30_days=-3)
        df = build_features(c)
        assert df["failure_count_30_days"].iloc[0] == -3  # Preserved


# ===================================================================
# deferral_count boundaries
# ===================================================================

class TestDeferralCountExtremeValues:
    @pytest.mark.parametrize("value", [0, -1, 100])
    def test_no_crash(self, value):
        c = ComplaintInput(
            complaint_text="Test fault",
            current_status="Reopened",
            deferral_count=value,
        )
        result = classify_case(c)
        assert isinstance(result, dict)


# ===================================================================
# train_delay_minutes boundaries
# ===================================================================

class TestTrainDelayExtremeValues:
    """train_delay_minutes is not in the core feature set, but should not
    crash the ComplaintInput schema."""

    @pytest.mark.parametrize("value", [0, -1, 100000])
    def test_no_crash(self, value):
        c = ComplaintInput(
            complaint_text="Test fault",
            train_delay_minutes=value,
        )
        result = classify_case(c)
        assert isinstance(result, dict)


# ===================================================================
# Suspicious value detection
# ===================================================================

class TestSuspiciousValueHandling:
    """Suspicious values should not silently normalise to safe values."""

    def test_extreme_failure_count_not_zeroed(self):
        c = ComplaintInput(complaint_text="Test", failure_count_30_days=999999)
        df = build_features(c)
        assert df["failure_count_30_days"].iloc[0] == 999999

    def test_extreme_overdue_not_zeroed(self):
        c = ComplaintInput(complaint_text="Test", days_overdue=999999)
        df = build_features(c)
        assert df["days_overdue"].iloc[0] == 999999

    def test_negative_values_not_silently_positive(self):
        c = ComplaintInput(complaint_text="Test", days_overdue=-10, failure_count_30_days=-5)
        df = build_features(c)
        assert df["days_overdue"].iloc[0] == -10
        assert df["failure_count_30_days"].iloc[0] == -5


# ===================================================================
# Confidence boundaries
# ===================================================================

class TestConfidenceExtremeValues:
    def test_negative_confidence_rejected(self):
        result = check_confidence(-0.01)
        assert result["human_review_required"] is True

    def test_zero_confidence(self):
        result = check_confidence(0.0)
        assert result["human_review_required"] is True

    def test_above_one_rejected(self):
        result = check_confidence(1.01)
        assert result["human_review_required"] is True

    def test_large_negative(self):
        result = check_confidence(-999999)
        assert result["human_review_required"] is True

    def test_large_positive(self):
        result = check_confidence(999999)
        assert result["human_review_required"] is True
