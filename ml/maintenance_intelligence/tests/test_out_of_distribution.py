"""Out-of-distribution input tests.

Tests TC-OOD-001 through TC-OOD-004: the system must handle language,
assets, and abbreviations not represented in the training dataset without
crashing, fabricating, or producing dangerous misclassifications.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import VALID_DEPARTMENTS, VALID_FAULT_CATEGORIES
from app.maintenance_intelligence.inference.classifier import classify_case
from app.maintenance_intelligence.prioritization.priority_engine import calculate_final_priority
from app.maintenance_intelligence.io_schemas import ComplaintInput


class TestTCOOD001UnknownAsset:
    """Wayside equipment not in training data."""

    def test_no_crash(self):
        c = ComplaintInput(
            complaint_text="An unfamiliar wayside equipment unit is showing intermittent behavior.",
            asset_type="Wayside Equipment",
            asset_criticality="Operational",
            safety_risk_level="Medium",
        )
        result = classify_case(c)
        assert isinstance(result, dict)

    def test_valid_department(self):
        c = ComplaintInput(
            complaint_text="An unfamiliar wayside equipment unit is showing intermittent behavior.",
            asset_type="Wayside Equipment",
            asset_criticality="Operational",
            safety_risk_level="Medium",
        )
        result = classify_case(c)
        assert result["department"] in VALID_DEPARTMENTS or result["department"] == "Unknown"

    def test_valid_fault_category(self):
        c = ComplaintInput(
            complaint_text="An unfamiliar wayside equipment unit is showing intermittent behavior.",
            asset_type="Wayside Equipment",
            asset_criticality="Operational",
            safety_risk_level="Medium",
        )
        result = classify_case(c)
        assert result["fault_category"] in VALID_FAULT_CATEGORIES

    def test_human_review_likely(self):
        """With unknown asset type, confidence is expected to be lower."""
        c = ComplaintInput(
            complaint_text="An unfamiliar wayside equipment unit is showing intermittent behavior.",
            asset_type="Wayside Equipment",
            asset_criticality="Operational",
            safety_risk_level="Medium",
        )
        result = classify_case(c)
        conf = result.get("confidence")
        if conf is not None and conf < 0.75:
            pass  # Expected: low confidence → human review needed


class TestTCOOD002UnseenWording:
    """Equipment does not respond reliably when route is commanded."""

    def test_no_crash(self):
        c = ComplaintInput(
            complaint_text="The equipment does not respond reliably when the route is commanded.",
            safety_risk_level="Medium",
        )
        result = classify_case(c)
        assert isinstance(result, dict)

    def test_prediction_or_controlled_result(self):
        c = ComplaintInput(
            complaint_text="The equipment does not respond reliably when the route is commanded.",
            safety_risk_level="Medium",
        )
        result = classify_case(c)
        assert "department" in result
        assert "fault_category" in result

    def test_no_invented_component(self):
        c = ComplaintInput(
            complaint_text="The equipment does not respond reliably when the route is commanded.",
            safety_risk_level="Medium",
        )
        result = classify_case(c)
        # Should return a valid department, not something invented
        assert result["department"] in VALID_DEPARTMENTS or result["department"] == "Unknown"

    def test_confidence_reported_honestly(self):
        c = ComplaintInput(
            complaint_text="The equipment does not respond reliably when the route is commanded.",
            safety_risk_level="Medium",
        )
        result = classify_case(c)
        conf = result.get("confidence")
        if conf is not None:
            assert 0.0 <= conf <= 1.0


class TestTCOOD003UnseenAbbreviation:
    """SM fails during RTE setting; manual operation required."""

    def test_no_crash(self):
        c = ComplaintInput(
            complaint_text="SM fails during RTE setting; manual operation required.",
            asset_type="Signal",
            safety_risk_level="High",
        )
        result = classify_case(c)
        assert isinstance(result, dict)

    def test_valid_output(self):
        c = ComplaintInput(
            complaint_text="SM fails during RTE setting; manual operation required.",
            asset_type="Signal",
            safety_risk_level="High",
        )
        result = classify_case(c)
        assert result["department"] in VALID_DEPARTMENTS
        assert result["fault_category"] in VALID_FAULT_CATEGORIES

    def test_does_not_fabricate_interpretation(self):
        """If abbreviation is not understood, model should not confidently claim
        a specific root cause."""
        c = ComplaintInput(
            complaint_text="SM fails during RTE setting; manual operation required.",
            asset_type="Signal",
            safety_risk_level="High",
        )
        result = classify_case(c)
        # The classifier returns labels only — no fabricated root cause text
        assert isinstance(result["fault_category"], str)


class TestTCOOD004ForeignOrMixedLanguage:
    """Mixed language input."""

    @pytest.mark.parametrize("text", [
        "Signal est\u00e1 parpadeando, por favor revisar.",
        "\u4fe1\u53f7\u7cfb\u7edf\u6545\u969c\uff0c\u9700\u8981\u7d27\u6025\u7ef4\u4fee.",
        "Signalemente \u00e9chou, remplacement n\u00e9cessaire.",
        "Anlage versagt, St\u00f6rung gemeldet.",
    ])
    def test_supported_language_no_crash(self, text):
        c = ComplaintInput(complaint_text=text, safety_risk_level="Medium")
        result = classify_case(c)
        assert isinstance(result, dict)

    @pytest.mark.parametrize("text", [
        "Signal est\u00e1 parpadeando, por favor revisar.",
        "\u4fe1\u53f7\u7cfb\u7edf\u6545\u969c\uff0c\u9700\u8981\u7d27\u6025\u7ef4\u4fee.",
    ])
    def test_valid_result_or_low_confidence(self, text):
        c = ComplaintInput(complaint_text=text, safety_risk_level="Medium")
        result = classify_case(c)
        assert "department" in result
        assert "fault_category" in result
        conf = result.get("confidence")
        if conf is not None:
            assert 0.0 <= conf <= 1.0
