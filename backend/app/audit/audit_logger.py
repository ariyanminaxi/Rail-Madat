"""
RailMaintain - Audit Logger

Records important system actions for traceability and security testing.
"""

from datetime import datetime, timezone
from typing import Optional


# Sensitive fields that must never appear in audit details
SENSITIVE_FIELDS = frozenset({
    "password", "access_token", "refresh_token",
    "secret", "secret_key", "private_key", "api_key",
    "credential", "token", "passphrase",
})


def _sanitize_details(details):
    """Remove sensitive fields from audit details."""
    if details is None:
        return None
    if isinstance(details, str):
        return details
    if isinstance(details, dict):
        return {
            k: v for k, v in details.items()
            if k.lower() not in SENSITIVE_FIELDS
        }
    if isinstance(details, list):
        return [_sanitize_details(item) for item in details]
    return details


def create_audit_log(
    user_id: str,
    role: str,
    action: str,
    resource_type: str,
    resource_id: str,
    status: str,
    details=None,
) -> dict:
    """
    Create one audit-log entry.

    Required fields:
    log_id, user_id, role, action, resource_type,
    resource_id, timestamp, status
    """

    if not user_id:
        raise ValueError("user_id is required")

    if not role:
        raise ValueError("role is required")

    if not action:
        raise ValueError("action is required")

    if not resource_type:
        raise ValueError("resource_type is required")

    if not resource_id:
        raise ValueError("resource_id is required")

    if status not in {"SUCCESS", "FAILED", "BLOCKED"}:
        raise ValueError(
            "status must be SUCCESS, FAILED, or BLOCKED"
        )

    timestamp = datetime.now(timezone.utc).isoformat()

    log_id = f"LOG-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"

    log = {
        "log_id": log_id,
        "user_id": user_id,
        "role": role,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "timestamp": timestamp,
        "status": status,
    }

    sanitized = _sanitize_details(details)
    if sanitized is not None:
        log["details"] = sanitized

    return log


def record_audit_event(
    user_id,
    role,
    action,
    resource_type,
    resource_id,
    status,
    details=None,
    idempotency_key=None,
    repository=None,
):
    """Create and persist an audit event.

    Provides the interface expected by the MVP integration spec
    while preserving the existing create_audit_log function name.

    If a repository is provided (or the default singleton is used),
    the event is persisted. Otherwise it is returned without persistence
    (backward-compatible with callers that don't use a repository).
    """
    event = create_audit_log(
        user_id=user_id,
        role=role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        status=status,
        details=details,
    )

    if idempotency_key:
        event["idempotency_key"] = idempotency_key

    repo = repository
    if repo is None:
        from .audit_repository import get_audit_repository
        repo = get_audit_repository()

    repo.save(event)
    return event


if __name__ == "__main__":
    import json

    sample = create_audit_log(
        user_id="USR-001",
        role="MAINTENANCE_MANAGER",
        action="APPROVAL_REQUESTED",
        resource_type="maintenance_block",
        resource_id="B-301",
        status="SUCCESS",
        details="Recommended block sent for human approval.",
    )

    print(json.dumps(sample, indent=2))
