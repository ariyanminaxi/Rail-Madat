"""
Work Completion Workflow — processes completion reports and updates
maintenance records, asset registry, audit events, and alerts.

When a work completion report is submitted:
  1. Task status is updated.
  2. Maintenance execution history is created.
  3. next_due_date is recalculated (for preventive maintenance).
  4. Asset registry is updated (is_overdue, operational_status).
  5. Audit event is recorded.
  6. Dashboard alert is triggered if needed.

Both functions are pure: inputs in, a plan dict out. No DB/network I/O.
The backend API is the one that actually performs the writes.
"""

from datetime import date
from typing import Optional

from .maintenance_due_dates import (
    calculate_next_due_date,
    is_overdue,
    overdue_days,
    recalculate_after_completion,
)


# ---------------------------------------------------------------------------
# 1. Process a completion report
# ---------------------------------------------------------------------------

def process_completion_workflow(
    report: dict,
    task: dict,
    asset: Optional[dict] = None,
    interval_days: int = 90,
) -> dict:
    """Process a work completion report and return all updates to apply.

    Args:
        report: work completion report dict with at least:
            task_id, work_status, completion_percentage, inspection_result,
            failure_reason, remaining_work_minutes, material_status,
            safety_status, submitted_at, reported_by
        task: current maintenance task dict with at least:
            task_id, final_priority, deferral_count, escalation_level,
            asset_id
        asset: current asset dict (optional) with at least:
            asset_id, maintenance_interval_days
        interval_days: the asset's maintenance interval in days

    Returns:
        A dict containing all updates the backend API should apply.
    """
    work_status = report.get("work_status", "")
    task_id = report.get("task_id")
    reported_by = report.get("reported_by")
    submitted_at = report.get("submitted_at", "")

    if asset:
        interval_days = asset.get("maintenance_interval_days", interval_days)

    result = {
        "task_id": task_id,
        "updates": {},
        "audit_event": None,
        "alert": None,
        "maintenance_record": None,
    }

    if work_status == "Completed":
        result = _process_completed(report, task, asset, interval_days, result)
    elif work_status in ("Not Completed", "Partially Completed", "Interrupted", "Awaiting Materials"):
        result = _process_interrupted(report, task, asset, interval_days, result)
    elif work_status == "Cancelled":
        result = _process_cancelled(report, task, result)
    elif work_status == "Emergency":
        result = _process_emergency(report, task, result)
    else:
        raise ValueError(f"Unrecognized work_status: {work_status!r}")

    return result


def _process_completed(report, task, asset, interval_days, result):
    """Handle completed work — update task, recalculate due dates, update asset."""
    task_id = report["task_id"]
    completion_date = report.get("received_at", report.get("submitted_at", ""))

    # Recalculate next due date
    due_fields = {}
    if completion_date:
        try:
            due_fields = recalculate_after_completion(completion_date[:10], interval_days)
        except (ValueError, TypeError):
            due_fields = {}

    # Update task
    result["updates"] = {
        "task_status": "Completed",
        "final_priority": task.get("final_priority", "Medium"),
        "queue_again": False,
        **due_fields,
    }

    # Update asset
    if asset and due_fields:
        result["updates"]["asset_update"] = {
            "asset_id": task.get("asset_id"),
            "last_maintenance_date": due_fields.get("last_maintenance_date"),
            "next_due_date": due_fields.get("next_due_date"),
            "is_overdue": False,
            "operational_status": "Working",
        }

    # Maintenance record
    result["maintenance_record"] = {
        "task_id": task_id,
        "asset_id": task.get("asset_id"),
        "completion_status": "Completed",
        "inspection_result": report.get("inspection_result"),
        "materials_used": report.get("material_status"),
        "next_due_date": due_fields.get("next_due_date"),
    }

    # Audit event
    result["audit_event"] = {
        "action": "WORK_COMPLETED",
        "resource_type": "maintenance_task",
        "resource_id": task_id,
        "status": "SUCCESS",
        "details": {
            "completion_percentage": report.get("completion_percentage", 100),
            "inspection_result": report.get("inspection_result"),
            "reported_by": report.get("reported_by"),
        },
    }

    # No alert needed for clean completion
    result["alert"] = None

    return result


