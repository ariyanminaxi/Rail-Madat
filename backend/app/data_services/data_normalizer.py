"""Data Normalizer — normalizes CSV and database records into consistent dicts.

Ensures all data records conform to the expected schema before they
enter the Maintenance Data Service or Scheduling Engine pipelines.

Supports multiple data sources via DATA_MODE:
  - supabase: read/write from Supabase (production)
  - csv: read from CSV files (offline testing)
  - memory: in-memory store (unit tests)
"""

import os
from datetime import date, datetime
from typing import Optional

from app.config import DATA_MODE, CSV_DATA_PATH


def get_data_source() -> str:
    """Return the current data source mode."""
    return DATA_MODE


def normalize_date(value: Optional[str]) -> Optional[str]:
    """Normalize a date string to ISO 8601 format (YYYY-MM-DD).

    Accepts ISO date strings, datetime strings, and date objects.
    Returns None if the input is None or cannot be parsed.
    """
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10]).isoformat()
        except (ValueError, TypeError):
            return None
    return None


def normalize_datetime(value: Optional[str]) -> Optional[str]:
    """Normalize a datetime string to ISO 8601 format.

    Returns None if the input is None or cannot be parsed.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).isoformat()
        except (ValueError, TypeError):
            return None
    return None


def normalize_task(record: dict) -> dict:
    """Normalize a maintenance task record to the standard schema.

    Ensures all required fields are present with sensible defaults.
    """
    return {
        "task_id": record.get("task_id"),
        "source_type": record.get("source_type", "complaint"),
        "source_id": record.get("source_id"),
        "asset_id": record.get("asset_id"),
        "section_id": record.get("section_id"),
        "department": record.get("department"),
        "maintenance_type": record.get("maintenance_type", "Corrective"),
        "base_priority": record.get("base_priority", "Medium"),
        "final_priority": record.get("final_priority", record.get("base_priority", "Medium")),
        "duration_minutes": record.get("duration_minutes", 60),
        "required_team": record.get("required_team"),
        "required_equipment": record.get("required_equipment", []),
        "due_date": normalize_date(record.get("due_date")),
        "block_required": record.get("block_required", True),
        "status": record.get("status", "Reported"),
        "overdue_days": record.get("overdue_days", 0),
        "deferral_count": record.get("deferral_count", 0),
        "escalation_level": record.get("escalation_level", 0),
        "fault_category": record.get("fault_category"),
        "execution_mode": record.get("execution_mode", "Sequential"),
    }


def normalize_schedule(record: dict) -> dict:
    """Normalize a preventive maintenance schedule record."""
    return {
        "schedule_id": record.get("schedule_id"),
        "asset_id": record.get("asset_id"),
        "section_id": record.get("section_id"),
        "department": record.get("department"),
        "next_due_date": normalize_date(record.get("next_due_date")),
        "interval_days": record.get("interval_days"),
        "assigned_team_id": record.get("assigned_team_id"),
        "status": record.get("status", "Active"),
    }
