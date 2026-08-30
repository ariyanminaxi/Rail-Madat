"""Model loading utilities for the Maintenance Intelligence Service."""

import json
from pathlib import Path

import joblib

from app.maintenance_intelligence.config import (
    LABEL_MAPS_PATH,
    MODEL_MANIFEST_PATH,
    MODEL_PATH,
)


class ModelNotFoundError(Exception):
    """Raised when the trained model artifact is missing."""
    pass


def load_model():
    """Load the trained pipeline from the model artifacts directory."""
    if not MODEL_PATH.exists():
        raise ModelNotFoundError(
            f"Trained model artifact not found at {MODEL_PATH}. "
            "Please run training first:\n"
            "  python -m ml.maintenance_intelligence.training.train_classifier"
        )
    return joblib.load(MODEL_PATH)


def load_label_maps() -> dict:
    """Load the label mappings from JSON."""
    if not LABEL_MAPS_PATH.exists():
        return {}
    with open(LABEL_MAPS_PATH) as f:
        return json.load(f)


def load_model_manifest() -> dict:
    """Load the model manifest."""
    if not MODEL_MANIFEST_PATH.exists():
        return {}
    with open(MODEL_MANIFEST_PATH) as f:
        return json.load(f)


def get_model_info() -> dict:
    """Return metadata about the loaded model."""
    manifest = load_model_manifest()
    return {
        "model_loaded": MODEL_PATH.exists(),
        "model_version": manifest.get("model_version", "unknown"),
        "trained_at": manifest.get("trained_at", "unknown"),
        "confidence_threshold": manifest.get("confidence_threshold", 0.75),
    }
