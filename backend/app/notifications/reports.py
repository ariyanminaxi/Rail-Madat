"""
RailMaintain - Reports

Generates structured reports for the MVP pipeline:
  - Work completion reports
  - Work interruption reports
  - Task requeue reports
  - Recommended scheduling-block reports
  - Resource-failure reports

All reports use ISO 8601 timestamps, valid task/resource IDs,
and are JSON-serializable. No secrets or credentials are included.
"""

from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _report_id(prefix: str, seq: int) -> str:
    return f"RPT-{prefix}-{seq:03d}"


_seq_counter = 0


def _next_seq() -> int:
    global _seq_counter
    _seq_counter += 1
    return _seq_counter


def reset_seq_counter() -> None:
    """Reset the report sequence counter. FOR TEST USE ONLY."""
    global _seq_counter
    _seq_counter = 0


# ---------------------------------------------------------------------------
# 1. Work Completion Report
# ---------------------------------------------------------------------------

def generate_completion_report(
    task_id: str,
    completion_percentage: int = 100,
    inspection_result: str = "Completed",
    materials_status: str = "Available",
    safety_status: str = "Verified",
    completed_by: str = "",
    work_summary: str = "",
    materials_used: list[str] | None = None,
    next_due_date: str = "",
    human_verified: bool = True,
) -> dict:
    """Generate a work completion report.

    Returns a dict matching the spec's completion report schema.
    """
    if not task_id:
        raise ValueError("task_id is required")

    if completion_percentage < 0 or completion_percentage > 100:
        raise ValueError("completion_percentage must be between 0 and 100")

    return {
        "report_id": _report_id("COMP", _next_seq()),
        "report_type": "WORK_COMPLETION",
        "task_id": task_id,
        "status": "Completed",
        "completion_percentage": completion_percentage,
        "inspection_result": inspection_result,
        "materials_status": materials_status,
        "safety_status": safety_status,
        "completed_by": completed_by,
        "work_summary": work_summary,
        "materials_used": materials_used or [],
        "next_due_date": next_due_date,
        "human_verified": human_verified,
        "created_at": _now_iso(),
    }


# ---------------------------------------------------------------------------
# 2. Work Interruption Report
# ---------------------------------------------------------------------------

def generate_interruption_report(
    task_id: str,
    reason: str = "",
    remaining_work_minutes: int = 0,
    priority_recalculated: bool = True,
    interrupted_by: str = "",
) -> dict:
    """Generate a work interruption report."""
    if not task_id:
        raise ValueError("task_id is required")

    return {
        "report_id": _report_id("INT", _next_seq()),
        "report_type": "WORK_INTERRUPTION",
        "task_id": task_id,
        "status": "Interrupted",
        "reason": reason,
        "remaining_work_minutes": remaining_work_minutes,
        "priority_recalculated": priority_recalculated,
        "interrupted_by": interrupted_by,
        "created_at": _now_iso(),
    }


# ---------------------------------------------------------------------------
# 3. Task Requeue Report
# ---------------------------------------------------------------------------

def generate_requeue_report(
    task_id: str,
    reason: str = "",
    previous_status: str = "",
    new_priority: str = "",
) -> dict:
    """Generate a task requeue report."""
    if not task_id:
        raise ValueError("task_id is required")

    return {
        "report_id": _report_id("REQUEUE", _next_seq()),
        "report_type": "TASK_REQUEUE",
        "task_id": task_id,
        "status": "Requeued",
        "reason": reason,
        "previous_status": previous_status,
        "new_priority": new_priority,
        "created_at": _now_iso(),
    }


# ---------------------------------------------------------------------------
# 4. Recommended Scheduling Block Report
# ---------------------------------------------------------------------------

def generate_block_report(
    block_id: str = "",
    section_id: str = "",
    start_time: str = "",
    end_time: str = "",
    duration_minutes: int = 0,
    tasks: list[str] | None = None,
    train_conflict_check: str = "PENDING",
    team_available: bool = False,
    equipment_available: bool = False,
    safety_buffer_minutes: int = 15,
    reason: str = "",
) -> dict:
    """Generate a recommended scheduling block report."""
    return {
        "report_id": _report_id("BLOCK", _next_seq()),
        "report_type": "SCHEDULING_BLOCK",
        "block_id": block_id,
        "section_id": section_id,
        "start_time": start_time,
        "end_time": end_time,
        "duration_minutes": duration_minutes,
        "tasks": tasks or [],
        "train_conflict_check": train_conflict_check,
        "team_available": team_available,
        "equipment_available": equipment_available,
        "safety_buffer_minutes": safety_buffer_minutes,
        "reason": reason,
        "status": "Recommended",
        "created_at": _now_iso(),
    }


# ---------------------------------------------------------------------------
# 5. Resource Failure Report
# ---------------------------------------------------------------------------

def generate_resource_failure_report(
    resource_id: str,
    resource_type: str = "",
    failure_reason: str = "",
    affected_task_id: str = "",
    replacement_available: bool = False,
) -> dict:
    """Generate a resource failure report."""
    if not resource_id:
        raise ValueError("resource_id is required")

    return {
        "report_id": _report_id("RESFAIL", _next_seq()),
        "report_type": "RESOURCE_FAILURE",
        "resource_id": resource_id,
        "resource_type": resource_type,
        "failure_reason": failure_reason,
        "affected_task_id": affected_task_id,
        "replacement_available": replacement_available,
        "status": "Failed",
        "created_at": _now_iso(),
    }
