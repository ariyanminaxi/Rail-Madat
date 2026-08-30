"""Validation Utilities — input sanitization and sensitive-data removal."""

SENSITIVE_KEYS = frozenset({
    "password", "access_token", "refresh_token",
    "secret_key", "jwt_secret", "api_key",
    "private_key", "credentials", "service_role_key",
    "secret", "token",
})


def validate_required_fields(data: dict, required: list[str]) -> list[str]:
    """Return a list of missing required field names (empty if all present)."""
    return [f for f in required if f not in data or data[f] is None]


def sanitize_sensitive_data(data: dict) -> dict:
    """Return a copy of *data* with sensitive values removed."""
    return {
        k: v for k, v in data.items()
        if k.lower() not in SENSITIVE_KEYS
    }


def is_valid_status(status: str, allowed: set[str]) -> bool:
    """Check that *status* is one of the allowed values."""
    return status in allowed


def is_valid_priority(priority: str) -> bool:
    """Check that *priority* is one of the recognised priorities."""
    return priority in {"Emergency", "Critical", "High", "Medium", "Low"}


def validate_log_status(status: str) -> bool:
    """Check that an audit-log status is valid."""
    return status in {"SUCCESS", "FAILED", "BLOCKED"}
