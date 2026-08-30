"""
Tests for notification_rules.py — Deterministic alert generation
for all MVP notification types.
"""

import pytest
from app.notifications.notification_rules import (
    critical_complaint_notification,
    upcoming_maintenance_notification,
    overdue_maintenance_notification,
    approval_pending_notification,
    failed_sync_notification,
    emergency_notification,
    incomplete_work_notification,
    materials_unavailable_notification,
    human_verification_notification,
    team_reassignment_notification,
    resource_failure_notification,
    CRITICAL_COMPLAINT,
    UPCOMING_MAINTENANCE,
    OVERDUE_MAINTENANCE,
    APPROVAL_PENDING,
    FAILED_SYNC,
    EMERGENCY,
    INCOMPLETE_WORK,
    MATERIALS_UNAVAILABLE,
    HUMAN_VERIFICATION_PENDING,
    TEAM_REASSIGNED,
    RESOURCE_FAILURE,
    CRITICAL_TASK,
    EMERGENCY_TASK,
    HUMAN_REVIEW_REQUIRED,
    WORK_INTERRUPTED,
    TASK_REQUEUED,
    RESOURCE_UNAVAILABLE,
    BUNDLE_INVALIDATED,
    SCHEDULING_APPROVAL_REQUIRED,
)


# ---------------------------------------------------------
# 1. Critical complaint
# ---------------------------------------------------------

def test_critical_complaint_creates_notification():
    result = critical_complaint_notification({
        "complaint_id": "C-205",
        "final_priority": "Critical",
        "suggested_action": "Immediate inspection",
        "human_review_required": True,
    })
    assert result is not None
    assert result["notification_type"] == CRITICAL_COMPLAINT
    assert result["priority"] == "Critical"
    assert "C-205" in result["message"]


def test_non_critical_complaint_returns_none():
    result = critical_complaint_notification({
        "complaint_id": "C-206",
        "final_priority": "High",
    })
    assert result is None


# ---------------------------------------------------------
# 2. Upcoming maintenance
# ---------------------------------------------------------

def test_upcoming_maintenance_creates_notification():
    result = upcoming_maintenance_notification(
        {"task_id": "T-101", "asset_id": "SIG-S02-04"},
        days_until_due=3,
    )
    assert result is not None
    assert result["notification_type"] == UPCOMING_MAINTENANCE
    assert "T-101" in result["message"]


def test_upcoming_maintenance_out_of_range_returns_none():
    result = upcoming_maintenance_notification(
        {"task_id": "T-101"},
        days_until_due=10,
    )
    assert result is None


def test_upcoming_maintenance_negative_days_returns_none():
    result = upcoming_maintenance_notification(
        {"task_id": "T-101"},
        days_until_due=-1,
    )
    assert result is None


# ---------------------------------------------------------
# 3. Overdue maintenance
# ---------------------------------------------------------

def test_overdue_maintenance_creates_notification():
    result = overdue_maintenance_notification({
        "task_id": "T-102",
        "asset_id": "TRK-S01-02",
        "days_overdue": 5,
    })
    assert result is not None
    assert result["notification_type"] == OVERDUE_MAINTENANCE
    assert "5 day(s)" in result["message"]


def test_overdue_maintenance_not_overdue_returns_none():
    result = overdue_maintenance_notification({
        "task_id": "T-102",
        "days_overdue": 0,
    })
    assert result is None


# ---------------------------------------------------------
# 4. Approval pending
# ---------------------------------------------------------

def test_approval_pending_creates_notification():
    result = approval_pending_notification({
        "block_id": "B-301",
        "status": "PENDING_APPROVAL",
    })
    assert result is not None
    assert result["notification_type"] == APPROVAL_PENDING
    assert result["human_approval_required"] is True


def test_approval_pending_wrong_status_returns_none():
    result = approval_pending_notification({
        "block_id": "B-301",
        "status": "APPROVED",
    })
    assert result is None


# ---------------------------------------------------------
# 5. Failed sync
# ---------------------------------------------------------

def test_failed_sync_creates_notification():
    result = failed_sync_notification("EQ-05")
    assert result["notification_type"] == FAILED_SYNC
    assert result["resource_id"] == "EQ-05"


# ---------------------------------------------------------
# 6. Emergency
# ---------------------------------------------------------

def test_emergency_creates_notification():
    result = emergency_notification("T-200")
    assert result["notification_type"] == EMERGENCY
    assert result["human_review_required"] is True


# ---------------------------------------------------------
# 7. Incomplete work
# ---------------------------------------------------------

def test_incomplete_work_creates_notification():
    result = incomplete_work_notification("T-103")
    assert result["notification_type"] == INCOMPLETE_WORK
    assert result["task_id"] == "T-103"


# ---------------------------------------------------------
# 8. Materials unavailable
# ---------------------------------------------------------

def test_materials_unavailable_creates_notification():
    result = materials_unavailable_notification("T-104", "Signal relay")
    assert result["notification_type"] == MATERIALS_UNAVAILABLE
    assert "Signal relay" in result["message"]


# ---------------------------------------------------------
# 9. Human verification
# ---------------------------------------------------------

def test_human_verification_creates_notification():
    result = human_verification_notification("T-105")
    assert result["notification_type"] == HUMAN_VERIFICATION_PENDING
    assert result["human_review_required"] is True


# ---------------------------------------------------------
# 10. Team reassignment
# ---------------------------------------------------------

def test_team_reassignment_creates_notification():
    result = team_reassignment_notification("TEAM-SIG-01", "B-301", "T-200")
    assert result["notification_type"] == TEAM_REASSIGNED
    assert result["team_id"] == "TEAM-SIG-01"


# ---------------------------------------------------------
# 11. Resource failure
# ---------------------------------------------------------

def test_resource_failure_creates_notification():
    result = resource_failure_notification("EQ-07", "Equipment broken")
    assert result["notification_type"] == RESOURCE_FAILURE
    assert result["resource_id"] == "EQ-07"


# ---------------------------------------------------------
# 12. All required alert type constants exist
# ---------------------------------------------------------

def test_all_alert_type_constants_defined():
    required_constants = [
        CRITICAL_TASK, EMERGENCY_TASK, HUMAN_REVIEW_REQUIRED,
        OVERDUE_MAINTENANCE, UPCOMING_MAINTENANCE, WORK_INTERRUPTED,
        TASK_REQUEUED, RESOURCE_UNAVAILABLE, BUNDLE_INVALIDATED, TEAM_REASSIGNED, FAILED_SYNC,
        INCOMPLETE_WORK, MATERIALS_UNAVAILABLE, EMERGENCY,
    ]
    for const in required_constants:
        assert isinstance(const, str)
        assert len(const) > 0


# ---------------------------------------------------------
# 13. Rules are deterministic (no side effects)
# ---------------------------------------------------------

def test_rules_are_side_effect_free():
    """Calling a rule function twice with the same input yields the same output."""
    task = {"task_id": "T-100", "asset_id": "A-1", "days_overdue": 3}
    r1 = overdue_maintenance_notification(task)
    r2 = overdue_maintenance_notification(task)
    assert r1["message"] == r2["message"]
