"""Schema contract tests."""

import sys
from pathlib import Path
import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import VALID_DEPARTMENTS, VALID_FAULT_CATEGORIES, VALID_PRIORITIES, VALID_SEVERITIES
from app.maintenance_intelligence.io_schemas import ComplaintInput, ClassificationResult, ServiceOutput
from app.contracts.maintenance_prediction import MaintenancePrediction


class TestComplaintInputSchema:
    def test_valid_complaint(self):
        c = ComplaintInput(complaint_text="Fault")
        assert c.complaint_text == "Fault"

    def test_defaults_applied(self):
        c = ComplaintInput(complaint_text="Fault")
        assert c.asset_type == "Unknown"
        assert c.asset_criticality == "Non-Critical"
        assert c.current_status == "New"

    def test_missing_text_rejected(self):
        with pytest.raises(ValidationError):
            ComplaintInput()

    def test_rejects_invalid_type(self):
        with pytest.raises(ValidationError):
            ComplaintInput(complaint_text=123)


class TestMaintenancePredictionContract:
    def test_valid_prediction(self):
        p = MaintenancePrediction(
            department="Signalling", fault_category="Signal malfunction",
            severity="High", base_priority="High", final_priority="Critical",
            recommended_action="Immediate inspection required",
            confidence=0.91, human_review_required=True,
            explanation=["Asset is safety-critical"],
        )
        assert p.department == "Signalling"
        assert p.human_review_required is True

    def test_optional_confidence_none(self):
        p = MaintenancePrediction(
            department="Track", fault_category="Track defect",
            severity="Low", base_priority="Low", final_priority="Low",
            recommended_action="Routine", confidence=None,
            human_review_required=False, explanation=[],
        )
        assert p.confidence is None

    def test_human_review_is_bool(self):
        p = MaintenancePrediction(
            department="Track", fault_category="Track defect",
            severity="Low", base_priority="Low", final_priority="Low",
            recommended_action="Routine", confidence=0.9,
            human_review_required=True, explanation=[],
        )
        assert isinstance(p.human_review_required, bool)


class TestOutputFieldValidation:
    def test_department_is_valid_string(self, signal_complaint):
        from app.maintenance_intelligence.inference.classifier import classify_case
        result = classify_case(signal_complaint)
        assert isinstance(result["department"], str)
        assert len(result["department"]) > 0

    def test_severity_in_allowed_set(self, signal_complaint):
        from app.maintenance_intelligence.inference.classifier import classify_case
        result = classify_case(signal_complaint)
        assert result["severity"] in VALID_SEVERITIES

    def test_base_priority_in_allowed_set(self, signal_complaint):
        from app.maintenance_intelligence.inference.classifier import classify_case
        result = classify_case(signal_complaint)
        assert result["base_priority"] in VALID_PRIORITIES

    def test_emergency_requires_review(self):
        from app.maintenance_intelligence.prioritization.priority_engine import requires_human_review
        hr, _ = requires_human_review("Emergency", confidence=0.99, safety_risk="Extreme")
        assert hr is True
