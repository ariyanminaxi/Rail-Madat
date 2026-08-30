"""
maintenance_due_dates.py — Maintenance Data Service

Single source of truth for "when is this asset next due for maintenance,
and is it currently overdue." Used by:
  - preventive_maintenance_cycle.py (recurring task generation)
  - Backend API completion endpoint (POST /maintenance-tasks/{task_id}/complete)
  - Scheduling and Resource Allocation Engine (to flag/skip overdue high-criticality assets)

All dates are ISO 8601 (see 03_Keywords_&_Data_Dictionary.md). All functions
here are pure — no database or network calls — so they're trivially
unit-testable and reusable by any module without importing a DB layer.
"""
from datetime import date, datetime, timedelta
from typing import Union

DateLike = Union[str, date, datetime]


def _to_date(value: DateLike) -> date:
    """Accept an ISO date string, a date, or a datetime; always return a date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    raise TypeError(f"Unsupported date type: {type(value)}")


def calculate_next_due_date(last_maintenance_date: DateLike, interval_days: int) -> date:
    """
    next_due_date = last_maintenance_date + interval_days

    interval_days comes from asset_master.csv / maintenance_schedules.csv.
    These MVP intervals are synthetic/illustrative (see the interval tables
    in 11_Exception_Handling & 12_Work_Completion), not official railway
    maintenance manuals — the PPT/demo must say so.
    """
    if interval_days <= 0:
        raise ValueError("interval_days must be a positive integer")
    return _to_date(last_maintenance_date) + timedelta(days=interval_days)


def is_overdue(next_due_date: DateLike, as_of: DateLike = None) -> bool:
    """True if as_of (default: today) is strictly after next_due_date."""
    as_of_date = _to_date(as_of) if as_of is not None else date.today()
    return as_of_date > _to_date(next_due_date)


def overdue_days(next_due_date: DateLike, as_of: DateLike = None) -> int:
    """Non-negative count of days overdue (0 if not yet due)."""
    as_of_date = _to_date(as_of) if as_of is not None else date.today()
    delta = (as_of_date - _to_date(next_due_date)).days
    return max(delta, 0)


def recalculate_after_completion(completion_date: DateLike, interval_days: int) -> dict:
    """
    Called when a task closes with work_status == 'Completed' (see the
    queue-decision logic in 12_Work_Completion_&_Receiver_Reports.md).
    Returns the fields the backend API should write back to asset_master / the task.
    """
    completion = _to_date(completion_date)
    next_due = calculate_next_due_date(completion, interval_days)
    return {
        "last_maintenance_date": completion.isoformat(),
        "next_due_date": next_due.isoformat(),
        "is_overdue": False,
        "overdue_days": 0,
    }


def upcoming_window(schedules, as_of: DateLike = None, horizon_days: int = 14):
    """
    schedules: iterable of dicts, each with at least 'next_due_date'.
    Returns the subset due within horizon_days of as_of (inclusive),
    not yet overdue. Powers GET /maintenance-schedules/due.
    """
    as_of_date = _to_date(as_of) if as_of is not None else date.today()
    horizon = as_of_date + timedelta(days=horizon_days)
    return [s for s in schedules if as_of_date <= _to_date(s["next_due_date"]) <= horizon]


def overdue_schedules(schedules, as_of: DateLike = None):
    """
    Returns the subset of schedules that are currently overdue.
    Powers GET /maintenance-schedules/overdue.
    """
    as_of_date = _to_date(as_of) if as_of is not None else date.today()
    return [s for s in schedules if is_overdue(s["next_due_date"], as_of_date)]
