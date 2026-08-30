"""Confidence threshold checking for Maintenance Intelligence predictions."""

from typing import Optional

from app.maintenance_intelligence.config import CONFIDENCE_THRESHOLD


def check_confidence(
    confidence: Optional[float],
    threshold: float = CONFIDENCE_THRESHOLD,
) -> dict:
    """Check whether the prediction confidence meets the threshold.

    Validates that confidence is within [0, 1] or None.
    """
    if confidence is None:
        return {
            "is_confident": False,
            "confidence": None,
            "threshold": threshold,
            "human_review_required": True,
            "message": "Confidence score unavailable — human review required",
        }

    # Validate confidence range
    if confidence < 0.0 or confidence > 1.0:
        return {
            "is_confident": False,
            "confidence": confidence,
            "threshold": threshold,
            "human_review_required": True,
            "message": f"Confidence {confidence:.2f} is outside valid range [0, 1] — human review required",
        }

    is_confident = confidence >= threshold

    if is_confident:
        message = f"Confidence {confidence:.2f} meets threshold {threshold}"
    else:
        message = (
            f"Confidence {confidence:.2f} is below threshold {threshold} "
            f"— human review recommended"
        )

    return {
        "is_confident": is_confident,
        "confidence": confidence,
        "threshold": threshold,
        "human_review_required": not is_confident,
        "message": message,
    }


def get_confidence_level(confidence: Optional[float]) -> str:
    """Return a human-readable confidence level label."""
    if confidence is None:
        return "Unknown"
    if confidence < 0.0 or confidence > 1.0:
        return "Invalid"
    if confidence >= 0.9:
        return "High"
    elif confidence >= 0.75:
        return "Medium"
    elif confidence >= 0.5:
        return "Low"
    else:
        return "Very Low"
