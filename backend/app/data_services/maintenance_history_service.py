"""Maintenance History Service — retrieves past maintenance execution records.

Provides historical maintenance data for assets including completed,
interrupted, and deferred work.
"""

import csv
import os
from typing import Optional


def load_maintenance_history(csv_path: Optional[str] = None) -> list:
    """Load maintenance execution history from CSV.

    Returns a list of dicts with at least:
        task_id, asset_id, section_id, work_status, completed_at,
        fault_category, department
    """
    if csv_path is None:
        csv_path = os.path.join("data", "execution", "maintenance_execution_history.csv")
    if not os.path.exists(csv_path):
        return []
    with open(csv_path, newline="") as f:
        return list(csv.DictReader(f))


def get_maintenance_history(asset_id: str, history: Optional[list] = None) -> list:
    """Return all maintenance history records for a given asset."""
    if history is None:
        history = load_maintenance_history()
    return [h for h in history if h.get("asset_id") == asset_id]


def count_repeated_failures(asset_id: str, fault_category: str,
                            history: Optional[list] = None) -> int:
    """Count how many times the same fault_category has occurred on an asset."""
    if history is None:
        history = load_maintenance_history()
    return sum(
        1 for h in history
        if h.get("asset_id") == asset_id
        and h.get("fault_category") == fault_category
        and h.get("work_status") in ("Not Completed", "Interrupted")
    )


def count_deferrals(asset_id: str, history: Optional[list] = None) -> int:
    """Count the total number of deferrals for an asset."""
    if history is None:
        history = load_maintenance_history()
    return sum(
        1 for h in history
        if h.get("asset_id") == asset_id
        and h.get("work_status") in ("Deferred", "Not Completed", "Interrupted")
    )


def count_reopenings(asset_id: str, history: Optional[list] = None) -> int:
    """Count how many times a task was reopened for an asset."""
    if history is None:
        history = load_maintenance_history()
    return sum(
        1 for h in history
        if h.get("asset_id") == asset_id
        and h.get("work_status") == "Reopened"
    )
