"""Scheduling Reports — block recommendation and resource failure reports."""

import uuid
from datetime import datetime, timezone


def generate_block_report(data: dict) -> dict:
    """Generate a recommended scheduling-block report."""
    block_id = data.get("block_id")
    if not block_id:
        raise ValueError("block_id is required")

    report_id = f"RPT-BLOCK-{uuid.uuid4().int % 900 + 100}"
    return {
        "report_id": report_id,
        "report_type": "RECOMMENDED_BLOCK",
        "block_id": block_id,
        "section_id": data.get("section_id"),
        "start_time": data.get("start_time"),
        "end_time": data.get("end_time"),
        "duration_minutes": data.get("duration_minutes", 0),
        "tasks": data.get("tasks", []),
        "train_conflict_check": data.get("train_conflict_check", "PENDING"),
        "team_available": data.get("team_available", False),
        "equipment_available": data.get("equipment_available", False),
        "safety_buffer_minutes": data.get("safety_buffer_minutes", 15),
        "reason": data.get("reason", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def generate_resource_failure_report(data: dict) -> dict:
    """Generate a resource-failure report."""
    resource_id = data.get("resource_id")
    if not resource_id:
        raise ValueError("resource_id is required")

    report_id = f"RPT-RES-{uuid.uuid4().int % 900 + 100}"
    return {
        "report_id": report_id,
        "report_type": "RESOURCE_FAILURE",
        "resource_id": resource_id,
        "resource_type": data.get("resource_type", "Unknown"),
        "failure_reason": data.get("failure_reason", "Unknown"),
        "affected_task_id": data.get("affected_task_id"),
        "replacement_available": data.get("replacement_available", False),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
