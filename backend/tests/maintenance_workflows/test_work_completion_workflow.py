"""Tests for work completion workflow edge cases and integration."""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.maintenance_workflows.preventive_maintenance_cycle import process_completion_report
from app.maintenance_workflows.maintenance_due_dates import calculate_next_due_date


def _make_task(final_priority="Medium", deferral_count=0, escalation_level=0):
    return {
        "task_id": "T-TEST",
        "final_priority": final_priority,
        "deferral_count": deferral_count,
        "escalation_level": escalation_level,
    }


def test_partially_completed_returns_to_queue():
    report = {"work_status": "Partially Completed", "received_at": "2026-08-20T14:00:00+05:30"}
    result = process_completion_report(report, _make_task(), asset_interval_days=90)
    assert result["task_status"] == "Partially Completed"
    assert result["queue_again"] is True
    assert result["human_review_required"] is True


def test_not_completed_increases_deferral():
    report = {"work_status": "Not Completed", "received_at": "2026-08-20T14:00:00+05:30"}
    task = _make_task(deferral_count=2)
    result = process_completion_report(report, task, asset_interval_days=90)
    assert result["deferral_count"] == 3


def test_notification_required_on_all_outcomes():
    statuses = ["Completed", "Interrupted", "Not Completed", "Partially Completed",
                "Awaiting Materials", "Cancelled", "Emergency"]
    for status in statuses:
        report = {"work_status": status, "received_at": "2026-08-20T14:00:00+05:30"}
        result = process_completion_report(report, _make_task(), asset_interval_days=90)
        assert result["notification_required"] is True, f"Missing notification_required for {status}"


def test_invalid_work_status_raises():
    report = {"work_status": "InvalidStatus", "received_at": "2026-08-20T14:00:00+05:30"}
    try:
        process_completion_report(report, _make_task(), asset_interval_days=90)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_maintenance_record_created_on_all_outcomes():
    statuses = ["Completed", "Interrupted", "Not Completed", "Awaiting Materials"]
    for status in statuses:
        report = {"work_status": status, "received_at": "2026-08-20T14:00:00+05:30"}
        result = process_completion_report(report, _make_task(), asset_interval_days=90)
        assert result["maintenance_record_created"] is True, f"Missing for {status}"
