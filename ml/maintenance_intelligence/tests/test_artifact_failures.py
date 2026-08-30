"""Model artifact failure tests."""

import json
import sys
import tempfile
from pathlib import Path

import joblib
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import MODEL_PATH, MODEL_MANIFEST_PATH
from app.maintenance_intelligence.inference.classifier import ModelNotFoundError, _load_model, classify_case, get_model_info
from app.maintenance_intelligence.io_schemas import ComplaintInput


class TestTCArtifact001:
    def test_missing_model_raises_error(self):
        import app.maintenance_intelligence.inference.classifier as mod
        original = mod.MODEL_PATH
        mod.MODEL_PATH = Path("/nonexistent/path/model.joblib")
        try:
            with pytest.raises(ModelNotFoundError):
                _load_model()
        finally:
            mod.MODEL_PATH = original


class TestTCArtifact002:
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


class TestTCArtifact003:
    def test_corrupted_file_raises_error(self):
        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as f:
            f.write(b"not a valid joblib \x00\x01\x02")
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


class TestTCArtifact004:
    def test_missing_manifest_returns_empty(self):
        import app.maintenance_intelligence.inference.classifier as mod
        original = mod.MODEL_MANIFEST_PATH
        mod.MODEL_MANIFEST_PATH = Path("/nonexistent/manifest.json")
        try:
            assert mod._load_model_manifest() == {}
        finally:
            mod.MODEL_MANIFEST_PATH = original


class TestTCArtifact005:
    def test_schema_consistency(self):
        from app.maintenance_intelligence.config import FEATURE_SCHEMA_PATH
        from app.maintenance_intelligence.inference.feature_builder import FEATURE_COLUMNS
        if FEATURE_SCHEMA_PATH.exists():
            with open(FEATURE_SCHEMA_PATH) as f:
                schema = json.load(f)
            expected = [schema["text_column"]] + schema["categorical_features"] + schema["numeric_features"]
            assert expected == FEATURE_COLUMNS


class TestTCArtifact007:
    def test_predictions_identical(self):
        if not MODEL_PATH.exists():
            pytest.skip("Model not found")
        c = ComplaintInput(complaint_text="Signal near S-02 is flickering.", asset_type="Signal",
                           asset_criticality="Safety-Critical", safety_risk_level="High")
        r1 = classify_case(c)
        r2 = classify_case(c)
        assert r1["department"] == r2["department"]
        assert r1["base_priority"] == r2["base_priority"]