def _process_interrupted(report, task, asset, interval_days, result):
    """Handle interrupted/incomplete work — requeue and escalate priority."""
    task_id = report["task_id"]
    work_status = report["work_status"]

    deferral_count = task.get("deferral_count", 0) or 0
    escalation_level = task.get("escalation_level", 0) or 0
    final_priority = task.get("final_priority", "Medium")

    bumps_deferral = work_status in ("Not Completed", "Interrupted")
    new_deferral = deferral_count + (1 if bumps_deferral else 0)
    new_escalation = escalation_level + (1 if bumps_deferral else 0)
    escalated_priority = _escalate_priority(final_priority, new_escalation)

    status_map = {
        "Not Completed": "Deferred",
        "Partially Completed": "Partially Completed",
        "Interrupted": "Interrupted",
        "Awaiting Materials": "Awaiting Materials",
    }

    result["updates"] = {
        "task_status": status_map.get(work_status, work_status),
        "final_priority": escalated_priority,
        "deferral_count": new_deferral,
        "escalation_level": new_escalation,
        "queue_again": True,
        "human_review_required": work_status in ("Partially Completed", "Interrupted"),
    }

    # Audit event
    result["audit_event"] = {
        "action": "WORK_INTERRUPTED",
        "resource_type": "maintenance_task",
        "resource_id": task_id,
        "status": "SUCCESS",
        "details": {
            "reason": report.get("failure_reason", report.get("interruption_reason", "")),
            "remaining_work_minutes": report.get("remaining_work_minutes", 0),
            "work_status": work_status,
            "new_priority": escalated_priority,
        },
    }

    # Alert for interrupted work
    result["alert"] = {
        "alert_type": "WORK_INTERRUPTED" if work_status == "Interrupted" else "INCOMPLETE_WORK",
        "title": f"Work {work_status.lower()} for task {task_id}",
        "message": report.get("failure_reason", "Work requires attention."),
        "resource_type": "maintenance_task",
        "resource_id": task_id,
        "priority": escalated_priority,
    }

    return result


def _process_cancelled(report, task, result):
    """Handle cancelled work — requires manager approval."""
    task_id = report["task_id"]

    result["updates"] = {
        "task_status": "Cancelled",
        "cancelled_reason": report.get("failure_reason", ""),
        "queue_again": False,
        "requires_manager_approval": True,
    }

    result["audit_event"] = {
        "action": "WORK_CANCELLED",
        "resource_type": "maintenance_task",
        "resource_id": task_id,
        "status": "SUCCESS",
        "details": {
            "reason": report.get("failure_reason", ""),
            "reported_by": report.get("reported_by"),
        },
    }

    result["alert"] = {
        "alert_type": "HUMAN_REVIEW_REQUIRED",
        "title": f"Task {task_id} cancellation requires approval",
        "message": report.get("failure_reason", "Cancellation pending manager review."),
        "resource_type": "maintenance_task",
        "resource_id": task_id,
        "priority": "High",
    }

    return result


def _process_emergency(report, task, result):
    """Handle emergency status — force Critical priority, never auto-authorize."""
    task_id = report["task_id"]

    result["updates"] = {
        "task_status": "Emergency",
        "final_priority": "Critical",
        "queue_again": False,
        "automatic_block_approval": False,
        "human_review_required": True,
    }

    result["audit_event"] = {
        "action": "WORK_EMERGENCY",
        "resource_type": "maintenance_task",
        "resource_id": task_id,
        "status": "SUCCESS",
        "details": {
            "reason": report.get("failure_reason", "Emergency condition"),
            "remaining_work_minutes": report.get("remaining_work_minutes", 0),
        },
    }

    result["alert"] = {
        "alert_type": "EMERGENCY",
        "title": f"EMERGENCY: Task {task_id}",
        "message": "Emergency condition requires immediate human attention.",
        "resource_type": "maintenance_task",
        "resource_id": task_id,
        "priority": "Emergency",
    }

    return result


# ---------------------------------------------------------------------------
# Priority escalation
# ---------------------------------------------------------------------------

PRIORITY_LADDER = ["Low", "Medium", "High", "Critical"]


def _escalate_priority(current_priority: str, escalation_level: int) -> str:
    """Escalate priority by the given number of steps.

    Priority never auto-downgrades. Critical always stays Critical.
    """
    if current_priority == "Critical":
        return "Critical"
    if current_priority not in PRIORITY_LADDER:
        current_priority = "Medium"
    idx = PRIORITY_LADDER.index(current_priority)
    new_idx = min(idx + escalation_level, len(PRIORITY_LADDER) - 1)
    return PRIORITY_LADDER[new_idx]
