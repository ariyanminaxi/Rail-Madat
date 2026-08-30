"""Explanation tests."""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.inference.explanation import (
    format_explanation_for_display, generate_explanation,
)


class TestSafetyCriticalInterrupted:
    def test_contains_safety_critical_reason(self):
        context = {"asset_criticality": "Safety-Critical", "current_status": "Interrupted",
                    "safety_risk_level": "High", "service_impact_level": "Major", "days_overdue": 3,
                    "failure_count_30_days": 2}
        priority_reasons = ["Asset is safety-critical and status is Interrupted"]
        confidence_info = {"human_review_required": False}
        explanations = generate_explanation({}, context, priority_reasons, confidence_info)
        combined = " ".join(explanations).lower()
        assert "safety-critical" in combined
        assert "interrupted" in combined


class TestExtremeSafetyRisk:
    def test_contains_extreme_risk(self):
        context = {"asset_criticality": "Safety-Critical", "current_status": "Escalated",
                    "safety_risk_level": "Extreme", "service_impact_level": "Severe",
                    "days_overdue": 5, "failure_count_30_days": 3}
        priority_reasons = ["Extreme safety risk overrides all priorities"]
        confidence_info = {"human_review_required": True, "confidence": 0.65}
        explanations = generate_explanation({}, context, priority_reasons, confidence_info)
        combined = " ".join(explanations).lower()
        assert "extreme" in combined


class TestLowConfidenceExplanation:
    def test_mentions_low_confidence(self):
        context = {"asset_criticality": "Non-Critical", "current_status": "New",
                    "safety_risk_level": "Low", "service_impact_level": "Minor",
                    "days_overdue": 0, "failure_count_30_days": 0}
        priority_reasons = []
        confidence_info = {"human_review_required": True, "confidence": 0.45}
        explanations = generate_explanation({}, context, priority_reasons, confidence_info)
        combined = " ".join(explanations).lower()
        assert "confidence" in combined or "review" in combined


class TestNoEscalationExplanation:
    def test_valid_not_misleading(self):
        context = {"asset_criticality": "Non-Critical", "current_status": "New",
                    "safety_risk_level": "Low", "service_impact_level": "Minor",
                    "days_overdue": 0, "failure_count_30_days": 0}
        priority_reasons = []
        confidence_info = {"human_review_required": False}
        explanations = generate_explanation({}, context, priority_reasons, confidence_info)
        assert len(explanations) > 0


class TestExplanationContent:
    def test_service_impact_major_included(self):
        context = {"asset_criticality": "Non-Critical", "current_status": "New",
                    "safety_risk_level": "Low", "service_impact_level": "Major",
                    "days_overdue": 0, "failure_count_30_days": 0}
        explanations = generate_explanation({}, context, [], {"human_review_required": False})
        combined = " ".join(explanations).lower()
        assert "major" in combined

    def test_overdue_days_included(self):
        context = {"asset_criticality": "Non-Critical", "current_status": "New",
                    "safety_risk_level": "Low", "service_impact_level": "Minor",
                    "days_overdue": 7, "failure_count_30_days": 0}
        explanations = generate_explanation({}, context, [], {"human_review_required": False})
        combined = " ".join(explanations).lower()
        assert "overdue" in combined

    def test_failure_count_included(self):
        context = {"asset_criticality": "Non-Critical", "current_status": "New",
                    "safety_risk_level": "Low", "service_impact_level": "Minor",
                    "days_overdue": 0, "failure_count_30_days": 3}
        explanations = generate_explanation({}, context, [], {"human_review_required": False})
        combined = " ".join(explanations).lower()
        assert "occurred" in combined


class TestFormatExplanationForDisplay:
    def test_format_returns_string(self):
        text = format_explanation_for_display(["Reason A", "Reason B"])
        assert isinstance(text, str)

    def test_format_numbered(self):
        text = format_explanation_for_display(["Alpha", "Beta", "Gamma"])
        assert "1. Alpha" in text
        assert "2. Beta" in text
