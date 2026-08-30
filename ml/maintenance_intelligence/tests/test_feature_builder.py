"""Feature builder tests."""

import sys
from pathlib import Path
import pandas as pd
import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import CATEGORICAL_FEATURES, NUMERIC_FEATURES, TEXT_COLUMN
from app.maintenance_intelligence.inference.feature_builder import FEATURE_COLUMNS, build_features, build_features_batch
from app.maintenance_intelligence.io_schemas import ComplaintInput


class TestValidCompleteContext:
    def test_build_features_succeeds(self, signal_complaint):
        df = build_features(signal_complaint)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1

    def test_all_required_fields_present(self, signal_complaint):
        df = build_features(signal_complaint)
        for col in FEATURE_COLUMNS:
            assert col in df.columns

    def test_field_names_match_feature_schema(self, signal_complaint, feature_schema):
        df = build_features(signal_complaint)
        schema_cols = [f["name"] for f in feature_schema["features"]]
        assert list(df.columns) == schema_cols

    def test_numeric_fields_are_numeric(self, signal_complaint):
        df = build_features(signal_complaint)
        assert df["days_overdue"].dtype in ("int64", "int32", "int")
        assert df["failure_count_30_days"].dtype in ("int64", "int32", "int")


class TestEmptyComplaintText:
    def test_empty_text_accepted(self):
        c = ComplaintInput(complaint_text="", asset_type="Signal")
        df = build_features(c)
        assert df[TEXT_COLUMN].iloc[0] == ""


class TestMissingComplaintText:
    def test_missing_text_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ComplaintInput()


class TestMissingAssetCriticality:
    def test_defaults_to_non_critical(self):
        c = ComplaintInput(complaint_text="Some fault")
        df = build_features(c)
        assert df["asset_criticality"].iloc[0] == "Non-Critical"


class TestUnknownAssetType:
    def test_none_asset_type_defaults_to_unknown(self):
        c = ComplaintInput(complaint_text="Something broke", asset_type=None)
        df = build_features(c)
        assert df["asset_type"].iloc[0] == "Unknown"

    def test_empty_string_preserved(self):
        """Empty string is now preserved (not silently converted to Unknown)."""
        c = ComplaintInput(complaint_text="Test", asset_type="")
        df = build_features(c)
        assert df["asset_type"].iloc[0] == ""


class TestInvalidStatus:
    def test_none_status_defaults_to_new(self):
        c = ComplaintInput(complaint_text="Fault", current_status=None)
        df = build_features(c)
        assert df["current_status"].iloc[0] == "New"


class TestStableFeatureOrder:
    def test_same_input_same_order(self, signal_complaint):
        df1 = build_features(signal_complaint)
        df2 = build_features(signal_complaint)
        assert list(df1.columns) == list(df2.columns)

    def test_feature_columns_constant(self):
        expected = [TEXT_COLUMN] + CATEGORICAL_FEATURES + NUMERIC_FEATURES
        assert FEATURE_COLUMNS == expected
        assert len(FEATURE_COLUMNS) == 8


class TestBatchFeatureBuilder:
    def test_batch_multiple(self):
        complaints = [
            ComplaintInput(complaint_text="Fault A"),
            ComplaintInput(complaint_text="Fault B"),
            ComplaintInput(complaint_text="Fault C"),
        ]
        df = build_features_batch(complaints)
        assert len(df) == 3
        assert list(df.columns) == FEATURE_COLUMNS
