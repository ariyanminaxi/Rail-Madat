"""Classifier behaviour tests."""

import sys
from pathlib import Path
import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import (
    VALID_DEPARTMENTS, VALID_FAULT_CATEGORIES, VALID_PRIORITIES, VALID_SEVERITIES,
)
from app.maintenance_intelligence.inference.classifier import (
    ModelNotFoundError, ClassificationError, classify_case, get_model_info,
)
from app.maintenance_intelligence.io_schemas import ComplaintInput


class TestSignalMalfunction:
    def test_returns_prediction(self, signal_complaint):
        result = classify_case(signal_complaint)
        assert isinstance(result, dict)

    def test_department_is_valid(self, signal_complaint):
        result = classify_case(signal_complaint)
        assert result["department"] in VALID_DEPARTMENTS

    def test_fault_category_is_valid(self, signal_complaint):
        result = classify_case(signal_complaint)
        assert result["fault_category"] in VALID_FAULT_CATEGORIES

    def test_severity_is_valid(self, signal_complaint):
        result = classify_case(signal_complaint)
        assert result["severity"] in VALID_SEVERITIES

    def test_priority_is_valid(self, signal_complaint):
        result = classify_case(signal_complaint)
        assert result["base_priority"] in VALID_PRIORITIES

    def test_confidence_in_range(self, signal_complaint):
        result = classify_case(signal_complaint)
        c = result["confidence"]
        assert c is None or (0.0 <= c <= 1.0)

    def test_signal_input_likely_signalling(self, signal_complaint):
        result = classify_case(signal_complaint)
        assert result["department"] == "Signalling"


class TestAmbiguousComplaint:
    def test_does_not_crash(self, ambiguous_complaint):
        result = classify_case(ambiguous_complaint)
        assert isinstance(result, dict)

    def test_short_text_valid(self, ambiguous_complaint):
        result = classify_case(ambiguous_complaint)
        assert "department" in result


class TestSpellingErrors:
    def test_does_not_crash(self):
        c = ComplaintInput(complaint_text="Signal is flikering near S-02.")
        result = classify_case(c)
        assert isinstance(result, dict)


class TestShortComplaint:
    def test_does_not_crash(self):
        c = ComplaintInput(complaint_text="Track crack.")
        result = classify_case(c)
        assert isinstance(result, dict)


class TestUnknownWording:
    def test_no_unhandled_exception(self):
        c = ComplaintInput(complaint_text="Unexpected irregular behavior observed in field equipment.")
        result = classify_case(c)
        assert isinstance(result, dict)


class TestEmptyModelInput:
    def test_missing_complaint_text_raises_validation(self):
        with pytest.raises(ValidationError):
            ComplaintInput()

    def test_empty_string_text_accepted(self):
        c = ComplaintInput(complaint_text="")
        result = classify_case(c)
        assert isinstance(result, dict)


class TestInvalidFieldValues:
    @pytest.mark.parametrize("field,value", [
        ("asset_criticality", "InvalidLevel"),
        ("current_status", "BogusStatus"),
        ("safety_risk_level", "Catastrophic"),
        ("service_impact_level", "Catastrophic"),
    ])
    def test_unsupported_values_handled(self, field, value):
        c = ComplaintInput(complaint_text="Test fault", **{field: value})
        result = classify_case(c)
        assert isinstance(result, dict)


class TestClassifierInterface:
    def test_get_model_info(self):
        info = get_model_info()
        assert "model_loaded" in info
        assert "model_version" in info

    def test_classify_case_returns_dict(self, signal_complaint):
        result = classify_case(signal_complaint)
        assert isinstance(result, dict)
