"""Tests for preventive_maintenance_cycle.py — Maintenance Workflows.

Covers:
  - Overdue schedule creates a preventive task
  - Schedule with an existing open task does not create a duplicate
  - Completed work recalculates the next due date
  - Interrupted work returns to the queue
  - Awaiting Materials returns to the queue
  - Cancelled work requires manager approval
  - Emergency work requires human review
  - Repeated maintenance cycles work over time
  - Workflow history is recorded
"""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.maintenance_workflows.preventive_maintenance_cycle import (
    generate_due_maintenance_tasks,
    process_completion_report,
    _escalate_priority,
)
from app.maintenance_workflows.maintenance_due_dates import (
    calculate_next_due_date,
    is_overdue,
    overdue_days,
    recalculate_after_completion,
)


# ---------------------------------------------------------------------------
# Helper data
# ---------------------------------------------------------------------------
def _make_schedule(schedule_id, asset_id, section_id, department,
                   next_due_date, interval_days=90, assigned_team_id=None,
                   status="Active"):
    return {
        "schedule_id": schedule_id,
        "asset_id": asset_id,
        "section_id": section_id,
        "department": department,
        "next_due_date": next_due_date,
        "interval_days": interval_days,
        "assigned_team_id": assigned_team_id,
        "status": status,
    }


def _make_task(task_id, final_priority="Medium", deferral_count=0, escalation_level=0):
    return {
        "task_id": task_id,
        "final_priority": final_priority,
        "deferral_count": deferral_count,
        "escalation_level": escalation_level,
    }


# ---------------------------------------------------------------------------
# 1. Overdue schedule creates a preventive task
# ---------------------------------------------------------------------------
def test_overdue_schedule_creates_preventive_task():
    schedules = [_make_schedule("SCH-001", "A-01", "S-01", "Track", "2026-08-01")]
    tasks = generate_due_maintenance_tasks(schedules, set(), current_time=date(2026, 8, 20))
    assert len(tasks) == 1
    assert tasks[0]["source_id"] == "SCH-001"
    assert tasks[0]["maintenance_type"] == "Preventive"
    assert tasks[0]["base_priority"] == "High"


# ---------------------------------------------------------------------------
# 2. Schedule with existing open task does not create duplicate
# ---------------------------------------------------------------------------
def test_existing_open_task_prevents_duplicate():
    schedules = [_make_schedule("SCH-001", "A-01", "S-01", "Track", "2026-08-01")]
    tasks = generate_due_maintenance_tasks(schedules, {"SCH-001"}, current_time=date(2026, 8, 20))
    assert len(tasks) == 0


# ---------------------------------------------------------------------------
# 3. Non-overdue schedule does not create task
# ---------------------------------------------------------------------------
def test_non_overdue_schedule_skipped():
    schedules = [_make_schedule("SCH-002", "A-02", "S-01", "Track", "2026-09-30")]
    tasks = generate_due_maintenance_tasks(schedules, set(), current_time=date(2026, 8, 20))
    assert len(tasks) == 0


# ---------------------------------------------------------------------------
# 4. Schedule marked Overdue in status creates task even if date not yet past
# ---------------------------------------------------------------------------
def test_status_overdue_creates_task():
    schedules = [_make_schedule("SCH-003", "A-03", "S-02", "Signalling",
                                "2026-08-25", status="Overdue")]
    tasks = generate_due_maintenance_tasks(schedules, set(), current_time=date(2026, 8, 20))
    assert len(tasks) == 1
    # Status is Overdue but date is in the future, so base_priority is Medium
    # (not actually overdue yet by date calculation)
    assert tasks[0]["base_priority"] == "Medium"


# ---------------------------------------------------------------------------
# 5. Assigned team comes from schedule
# ---------------------------------------------------------------------------
def test_assigned_team_from_schedule():
    schedules = [_make_schedule("SCH-004", "A-04", "S-01", "Track",
                                "2026-08-01", assigned_team_id="TEAM-TRK-01")]
    tasks = generate_due_maintenance_tasks(schedules, set(), current_time=date(2026, 8, 20))
    assert tasks[0]["required_team"] == "TEAM-TRK-01"


# ---------------------------------------------------------------------------
# 6. Fallback team prefix when no assigned_team_id
# ---------------------------------------------------------------------------
def test_fallback_team_prefix():
    schedules = [_make_schedule("SCH-005", "A-05", "S-01", "Signalling", "2026-08-01")]
    tasks = generate_due_maintenance_tasks(schedules, set(), current_time=date(2026, 8, 20))
    assert tasks[0]["required_team"] == "TEAM-SIG-01"


# ---------------------------------------------------------------------------
# 7. Completed work recalculates the next due date
# ---------------------------------------------------------------------------
def test_completed_recalculates_next_due():
    report = {"work_status": "Completed", "received_at": "2026-08-20T14:00:00+05:30"}
    task = _make_task("T-001")
    result = process_completion_report(report, task, asset_interval_days=90)
    assert result["task_status"] == "Completed"
    assert result["queue_again"] is False
    assert result["next_due_date"] == "2026-11-18"
    assert result["is_overdue"] is False
    assert result["overdue_days"] == 0


# ---------------------------------------------------------------------------
# 8. Interrupted work returns to the queue
# ---------------------------------------------------------------------------
def test_interrupted_returns_to_queue():
    report = {"work_status": "Interrupted", "received_at": "2026-08-20T14:00:00+05:30",
              "failure_reason": "Train conflict"}
    task = _make_task("T-002", final_priority="Medium")
    result = process_completion_report(report, task, asset_interval_days=90)
    assert result["task_status"] == "Interrupted"
    assert result["queue_again"] is True
    assert result["human_review_required"] is True


