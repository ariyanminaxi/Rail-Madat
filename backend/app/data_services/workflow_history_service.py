"""Workflow History Service — retrieves workflow status history records.

Tracks status transitions and workflow events for maintenance tasks.
"""

import csv
import os
from typing import Optional


def load_workflow_history(csv_path: Optional[str] = None) -> list:
    """Load workflow status history from CSV.

    Returns a list of dicts with at least:
        task_id, asset_id, section_id, previous_status, new_status,
        changed_at, changed_by, reason
    """
    if csv_path is None:
        csv_path = os.path.join("data", "workflow", "workflow_status_history.csv")
    if not os.path.exists(csv_path):
        return []
    with open(csv_path, newline="") as f:
        return list(csv.DictReader(f))


def get_workflow_history(asset_id: str, history: Optional[list] = None) -> list:
    """Return all workflow status history records for a given asset."""
    if history is None:
        history = load_workflow_history()
    return [h for h in history if h.get("asset_id") == asset_id]


def get_task_workflow_history(task_id: str, history: Optional[list] = None) -> list:
    """Return all workflow status history records for a given task."""
    if history is None:
        history = load_workflow_history()
    return [h for h in history if h.get("task_id") == task_id]


def get_latest_status(task_id: str, history: Optional[list] = None) -> Optional[str]:
    """Return the most recent status for a task."""
    task_history = get_task_workflow_history(task_id, history)
    if not task_history:
        return None
    return task_history[-1].get("new_status")
