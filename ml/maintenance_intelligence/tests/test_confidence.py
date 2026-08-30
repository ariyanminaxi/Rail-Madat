"""Confidence tests."""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import CONFIDENCE_THRESHOLD
from app.maintenance_intelligence.inference.confidence import check_confidence, get_confidence_level


class TestConfidenceThreshold:
    def test_high_confidence_not_flagged(self):
        result = check_confidence(0.95)
        assert result["is_confident"] is True
        assert result["human_review_required"] is False

    def test_below_threshold_flagged(self):
        result = check_confidence(0.74)
        assert result["human_review_required"] is True
        assert result["is_confident"] is False

    def test_exactly_at_threshold(self):
        result = check_confidence(0.75)
        assert result["is_confident"] is True
        assert result["human_review_required"] is False

    def test_just_below_threshold(self):
        result = check_confidence(0.7499999)
        assert result["is_confident"] is False
        assert result["human_review_required"] is True

    def test_very_low_flagged(self):
        result = check_confidence(0.20)
        assert result["human_review_required"] is True

    def test_none_always_triggers_review(self):
        result = check_confidence(None)
        assert result["human_review_required"] is True
        assert result["is_confident"] is False

    def test_negative_confidence_rejected(self):
        result = check_confidence(-0.1)
        assert result["human_review_required"] is True
        assert result["is_confident"] is False

    def test_above_one_rejected(self):
        result = check_confidence(1.1)
        assert result["human_review_required"] is True
        assert result["is_confident"] is False

    def test_one_point_zero_valid(self):
        result = check_confidence(1.0)
        assert result["is_confident"] is True


class TestConfidenceLevelLabels:
    @pytest.mark.parametrize("confidence, expected", [
        (0.95, "High"),
        (0.80, "Medium"),
        (0.60, "Low"),
        (0.30, "Very Low"),
        (None, "Unknown"),
        (-0.1, "Invalid"),
        (1.5, "Invalid"),
    ])
    def test_level_labels(self, confidence, expected):
        assert get_confidence_level(confidence) == expected


class TestThresholdDeterministic:
    def test_same_value_same_result(self):
        r1 = check_confidence(0.75)
        r2 = check_confidence(0.75)
        assert r1["is_confident"] == r2["is_confident"]

    def test_boundary_at_config_threshold(self):
        assert CONFIDENCE_THRESHOLD == 0.75
        result = check_confidence(0.75)
        assert result["threshold"] == 0.75
