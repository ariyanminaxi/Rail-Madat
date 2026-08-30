"""Preventive Schedule Service — retrieves preventive maintenance schedules.

Reads schedule data from CSV or database to determine when assets
are next due for preventive maintenance.
"""

import csv
import os
from typing import Optional


def load_preventive_schedules(csv_path: Optional[str] = None) -> list:
    """Load preventive maintenance schedules from CSV.

    Returns a list of dicts with at least:
        schedule_id, asset_id, section_id, department, next_due_date,
        interval_days, assigned_team_id, status
    """
    if csv_path is None:
        csv_path = os.path.join("data", "planning", "preventive_maintenance_schedules.csv")
    if not os.path.exists(csv_path):
        return []
    with open(csv_path, newline="") as f:
        return list(csv.DictReader(f))


def get_preventive_schedule(asset_id: str, schedules: Optional[list] = None) -> list:
    """Return all preventive schedules for a given asset."""
    if schedules is None:
        schedules = load_preventive_schedules()
    return [s for s in schedules if s.get("asset_id") == asset_id]


def get_schedules_by_section(section_id: str, schedules: Optional[list] = None) -> list:
    """Return all preventive schedules for a given section."""
    if schedules is None:
        schedules = load_preventive_schedules()
    return [s for s in schedules if s.get("section_id") == section_id]


def get_overdue_input_schedules(schedules: Optional[list] = None) -> list:
    """Return schedules that are marked as Overdue in the data."""
    if schedules is None:
        schedules = load_preventive_schedules()
    return [s for s in schedules if s.get("status") == "Overdue"]
