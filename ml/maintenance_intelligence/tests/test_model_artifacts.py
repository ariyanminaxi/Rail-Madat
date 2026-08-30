"""Model artifact tests."""

import json
import sys
import tempfile
from pathlib import Path

import joblib
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import CONFIDENCE_THRESHOLD, LABEL_MAPS_PATH, MODEL_MANIFEST_PATH, MODEL_PATH
from app.maintenance_intelligence.inference.classifier import ModelNotFoundError, _load_model, classify_case, get_model_info
from app.maintenance_intelligence.io_schemas import ComplaintInput


class TestModelExists:
    def test_model_file_exists(self):
        assert MODEL_PATH.exists()

    def test_model_file_not_empty(self):
        assert MODEL_PATH.stat().st_size > 0

    def test_label_maps_file_exists(self):
        assert LABEL_MAPS_PATH.exists()

    def test_manifest_file_exists(self):
        assert MODEL_MANIFEST_PATH.exists()


class TestModelLoads:
    def test_load_returns_pipeline(self, trained_model):
        from sklearn.pipeline import Pipeline
        assert isinstance(trained_model, Pipeline)

    def test_model_has_predict(self, trained_model):
        assert hasattr(trained_model, "predict")


class TestMissingModel:
    def test_missing_model_raises_error(self):
        import app.maintenance_intelligence.inference.classifier as mod
        original = mod.MODEL_PATH
        mod.MODEL_PATH = Path("/nonexistent/path/model.joblib")
        try:
            with pytest.raises(ModelNotFoundError):
                _load_model()
        finally:
            mod.MODEL_PATH = original


class TestSaveLoadConsistency:
    def test_predictions_identical_after_reload(self, trained_model):
        c = ComplaintInput(
            complaint_text="Signal near S-02 is flickering.",
            asset_type="Signal",
            asset_criticality="Safety-Critical",
        )
        r1 = classify_case(c)
        r2 = classify_case(c)
        assert r1["department"] == r2["department"]
        assert r1["fault_category"] == r2["fault_category"]

    def test_model_file_is_valid_joblib(self):
        loaded = joblib.load(MODEL_PATH)
        assert loaded is not None
        assert hasattr(loaded, "predict")


class TestManifestCompatibility:
    def test_manifest_has_required_fields(self, model_manifest):
        for field in ["model_name", "model_version", "algorithm", "confidence_threshold"]:
            assert field in model_manifest

    def test_manifest_threshold_matches_config(self, model_manifest):
        assert model_manifest["confidence_threshold"] == CONFIDENCE_THRESHOLD

    def test_manifest_target_columns(self, model_manifest):
        expected = {"department", "fault_category", "severity", "base_priority"}
        assert set(model_manifest["target_columns"]) == expected