# ---------------------------------------------------------------------------
# 9. Awaiting Materials returns to the queue
# ---------------------------------------------------------------------------
def test_awaiting_materials_returns_to_queue():
    report = {"work_status": "Awaiting Materials", "received_at": "2026-08-20T14:00:00+05:30"}
    task = _make_task("T-003")
    result = process_completion_report(report, task, asset_interval_days=90)
    assert result["task_status"] == "Awaiting Materials"
    assert result["queue_again"] is True
    assert result["human_review_required"] is False


# ---------------------------------------------------------------------------
# 10. Cancelled work requires manager approval
# ---------------------------------------------------------------------------
def test_cancelled_requires_manager_approval():
    report = {"work_status": "Cancelled", "received_at": "2026-08-20T14:00:00+05:30",
              "failure_reason": "Scope change"}
    task = _make_task("T-004")
    result = process_completion_report(report, task, asset_interval_days=90)
    assert result["task_status"] == "Cancelled"
    assert result["requires_manager_approval"] is True
    assert result["queue_again"] is False


# ---------------------------------------------------------------------------
# 11. Emergency work requires human review
# ---------------------------------------------------------------------------
def test_emergency_requires_human_review():
    report = {"work_status": "Emergency", "received_at": "2026-08-20T14:00:00+05:30"}
    task = _make_task("T-005")
    result = process_completion_report(report, task, asset_interval_days=90)
    assert result["task_status"] == "Emergency"
    assert result["final_priority"] == "Critical"
    assert result["human_review_required"] is True
    assert result["automatic_block_approval"] is False


# ---------------------------------------------------------------------------
# 12. Repeated maintenance cycles work over time
# ---------------------------------------------------------------------------
def test_repeated_maintenance_cycles_over_time():
    """Simulate three maintenance cycles to verify the due-date chain."""
    interval = 90
    # Cycle 1
    report1 = {"work_status": "Completed", "received_at": "2026-01-15T10:00:00+05:30"}
    result1 = process_completion_report(report1, _make_task("T-C1"), interval)
    assert result1["next_due_date"] == "2026-04-15"

    # Cycle 2
    report2 = {"work_status": "Completed", "received_at": "2026-04-15T10:00:00+05:30"}
    result2 = process_completion_report(report2, _make_task("T-C2"), interval)
    assert result2["next_due_date"] == "2026-07-14"

    # Cycle 3
    report3 = {"work_status": "Completed", "received_at": "2026-07-14T10:00:00+05:30"}
    result3 = process_completion_report(report3, _make_task("T-C3"), interval)
    assert result3["next_due_date"] == "2026-10-12"


# ---------------------------------------------------------------------------
# 13. Priority escalation on deferral
# ---------------------------------------------------------------------------
def test_priority_escalates_on_deferral():
    report = {"work_status": "Not Completed", "received_at": "2026-08-20T14:00:00+05:30"}
    task = _make_task("T-006", final_priority="Low", deferral_count=0, escalation_level=0)
    result = process_completion_report(report, task, asset_interval_days=90)
    assert result["final_priority"] == "Medium"
    assert result["escalation_level"] == 1


# ---------------------------------------------------------------------------
# 14. Critical priority never downgrades
# ---------------------------------------------------------------------------
def test_critical_never_downgrades():
    report = {"work_status": "Not Completed", "received_at": "2026-08-20T14:00:00+05:30"}
    task = _make_task("T-007", final_priority="Critical", deferral_count=0, escalation_level=0)
    result = process_completion_report(report, task, asset_interval_days=90)
    assert result["final_priority"] == "Critical"


# ---------------------------------------------------------------------------
# 15. Workflow history fields are present on all outcomes
# ---------------------------------------------------------------------------
def test_audit_log_required_on_all_outcomes():
    statuses = ["Completed", "Interrupted", "Awaiting Materials", "Cancelled", "Emergency"]
    for status in statuses:
        report = {"work_status": status, "received_at": "2026-08-20T14:00:00+05:30"}
        task = _make_task("T-AUDIT")
        result = process_completion_report(report, task, asset_interval_days=90)
        assert result["audit_log_required"] is True, f"Missing audit_log_required for {status}"


# ---------------------------------------------------------------------------
# Six-month simulation test
# ---------------------------------------------------------------------------
def test_six_month_simulation():
    """Simulate a 6-month preventive maintenance lifecycle with varied outcomes."""
    interval = 90
    start = date(2026, 1, 1)
    schedules = [_make_schedule("SCH-SIM", "A-SIM", "S-01", "Track", "2026-01-01",
                                interval_days=interval)]

    # Month 1: overdue, task generated
    tasks = generate_due_maintenance_tasks(schedules, set(), current_time=date(2026, 1, 10))
    assert len(tasks) == 1

    # Month 1: work interrupted
    report_interrupted = {"work_status": "Interrupted", "received_at": "2026-01-15T10:00:00+05:30"}
    result_interrupted = process_completion_report(report_interrupted, _make_task("T-SIM-1"), interval)
    assert result_interrupted["queue_again"] is True

    # Month 2: work completed
    report_completed = {"work_status": "Completed", "received_at": "2026-02-10T10:00:00+05:30"}
    result_completed = process_completion_report(report_completed, _make_task("T-SIM-2"), interval)
    next_due = date.fromisoformat(result_completed["next_due_date"])

    # Month 5: new task generated when past due date
    from datetime import timedelta
    tasks2 = generate_due_maintenance_tasks(
        [_make_schedule("SCH-SIM", "A-SIM", "S-01", "Track",
                        result_completed["next_due_date"], interval_days=interval)],
        set(), current_time=next_due + timedelta(days=1)
    )
    assert len(tasks2) == 1
