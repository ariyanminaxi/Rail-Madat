"""
Tests for audit_logger.py — Audit event creation, validation,
sensitive-field removal, and repository integration.
"""

import pytest
from app.audit.audit_logger import (
    create_audit_log,
    record_audit_event,
    SENSITIVE_FIELDS,
    _sanitize_details,
)
from app.audit.audit_repository import AuditRepository


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _valid_kwargs():
    return dict(
        user_id="USER-001",
        role="manager",
        action="PRIORITY_ESCALATED",
        resource_type="maintenance_task",
        resource_id="T-001",
        status="SUCCESS",
    )


# ---------------------------------------------------------
# 1. Audit event creation
# ---------------------------------------------------------

def test_create_audit_log_returns_dict():
    event = create_audit_log(**_valid_kwargs())
    assert isinstance(event, dict)


def test_create_audit_log_has_all_required_fields():
    event = create_audit_log(**_valid_kwargs())
    required = {"log_id", "user_id", "role", "action",
                "resource_type", "resource_id", "timestamp", "status"}
    assert required.issubset(event.keys())


# ---------------------------------------------------------
# 2. ISO timestamp
# ---------------------------------------------------------

def test_timestamp_is_iso_format():
    event = create_audit_log(**_valid_kwargs())
    ts = event["timestamp"]
    assert "T" in ts
    assert "+" in ts or "Z" in ts


# ---------------------------------------------------------
# 3. Correct field values
# ---------------------------------------------------------

def test_correct_user_id():
    event = create_audit_log(**_valid_kwargs())
    assert event["user_id"] == "USER-001"


def test_correct_role():
    event = create_audit_log(**_valid_kwargs())
    assert event["role"] == "manager"


def test_correct_action():
    event = create_audit_log(**_valid_kwargs())
    assert event["action"] == "PRIORITY_ESCALATED"


def test_correct_resource():
    event = create_audit_log(**_valid_kwargs())
    assert event["resource_type"] == "maintenance_task"
    assert event["resource_id"] == "T-001"


# ---------------------------------------------------------
# 4. Sensitive-field removal
# ---------------------------------------------------------

def test_password_removed_from_details():
    details = {"password": "secret123", "action": "login"}
    event = create_audit_log(**_valid_kwargs(), details=details)
    assert "password" not in event.get("details", {})


def test_access_token_removed_from_details():
    details = {"access_token": "tok_abc", "user_id": "USR-001"}
    event = create_audit_log(**_valid_kwargs(), details=details)
    assert "access_token" not in event.get("details", {})
    assert event["details"]["user_id"] == "USR-001"


def test_all_sensitive_fields_removed():
    details = {field: "value" for field in SENSITIVE_FIELDS}
    details["safe_field"] = "keep_me"
    event = create_audit_log(**_valid_kwargs(), details=details)
    for field in SENSITIVE_FIELDS:
        assert field not in event.get("details", {})
    assert event["details"]["safe_field"] == "keep_me"


def test_string_details_preserved():
    event = create_audit_log(**_valid_kwargs(), details="Simple log message")
    assert event["details"] == "Simple log message"


def test_none_details_omitted():
    event = create_audit_log(**_valid_kwargs(), details=None)
    assert "details" not in event


# ---------------------------------------------------------
# 5. Invalid input handling
# ---------------------------------------------------------

def test_missing_user_id_raises():
    with pytest.raises(ValueError, match="user_id"):
        create_audit_log(user_id="", role="m", action="a",
                         resource_type="t", resource_id="r", status="SUCCESS")


def test_missing_role_raises():
    with pytest.raises(ValueError, match="role"):
        create_audit_log(user_id="u", role="", action="a",
                         resource_type="t", resource_id="r", status="SUCCESS")


def test_missing_action_raises():
    with pytest.raises(ValueError, match="action"):
        create_audit_log(user_id="u", role="r", action="",
                         resource_type="t", resource_id="r", status="SUCCESS")


def test_invalid_status_raises():
    with pytest.raises(ValueError, match="status"):
        create_audit_log(user_id="u", role="r", action="a",
                         resource_type="t", resource_id="r", status="INVALID")


# ---------------------------------------------------------
# 6. record_audit_event wrapper
# ---------------------------------------------------------

def test_record_audit_event_returns_event():
    event = record_audit_event(**_valid_kwargs())
    assert event["action"] == "PRIORITY_ESCALATED"
    assert event["resource_id"] == "T-001"
    assert "timestamp" in event


def test_record_audit_event_persists_to_repository():
    repo = AuditRepository()
    event = record_audit_event(**_valid_kwargs(), repository=repo)
    stored = repo.get_by_resource("maintenance_task", "T-001")
    assert len(stored) == 1
    assert stored[0]["log_id"] == event["log_id"]


# ---------------------------------------------------------
# 7. Append-only behavior
# ---------------------------------------------------------

def test_repository_is_append_only():
    repo = AuditRepository()
    e1 = record_audit_event(**_valid_kwargs(), repository=repo)
    e2 = record_audit_event(**_valid_kwargs(), repository=repo)

    events = repo.get_by_resource("maintenance_task", "T-001")
    assert len(events) == 2
    # Both should have different log_ids
    assert e1["log_id"] != e2["log_id"]


# ---------------------------------------------------------
# 8. Idempotency
# ---------------------------------------------------------

def test_duplicate_idempotency_key_rejected():
    repo = AuditRepository()
    record_audit_event(
        **_valid_kwargs(),
        idempotency_key="KEY-001",
        repository=repo,
    )
    with pytest.raises(ValueError, match="Duplicate"):
        record_audit_event(
            **_valid_kwargs(),
            idempotency_key="KEY-001",
            repository=repo,
        )


def test_idempotency_key_check():
    repo = AuditRepository()
    assert not repo.exists_by_idempotency_key("KEY-001")
    record_audit_event(
        **_valid_kwargs(),
        idempotency_key="KEY-001",
        repository=repo,
    )
    assert repo.exists_by_idempotency_key("KEY-001")


# ---------------------------------------------------------
# 9. Database failure simulation
# ---------------------------------------------------------

def test_repository_save_validates_required_fields():
    repo = AuditRepository()
    with pytest.raises(ValueError, match="missing required fields"):
        repo.save({"log_id": "L-1"})  # missing most fields
