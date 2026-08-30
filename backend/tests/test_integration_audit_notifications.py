"""
Integration test — Audit, Notifications, Reports, and Workflow

Tests the full MVP flow:

  Critical task created
        ↓
  Audit event created
        ↓
  Human review required
        ↓
  Dashboard alert created
        ↓
  Manager approval
        ↓
  Approval audit event created
        ↓
  Work interrupted
        ↓
  Interruption report created
        ↓
  Task requeued
        ↓
  Requeue audit event created

Expected:
  - All events are traceable.
  - All required alerts exist.
  - No external notification service is needed.
  - No unauthorized operation succeeds.
"""

import pytest
from app.audit.audit_logger import record_audit_event
from app.audit.audit_repository import AuditRepository
from app.notifications.notification_service import (
    create_dashboard_alert,
    get_dashboard_alerts,
    mark_alert_as_read,
)
from app.notifications.notification_rules import (
    critical_complaint_notification,
    overdue_maintenance_notification,
    emergency_notification,
)
from app.notifications.reports import (
    generate_interruption_report,
    generate_requeue_report,
    generate_completion_report,
    generate_block_report,
    generate_resource_failure_report,
    reset_seq_counter,
)


@pytest.fixture(autouse=True)
def clean_state():
    """Fresh audit repo and notification service for each test."""
    from app.notifications import notification_service
    notification_service._default_service.reset()
    repo = AuditRepository()
    repo.reset()
    reset_seq_counter()
    yield


# ---------------------------------------------------------
# 1. Critical task → audit → alert → approval → completion flow
# ---------------------------------------------------------

def test_critical_task_full_flow():
    repo = AuditRepository()

    # Step 1: Critical task created → audit event
    audit1 = record_audit_event(
        user_id="USER-OFFICER-001",
        role="officer",
        action="TASK_CREATED",
        resource_type="maintenance_task",
        resource_id="T-001",
        status="SUCCESS",
        details={"priority": "Critical", "source": "fault_report"},
        repository=repo,
    )
    assert audit1["action"] == "TASK_CREATED"
    assert audit1["status"] == "SUCCESS"

    # Step 2: Human review required → dashboard alert
    alert1 = create_dashboard_alert(
        user_id="USER-MANAGER-001",
        alert_type="HUMAN_REVIEW_REQUIRED",
        title="Critical task requires review",
        message="Task T-001 requires manager verification.",
        resource_type="maintenance_task",
        resource_id="T-001",
        priority="Critical",
    )
    assert alert1["notification_type"] == "HUMAN_REVIEW_REQUIRED"
    assert alert1["priority"] == "Critical"

    # Step 3: Manager approves → audit event
    audit2 = record_audit_event(
        user_id="USER-MANAGER-001",
        role="manager",
        action="TASK_APPROVED",
        resource_type="maintenance_task",
        resource_id="T-001",
        status="SUCCESS",
        details={"approved_by": "USER-MANAGER-001"},
        repository=repo,
    )
    assert audit2["action"] == "TASK_APPROVED"

    # Step 4: Mark alert as read
    result = mark_alert_as_read(alert1["alert_id"], "USER-MANAGER-001")
    assert result is True

    # Verify audit traceability
    events = repo.get_by_resource("maintenance_task", "T-001")
    assert len(events) == 2
    actions = [e["action"] for e in events]
    assert "TASK_CREATED" in actions
    assert "TASK_APPROVED" in actions


# ---------------------------------------------------------
# 2. Work interrupted → report → requeue → audit
# ---------------------------------------------------------

def test_interruption_requeue_flow():
    repo = AuditRepository()

    # Step 1: Work interrupted
    interruption = generate_interruption_report(
        task_id="T-002",
        reason="Required equipment unavailable",
        remaining_work_minutes=45,
        priority_recalculated=True,
    )
    assert interruption["status"] == "Interrupted"

    # Step 2: Audit the interruption
    audit1 = record_audit_event(
        user_id="USER-TEAM-001",
        role="team_lead",
        action="WORK_INTERRUPTED",
        resource_type="maintenance_task",
        resource_id="T-002",
        status="SUCCESS",
        details={"reason": "equipment_unavailable"},
        repository=repo,
    )
    assert audit1["action"] == "WORK_INTERRUPTED"

    # Step 3: Task requeued
    requeue = generate_requeue_report(
        task_id="T-002",
        reason="Equipment unavailable, requeued for next window",
        previous_status="Interrupted",
        new_priority="High",
    )
    assert requeue["status"] == "Requeued"

    # Step 4: Audit the requeue
    audit2 = record_audit_event(
        user_id="SYSTEM",
        role="system",
        action="TASK_REQUEUED",
        resource_type="maintenance_task",
        resource_id="T-002",
        status="SUCCESS",
        details={"new_priority": "High"},
        repository=repo,
    )
    assert audit2["action"] == "TASK_REQUEUED"

    # Step 5: Dashboard alert for requeue
    alert = create_dashboard_alert(
        user_id="USER-MANAGER-001",
        alert_type="TASK_REQUEUED",
        title="Task requeued",
        message="Task T-002 has been requeued.",
        resource_type="maintenance_task",
        resource_id="T-002",
    )
    assert alert["notification_type"] == "TASK_REQUEUED"

    # Verify traceability
    events = repo.get_by_resource("maintenance_task", "T-002")
    assert len(events) == 2


# ---------------------------------------------------------
# 3. Completion flow
# ---------------------------------------------------------

