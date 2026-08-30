"""Numeric boundary tests."""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import CONFIDENCE_THRESHOLD
from app.maintenance_intelligence.inference.classifier import classify_case
from app.maintenance_intelligence.inference.confidence import check_confidence
from app.maintenance_intelligence.inference.feature_builder import build_features
from app.maintenance_intelligence.io_schemas import ComplaintInput


class TestDaysOverdueBoundaries:
    @pytest.mark.parametrize("value", [-1, -999, 0, 1, 36500])
    def test_no_crash(self, value):
        c = ComplaintInput(complaint_text="Test", days_overdue=value)
        df = build_features(c)
        assert df["days_overdue"].iloc[0] == value


class TestFailureCountBoundaries:
    @pytest.mark.parametrize("value", [-1, 0, 999999])
    def test_no_crash(self, value):
        c = ComplaintInput(complaint_text="Test", failure_count_30_days=value)
        df = build_features(c)
        assert df["failure_count_30_days"].iloc[0] == value


class TestConfidenceBoundaries:
    def test_negative_rejected(self):
        result = check_confidence(-0.1)
        assert result["human_review_required"] is True

    def test_zero(self):
        result = check_confidence(0.0)
        assert result["human_review_required"] is True

    def test_exactly_at_threshold(self):
        result = check_confidence(0.75)
        assert result["is_confident"] is True

    def test_above_one_rejected(self):
        result = check_confidence(1.1)
        assert result["human_review_required"] is True

    def test_none(self):
        result = check_confidence(None)
        assert result["human_review_required"] is True

    def test_threshold_deterministic(self):
        r1 = check_confidence(0.75)
        r2 = check_confidence(0.75)
        assert r1["is_confident"] == r2["is_confident"]
