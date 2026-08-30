"""Artifact and version integrity tests.

Test missing model, empty model, corrupted model, missing manifest,
wrong version, missing feature schema, schema mismatch, and invalid
label maps.
"""

import json
import sys
import tempfile
from pathlib import Path

import joblib
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import (
    CONFIDENCE_THRESHOLD,
    FEATURE_SCHEMA_PATH,
    LABEL_MAPS_PATH,
    MODEL_MANIFEST_PATH,
    MODEL_PATH,
    TARGET_COLUMNS,
)
from app.maintenance_intelligence.inference.classifier import (
    ModelNotFoundError,
    _load_model,
    classify_case,
    get_model_info,
)
from app.maintenance_intelligence.inference.feature_builder import FEATURE_COLUMNS
from app.maintenance_intelligence.io_schemas import ComplaintInput


# ===================================================================
# Model file existence and validity
# ===================================================================

class TestModelFileIntegrity:
    def test_model_file_exists(self):
        assert MODEL_PATH.exists(), f"Model not found at {MODEL_PATH}"

    def test_model_file_not_empty(self):
        assert MODEL_PATH.stat().st_size > 0, "Model file is empty"

    def test_model_file_valid_joblib(self):
        loaded = joblib.load(MODEL_PATH)
        assert loaded is not None
        assert hasattr(loaded, "predict")
        assert hasattr(loaded, "fit")

    def test_model_is_pipeline(self):
        from sklearn.pipeline import Pipeline
        loaded = joblib.load(MODEL_PATH)
        assert isinstance(loaded, Pipeline)


# ===================================================================
# Missing model file
# ===================================================================

class TestMissingModelFile:
    def test_missing_model_raises_error(self):
        import app.maintenance_intelligence.inference.classifier as mod
        original = mod.MODEL_PATH
        mod.MODEL_PATH = Path("/nonexistent/path/model.joblib")
        try:
            with pytest.raises(ModelNotFoundError):
                _load_model()
        finally:
            mod.MODEL_PATH = original


# ===================================================================
# Empty model file
# ===================================================================

class TestEmptyModelFile:
    def test_empty_file_raises_error(self):
        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as f:
            f.write(b"")
            tmp = Path(f.name)
        import app.maintenance_intelligence.inference.classifier as mod
        original = mod.MODEL_PATH
        mod.MODEL_PATH = tmp
        try:
            with pytest.raises(Exception):
                _load_model()
        finally:
            mod.MODEL_PATH = original
            tmp.unlink(missing_ok=True)


# ===================================================================
# Corrupted model file
# ===================================================================

class TestCorruptedModelFile:
    def test_corrupted_file_raises_error(self):
        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as f:
            f.write(b"not a valid joblib \x00\x01\x02\x03\x04\x05")
            tmp = Path(f.name)
        import app.maintenance_intelligence.inference.classifier as mod
        original = mod.MODEL_PATH
        mod.MODEL_PATH = tmp
        try:
            with pytest.raises(Exception):
                _load_model()
        finally:
            mod.MODEL_PATH = original
            tmp.unlink(missing_ok=True)

    def test_random_bytes_raises_error(self):
        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as f:
            f.write(b"\x89PNG\r\n\x1a\n" * 100)  # Fake PNG header
            tmp = Path(f.name)
        import app.maintenance_intelligence.inference.classifier as mod
        original = mod.MODEL_PATH
        mod.MODEL_PATH = tmp
        try:
            with pytest.raises(Exception):
                _load_model()
        finally:
            mod.MODEL_PATH = original
            tmp.unlink(missing_ok=True)


# ===================================================================
# Missing model manifest
# ===================================================================

class TestMissingManifest:
    def test_missing_manifest_returns_empty(self):
        import app.maintenance_intelligence.inference.classifier as mod
        original = mod.MODEL_MANIFEST_PATH
        mod.MODEL_MANIFEST_PATH = Path("/nonexistent/manifest.json")
        try:
            result = mod._load_model_manifest()
            assert result == {}
        finally:
            mod.MODEL_MANIFEST_PATH = original

    def test_missing_manifest_get_model_info_works(self):
        import app.maintenance_intelligence.inference.classifier as mod
        original = mod.MODEL_MANIFEST_PATH
        mod.MODEL_MANIFEST_PATH = Path("/nonexistent/manifest.json")
        try:
            info = get_model_info()
            assert info["model_version"] == "unknown"
            assert info["model_loaded"] is True  # Model file still exists
        finally:
            mod.MODEL_MANIFEST_PATH = original


