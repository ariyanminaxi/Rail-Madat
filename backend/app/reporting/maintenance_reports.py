"""Maintenance Reports — completion, interruption, and requeue reports."""

import uuid
from datetime import datetime, timezone


def generate_completion_report(data: dict) -> dict:
    """Generate a work completion report."""
    task_id = data.get("task_id")
    if not task_id:
        raise ValueError("task_id is required")

    report_id = f"RPT-COMP-{uuid.uuid4().int % 900 + 100}"
    return {
        "report_id": report_id,
        "report_type": "WORK_COMPLETION",
        "task_id": task_id,
        "status": data.get("completion_status", "Completed"),
        "completion_percentage": data.get("completion_percentage", 100),
        "inspection_result": data.get("inspection_result", "Completed"),
        "materials_status": data.get("materials_status", "Available"),
        "safety_status": data.get("safety_status", "Verified"),
        "completed_by": data.get("completed_by"),
        "work_summary": data.get("work_summary", ""),
        "next_due_date": data.get("next_due_date"),
        "human_verified": data.get("human_verified", False),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def generate_interruption_report(data: dict) -> dict:
    """Generate a work interruption report."""
    task_id = data.get("task_id")
    if not task_id:
        raise ValueError("task_id is required")

    report_id = f"RPT-INT-{uuid.uuid4().int % 900 + 100}"
    return {
        "report_id": report_id,
        "report_type": "WORK_INTERRUPTION",
        "task_id": task_id,
        "status": "Interrupted",
        "reason": data.get("reason", "Unknown"),
        "remaining_work_minutes": data.get("remaining_work_minutes", 0),
        "priority_recalculated": data.get("priority_recalculated", True),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def generate_requeue_report(data: dict) -> dict:
    """Generate a task requeue report."""
    task_id = data.get("task_id")
    if not task_id:
        raise ValueError("task_id is required")

    report_id = f"RPT-REQUEUE-{uuid.uuid4().int % 900 + 100}"
    return {
        "report_id": report_id,
        "report_type": "TASK_REQUEUE",
        "task_id": task_id,
        "status": data.get("previous_status", "Requeued"),
        "reason": data.get("reason", "Unknown"),
        "requeued_at": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
