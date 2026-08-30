"""Report Serializer — JSON serialization and validation for reports."""

import json
from datetime import datetime, timezone


def validate_report(report: dict) -> bool:
    """Validate that a report contains required fields."""
    required_fields = ["report_id", "report_type", "created_at"]
    return all(field in report and report[field] for field in required_fields)


def serialize_report(report: dict) -> str:
    """Serialize a report to JSON string, handling datetime objects."""
    def _default(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    return json.dumps(report, default=_default, indent=2)


def deserialize_report(json_str: str) -> dict:
    """Deserialize a report from JSON string."""
    return json.loads(json_str)


def sanitize_report(report: dict) -> dict:
    """Remove sensitive fields from a report before storage or display."""
    sensitive_keys = {
        "password", "access_token", "refresh_token",
        "secret_key", "jwt_secret", "api_key",
        "private_key", "credentials",
    }
    return {
        k: v for k, v in report.items()
        if k.lower() not in sensitive_keys
    }