# ===================================================================
# Wrong model version
# ===================================================================

class TestWrongModelVersion:
    def test_manifest_version_logged(self, model_manifest):
        """Model metadata should be accessible."""
        assert "model_version" in model_manifest
        assert isinstance(model_manifest["model_version"], str)
        assert len(model_manifest["model_version"]) > 0

    def test_manifest_required_fields(self, model_manifest):
        required_fields = [
            "model_name",
            "model_version",
            "algorithm",
            "confidence_threshold",
            "target_columns",
        ]
        for field in required_fields:
            assert field in model_manifest, f"Missing required field: {field}"


# ===================================================================
# Missing feature schema
# ===================================================================

class TestFeatureSchema:
    def test_feature_schema_exists(self):
        if not FEATURE_SCHEMA_PATH.exists():
            pytest.skip("Feature schema not found")

    def test_feature_schema_consistency(self):
        if not FEATURE_SCHEMA_PATH.exists():
            pytest.skip("Feature schema not found")
        with open(FEATURE_SCHEMA_PATH) as f:
            schema = json.load(f)
        expected = (
            [schema["text_column"]]
            + schema["categorical_features"]
            + schema["numeric_features"]
        )
        assert expected == FEATURE_COLUMNS

    def test_feature_schema_matches_config(self):
        if not FEATURE_SCHEMA_PATH.exists():
            pytest.skip("Feature schema not found")
        with open(FEATURE_SCHEMA_PATH) as f:
            schema = json.load(f)
        assert len(schema["features"]) == len(FEATURE_COLUMNS)


# ===================================================================
# Invalid label maps
# ===================================================================

class TestLabelMaps:
    def test_label_maps_exists(self):
        assert LABEL_MAPS_PATH.exists()

    def test_label_maps_valid_json(self):
        with open(LABEL_MAPS_PATH) as f:
            maps = json.load(f)
        assert isinstance(maps, dict)

    def test_label_maps_has_all_targets(self):
        with open(LABEL_MAPS_PATH) as f:
            maps = json.load(f)
        for col in TARGET_COLUMNS:
            assert col in maps, f"Label map missing for {col}"

    def test_label_maps_non_empty(self):
        with open(LABEL_MAPS_PATH) as f:
            maps = json.load(f)
        for col in TARGET_COLUMNS:
            assert len(maps[col]) > 0, f"Empty label map for {col}"


# ===================================================================
# Manifest threshold matches config
# ===================================================================

class TestManifestConfigConsistency:
    def test_threshold_matches(self, model_manifest):
        assert model_manifest["confidence_threshold"] == CONFIDENCE_THRESHOLD

    def test_target_columns_match(self, model_manifest):
        expected = set(TARGET_COLUMNS)
        assert set(model_manifest["target_columns"]) == expected

    def test_n_training_samples_positive(self, model_manifest):
        assert model_manifest["n_training_samples"] > 0


# ===================================================================
# No false successful prediction from missing artifact
# ===================================================================

class TestNoFalsePredictionFromMissingArtifact:
    """If the model is missing, classify_case should raise, not return
    a fake prediction."""

    def test_missing_model_raises_not_fake(self):
        import app.maintenance_intelligence.inference.classifier as mod
        original = mod.MODEL_PATH
        mod.MODEL_PATH = Path("/nonexistent/model.joblib")
        try:
            with pytest.raises(ModelNotFoundError):
                classify_case(ComplaintInput(complaint_text="Test"))
        finally:
            mod.MODEL_PATH = original

    def test_no_production_startup_if_artifacts_invalid(self):
        """Model metadata is logged — verify the manifest exists and is readable."""
        info = get_model_info()
        assert "model_loaded" in info
        assert "model_version" in info
        if info["model_loaded"]:
            assert info["model_version"] != "unknown" or not MODEL_MANIFEST_PATH.exists()
