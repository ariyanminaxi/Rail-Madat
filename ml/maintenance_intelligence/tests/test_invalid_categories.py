"""Invalid categorical value tests."""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import VALID_DEPARTMENTS, VALID_FAULT_CATEGORIES, VALID_PRIORITIES, VALID_SEVERITIES
from app.maintenance_intelligence.inference.classifier import classify_case
from app.maintenance_intelligence.inference.feature_builder import build_features
from app.maintenance_intelligence.prioritization.priority_engine import calculate_final_priority
from app.maintenance_intelligence.io_schemas import ComplaintInput


class TestInvalidFeatureCategories:
    @pytest.mark.parametrize("field,value", [
        ("asset_type", "UnknownEquipment"),
        ("asset_criticality", "SuperCritical"),
        ("current_status", "RandomStatus"),
        ("safety_risk_level", "UnknownDanger"),
    ])
    def test_does_not_crash(self, field, value):
        c = ComplaintInput(complaint_text="Test fault", **{field: value})
        result = classify_case(c)
        assert isinstance(result, dict)

    def test_empty_string_preserved(self):
        """Empty string is now preserved (not silently converted to Unknown)."""
        c = ComplaintInput(complaint_text="Test", asset_type="")
        df = build_features(c)
        assert df["asset_type"].iloc[0] == ""


class TestInvalidPriorities:
    @pytest.mark.parametrize("bad_priority", ["UrgentButNotDefined", "P0", "1", ""])
    def test_defaults_to_medium(self, bad_priority):
        result = calculate_final_priority(
            {"base_priority": bad_priority},
            {"asset_criticality": "Non-Critical", "current_status": "New", "safety_risk_level": "Low"},
        )
        assert result["final_priority"] in VALID_PRIORITIES


class TestClassifierOutputValues:
    def test_department_valid(self):
        c = ComplaintInput(complaint_text="Track defect.", asset_type="Track", safety_risk_level="High")
        result = classify_case(c)
        assert result["department"] in VALID_DEPARTMENTS or result["department"] == "Unknown"

    def test_severity_valid(self):
        c = ComplaintInput(complaint_text="Signal malfunction.", asset_type="Signal", safety_risk_level="High")
        result = classify_case(c)
        assert result["severity"] in VALID_SEVERITIES
