"""Missing and null input tests."""

import sys
from pathlib import Path
import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.inference.classifier import classify_case
from app.maintenance_intelligence.inference.feature_builder import build_features
from app.maintenance_intelligence.prioritization.priority_engine import calculate_final_priority
from app.maintenance_intelligence.io_schemas import ComplaintInput


class TestTCMissing001:
    def test_missing_complaint_text_raises_error(self):
        with pytest.raises(ValidationError):
            ComplaintInput(asset_type="Signal")


class TestTCMissing002:
    def test_empty_string_classifies(self):
        c = ComplaintInput(complaint_text="", asset_type="Signal")
        result = classify_case(c)
        assert isinstance(result, dict)


class TestTCMissing003:
    def test_whitespace_only_classifies(self):
        c = ComplaintInput(complaint_text="     ")
        result = classify_case(c)
        assert isinstance(result, dict)


class TestTCMissing004:
    def test_defaults_to_unknown(self):
        c = ComplaintInput(complaint_text="Fault")
        assert c.asset_type == "Unknown"


class TestTCMissing005:
    def test_defaults_to_non_critical(self):
        c = ComplaintInput(complaint_text="Fault")
        assert c.asset_criticality == "Non-Critical"


class TestTCMissing006:
    def test_defaults_to_new(self):
        c = ComplaintInput(complaint_text="Fault")
        assert c.current_status == "New"


class TestTCMissing007:
    def test_null_history_defaults_to_zero(self):
        c = ComplaintInput(complaint_text="Fault", days_overdue=None, failure_count_30_days=None)
        df = build_features(c)
        assert df["days_overdue"].iloc[0] == 0
        assert df["failure_count_30_days"].iloc[0] == 0


class TestTCMissing008:
    def test_minimal_input_no_exception(self):
        c = ComplaintInput(complaint_text="Equipment is not working.")
        result = classify_case(c)
        assert isinstance(result, dict)
