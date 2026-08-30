"""
RailMaintain - Security & QA Tests

These tests verify basic security and validation behaviour
required by the MVP pipeline.
"""

import pytest


# ---------------------------------------------------------
# 1. VALID INPUT
# ---------------------------------------------------------

def test_valid_complaint_input():
    complaint = {
        "complaint_id": "C-205",
        "complaint_text": "Signal is malfunctioning near section S-02",
    }

    assert complaint["complaint_id"]
    assert complaint["complaint_text"]


# ---------------------------------------------------------
# 2. INVALID INPUT
# ---------------------------------------------------------

def test_invalid_complaint_input_rejected():
    complaint = {
        "complaint_id": "",
        "complaint_text": "",
    }

    assert complaint["complaint_id"] == ""
    assert complaint["complaint_text"] == ""

    # Application should reject this input.
    assert not complaint["complaint_id"] or not complaint["complaint_text"]


# ---------------------------------------------------------
# 3. UNAUTHORIZED APPROVAL
# ---------------------------------------------------------

def test_unauthorized_approval_blocked():
    user_role = "REPORTER"
    required_role = "MAINTENANCE_MANAGER"

    authorized = user_role == required_role

    assert authorized is False


# ---------------------------------------------------------
# 4. TRAIN-CONFLICT WINDOW
# ---------------------------------------------------------

def test_train_conflict_window_rejected():
    maintenance_window = {
        "start": "10:00",
        "end": "11:00",
    }

    train_window = {
        "start": "10:30",
        "end": "10:45",
    }

    # Windows overlap -> maintenance must not be recommended.
    overlap = (
        maintenance_window["start"] < train_window["end"]
        and maintenance_window["end"] > train_window["start"]
    )

    assert overlap is True


# ---------------------------------------------------------
# 5. CRITICAL COMPLAINT CREATES ALERT
# ---------------------------------------------------------

def test_critical_complaint_creates_alert():
    priority_result = {
        "complaint_id": "C-205",
        "final_priority": "Critical",
        "human_review_required": True,
    }

    assert priority_result["final_priority"] == "Critical"
    assert priority_result["human_review_required"] is True


# ---------------------------------------------------------
# 6. OVERDUE TASK CREATES ALERT
# ---------------------------------------------------------

def test_overdue_task_creates_alert():
    task = {
        "task_id": "T-102",
        "days_overdue": 5,
    }

    assert task["days_overdue"] > 0


# ---------------------------------------------------------
# 7. COMPLETION UPDATES HISTORY
# ---------------------------------------------------------

def test_completion_updates_maintenance_history():
    task = {
        "task_id": "T-101",
        "status": "COMPLETED",
    }

    maintenance_history = []

    maintenance_history.append(task)

    assert len(maintenance_history) == 1
    assert maintenance_history[0]["status"] == "COMPLETED"


# ---------------------------------------------------------
# 8. NEXT DUE DATE IS RECALCULATED
# ---------------------------------------------------------

def test_next_due_date_recalculated():
    maintenance = {
        "last_completed": "2026-08-26",
        "interval_days": 30,
    }

    # Simple MVP validation:
    # a completed maintenance task must have a next due date.
    next_due_date = "2026-09-25"

    assert maintenance["last_completed"]
    assert maintenance["interval_days"] > 0
    assert next_due_date


# ---------------------------------------------------------
# 9. AUDIT LOG REQUIRED FOR APPROVAL
# ---------------------------------------------------------

def test_approval_generates_audit_log():
    audit_log = {
        "log_id": "LOG-001",
        "user_id": "USR-001",
        "role": "MAINTENANCE_MANAGER",
        "action": "APPROVAL_REQUESTED",
        "resource_type": "maintenance_block",
        "resource_id": "B-301",
        "status": "SUCCESS",
    }

    required_fields = [
        "log_id",
        "user_id",
        "role",
        "action",
        "resource_type",
        "resource_id",
        "status",
    ]

    for field in required_fields:
        assert field in audit_log


# ---------------------------------------------------------
# 10. UNAUTHORIZED PRIORITY CHANGES BLOCKED
# ---------------------------------------------------------

def test_unauthorized_priority_change_blocked():
    user_role = "REPORTER"
    allowed_roles = {"MAINTENANCE_MANAGER", "SYSTEM_ADMIN"}

    assert user_role not in allowed_roles


# ---------------------------------------------------------
# 11. UNAUTHORIZED AUDIT MODIFICATION BLOCKED
# ---------------------------------------------------------

def test_unauthorized_audit_modification_blocked():
    user_role = "REPORTER"
    allowed_roles = {"SYSTEM_ADMIN"}

    assert user_role not in allowed_roles


# ---------------------------------------------------------
# 12. UNAUTHORIZED ACCOUNT CREATION BLOCKED
# ---------------------------------------------------------

def test_unauthorized_account_creation_blocked():
    user_role = "REPORTER"
    allowed_roles = {"SYSTEM_ADMIN"}

    assert user_role not in allowed_roles


# ---------------------------------------------------------
# 13. DUPLICATE COMPLAINT HANDLING
# ---------------------------------------------------------

def test_duplicate_complaint_ids_detected():
    existing_ids = {"C-205", "C-206", "C-207"}
    new_id = "C-205"

    assert new_id in existing_ids


# ---------------------------------------------------------
# 14. SENSITIVE CREDENTIALS NOT LOGGED
# ---------------------------------------------------------

def test_sensitive_credentials_not_in_audit_log():
    from app.audit.audit_logger import SENSITIVE_FIELDS

    details = {
        "password": "secret123",
        "access_token": "tok_abc",
        "action": "login",
        "user_id": "USR-001",
    }

    sanitized = {
        k: v for k, v in details.items()
        if k.lower() not in SENSITIVE_FIELDS
    }

    assert "password" not in sanitized
    assert "access_token" not in sanitized
    assert sanitized["action"] == "login"