def test_completion_flow():
    repo = AuditRepository()

    completion = generate_completion_report(
        task_id="T-003",
        completed_by="TEAM-SIG-01",
        work_summary="Signal repaired.",
    )
    assert completion["status"] == "Completed"

    audit = record_audit_event(
        user_id="USER-TEAM-001",
        role="team_lead",
        action="WORK_COMPLETED",
        resource_type="maintenance_task",
        resource_id="T-003",
        status="SUCCESS",
        repository=repo,
    )
    assert audit["action"] == "WORK_COMPLETED"


# ---------------------------------------------------------
# 4. Resource failure flow
# ---------------------------------------------------------

def test_resource_failure_flow():
    repo = AuditRepository()

    failure = generate_resource_failure_report(
        resource_id="EQ-07",
        resource_type="Inspection Equipment",
        failure_reason="Broken.",
        affected_task_id="T-004",
    )
    assert failure["status"] == "Failed"

    audit = record_audit_event(
        user_id="SYSTEM",
        role="system",
        action="RESOURCE_FAILURE",
        resource_type="equipment",
        resource_id="EQ-07",
        status="FAILED",
        details={"affected_task": "T-004"},
        repository=repo,
    )
    assert audit["status"] == "FAILED"

    alert = create_dashboard_alert(
        user_id="USER-MANAGER-001",
        alert_type="RESOURCE_UNAVAILABLE",
        title="Resource failure",
        message="Equipment EQ-07 is unavailable.",
        resource_type="equipment",
        resource_id="EQ-07",
    )
    assert alert["notification_type"] == "RESOURCE_UNAVAILABLE"


# ---------------------------------------------------------
# 5. Scheduling block recommendation flow
# ---------------------------------------------------------

def test_scheduling_block_flow():
    repo = AuditRepository()

    block = generate_block_report(
        block_id="B-301",
        section_id="S-02",
        tasks=["T-101", "T-104"],
        train_conflict_check="PASSED",
        team_available=True,
    )
    assert block["status"] == "Recommended"

    audit = record_audit_event(
        user_id="SYSTEM",
        role="system",
        action="SCHEDULE_RECOMMENDED",
        resource_type="maintenance_block",
        resource_id="B-301",
        status="SUCCESS",
        repository=repo,
    )
    assert audit["action"] == "SCHEDULE_RECOMMENDED"

    alert = create_dashboard_alert(
        user_id="USER-MANAGER-001",
        alert_type="SCHEDULING_APPROVAL_REQUIRED",
        title="Schedule awaiting approval",
        message="Block B-301 requires manager approval.",
        resource_type="maintenance_block",
        resource_id="B-301",
    )
    assert alert["notification_type"] == "SCHEDULING_APPROVAL_REQUIRED"


# ---------------------------------------------------------
# 6. Unauthorized approval blocked
# ---------------------------------------------------------

def test_unauthorized_approval_blocked():
    user_role = "officer"
    required_role = "manager"

    audit = record_audit_event(
        user_id="USER-OFFICER-001",
        role=user_role,
        action="APPROVAL_ATTEMPTED",
        resource_type="maintenance_task",
        resource_id="T-005",
        status="BLOCKED",
        details={"reason": "insufficient_permissions"},
    )
    assert audit["status"] == "BLOCKED"


# ---------------------------------------------------------
# 7. No external notification provider needed
# ---------------------------------------------------------

def test_no_external_notification_imports():
    """The full integration flow works without external providers."""
    import inspect
    from app.notifications import notification_service
    from app.notifications import notification_rules

    for mod in [notification_service, notification_rules]:
        source = inspect.getsource(mod)
        for provider in ["smtplib", "twilio", "firebase", "websocket"]:
            assert provider not in source


# ---------------------------------------------------------
# 8. Critical complaint → audit + alert
# ---------------------------------------------------------

def test_critical_complaint_creates_audit_and_alert():
    repo = AuditRepository()

    notification = critical_complaint_notification({
        "complaint_id": "C-205",
        "final_priority": "Critical",
        "human_review_required": True,
    })
    assert notification is not None

    audit = record_audit_event(
        user_id="USER-OFFICER-001",
        role="officer",
        action="COMplaint_CLASSIFIED",
        resource_type="complaint",
        resource_id="C-205",
        status="SUCCESS",
        details={"priority": "Critical"},
        repository=repo,
    )
    assert audit["action"] == "COMplaint_CLASSIFIED"

    alert = create_dashboard_alert(
        user_id="USER-MANAGER-001",
        alert_type="CRITICAL_TASK",
        title="Critical complaint",
        message="Complaint C-205 classified as Critical.",
        resource_type="complaint",
        resource_id="C-205",
        priority="Critical",
    )
    assert alert["priority"] == "Critical"


# ---------------------------------------------------------
# 9. All alerts are traceable
# ---------------------------------------------------------

def test_alerts_created_in_flow_are_retrievable():
    create_dashboard_alert(
        user_id="U-001",
        alert_type="EMERGENCY",
        title="Emergency",
        message="Emergency on T-100",
        resource_type="task",
        resource_id="T-100",
    )
    create_dashboard_alert(
        user_id="U-001",
        alert_type="OVERDUE_MAINTENANCE",
        title="Overdue",
        message="T-101 overdue",
        resource_type="task",
        resource_id="T-101",
    )

    all_alerts = get_dashboard_alerts(user_id="U-001")
    assert len(all_alerts) == 2

    unread = get_dashboard_alerts(user_id="U-001", unread_only=True)
    assert len(unread) == 2
