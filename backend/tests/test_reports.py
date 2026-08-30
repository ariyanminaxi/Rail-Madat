"""
Tests for reports.py — Work completion, interruption, requeue,
scheduling block, and resource failure report generation.
"""

import json
import pytest
from app.notifications.reports import (
    generate_completion_report,
    generate_interruption_report,
    generate_requeue_report,
    generate_block_report,
    generate_resource_failure_report,
    reset_seq_counter,
)


@pytest.fixture(autouse=True)
def reset_counter():
    """Reset the report sequence counter before each test."""
    reset_seq_counter()
    yield
    reset_seq_counter()


# ---------------------------------------------------------
# 1. Completion report
# ---------------------------------------------------------

def test_completion_report_basic():
    report = generate_completion_report(task_id="T-101")
    assert report["report_type"] == "WORK_COMPLETION"
    assert report["task_id"] == "T-101"
    assert report["status"] == "Completed"
    assert report["completion_percentage"] == 100


def test_completion_report_has_all_fields():
    report = generate_completion_report(
        task_id="T-101",
        completion_percentage=85,
        inspection_result="Partial",
        materials_status="Low",
        safety_status="Pending",
        completed_by="TEAM-SIG-01",
        work_summary="Signal inspected.",
        materials_used=["relay", "wire"],
        next_due_date="2027-02-26",
        human_verified=True,
    )
    assert report["completion_percentage"] == 85
    assert report["materials_used"] == ["relay", "wire"]
    assert report["next_due_date"] == "2027-02-26"
    assert report["human_verified"] is True


def test_completion_report_missing_task_id_raises():
    with pytest.raises(ValueError, match="task_id"):
        generate_completion_report(task_id="")


def test_completion_report_invalid_percentage_raises():
    with pytest.raises(ValueError, match="completion_percentage"):
        generate_completion_report(task_id="T-1", completion_percentage=150)


# ---------------------------------------------------------
# 2. Interruption report
# ---------------------------------------------------------

def test_interruption_report_basic():
    report = generate_interruption_report(task_id="T-201")
    assert report["report_type"] == "WORK_INTERRUPTION"
    assert report["task_id"] == "T-201"
    assert report["status"] == "Interrupted"


def test_interruption_report_with_reason():
    report = generate_interruption_report(
        task_id="T-201",
        reason="Required equipment unavailable",
        remaining_work_minutes=60,
        priority_recalculated=True,
        interrupted_by="TEAM-SIG-01",
    )
    assert report["reason"] == "Required equipment unavailable"
    assert report["remaining_work_minutes"] == 60
    assert report["priority_recalculated"] is True


def test_interruption_report_missing_task_id_raises():
    with pytest.raises(ValueError, match="task_id"):
        generate_interruption_report(task_id="")


# ---------------------------------------------------------
# 3. Requeue report
# ---------------------------------------------------------

def test_requeue_report_basic():
    report = generate_requeue_report(task_id="T-301")
    assert report["report_type"] == "TASK_REQUEUE"
    assert report["task_id"] == "T-301"
    assert report["status"] == "Requeued"


def test_requeue_report_with_details():
    report = generate_requeue_report(
        task_id="T-301",
        reason="Required material unavailable",
        previous_status="BLOCKED",
        new_priority="High",
    )
    assert report["reason"] == "Required material unavailable"
    assert report["previous_status"] == "BLOCKED"
    assert report["new_priority"] == "High"


def test_requeue_report_missing_task_id_raises():
    with pytest.raises(ValueError, match="task_id"):
        generate_requeue_report(task_id="")


# ---------------------------------------------------------
# 4. Block report
# ---------------------------------------------------------

def test_block_report_basic():
    report = generate_block_report()
    assert report["report_type"] == "SCHEDULING_BLOCK"
    assert report["status"] == "Recommended"


def test_block_report_with_details():
    report = generate_block_report(
        block_id="B-301",
        section_id="S-02",
        start_time="02:00",
        end_time="03:30",
        duration_minutes=90,
        tasks=["T-101", "T-104"],
        train_conflict_check="PASSED",
        team_available=True,
        equipment_available=True,
        safety_buffer_minutes=15,
        reason="Low-disruption window.",
    )
    assert report["block_id"] == "B-301"
    assert report["tasks"] == ["T-101", "T-104"]
    assert report["train_conflict_check"] == "PASSED"
    assert report["team_available"] is True


# ---------------------------------------------------------
# 5. Resource failure report
# ---------------------------------------------------------

def test_resource_failure_report_basic():
    report = generate_resource_failure_report(resource_id="EQ-07")
    assert report["report_type"] == "RESOURCE_FAILURE"
    assert report["resource_id"] == "EQ-07"
    assert report["status"] == "Failed"


def test_resource_failure_report_with_details():
    report = generate_resource_failure_report(
        resource_id="EQ-07",
        resource_type="Inspection Equipment",
        failure_reason="Equipment unavailable.",
        affected_task_id="T-101",
        replacement_available=True,
    )
    assert report["resource_type"] == "Inspection Equipment"
    assert report["affected_task_id"] == "T-101"
    assert report["replacement_available"] is True


def test_resource_failure_report_missing_resource_id_raises():
    with pytest.raises(ValueError, match="resource_id"):
        generate_resource_failure_report(resource_id="")


# ---------------------------------------------------------
# 6. JSON serialization
# ---------------------------------------------------------

def test_completion_report_json_serializable():
    report = generate_completion_report(task_id="T-101")
    serialized = json.dumps(report)
    assert isinstance(serialized, str)


def test_interruption_report_json_serializable():
    report = generate_interruption_report(task_id="T-201")
    serialized = json.dumps(report)
    assert isinstance(serialized, str)


def test_block_report_json_serializable():
    report = generate_block_report(block_id="B-1")
    serialized = json.dumps(report)
    assert isinstance(serialized, str)


def test_resource_failure_report_json_serializable():
    report = generate_resource_failure_report(resource_id="EQ-1")
    serialized = json.dumps(report)
    assert isinstance(serialized, str)


# ---------------------------------------------------------
# 7. ISO timestamps
# ---------------------------------------------------------

def test_reports_use_iso_timestamps():
    for report_fn, kwargs in [
        (generate_completion_report, {"task_id": "T-1"}),
        (generate_interruption_report, {"task_id": "T-2"}),
        (generate_requeue_report, {"task_id": "T-3"}),
        (generate_block_report, {}),
        (generate_resource_failure_report, {"resource_id": "EQ-1"}),
    ]:
        report = report_fn(**kwargs)
        ts = report["created_at"]
        assert "T" in ts, f"{report_fn.__name__} missing ISO timestamp"


# ---------------------------------------------------------
# 8. Sensitive data absence
# ---------------------------------------------------------

def test_reports_contain_no_secrets():
    report = generate_completion_report(task_id="T-101")
    # The reports module should not include raw sensitive fields
    serialized = json.dumps(report)
    assert "password" not in serialized.lower()
