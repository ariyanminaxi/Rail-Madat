"""Tests for maintenance_due_dates.py — pure due-date calculation functions."""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.maintenance_workflows.maintenance_due_dates import (
    calculate_next_due_date,
    is_overdue,
    overdue_days,
    recalculate_after_completion,
    upcoming_window,
    overdue_schedules,
)


def test_calculate_next_due_date():
    result = calculate_next_due_date("2026-01-01", 90)
    assert result == date(2026, 4, 1)


def test_calculate_next_due_date_rejects_zero_interval():
    try:
        calculate_next_due_date("2026-01-01", 0)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_is_overdue_true():
    assert is_overdue("2026-01-01", "2026-02-01") is True


def test_is_overdue_false():
    assert is_overdue("2026-03-01", "2026-02-01") is False


def test_overdue_days_positive():
    assert overdue_days("2026-01-01", "2026-01-11") == 10


def test_overdue_days_zero_when_not_overdue():
    assert overdue_days("2026-03-01", "2026-02-01") == 0


def test_recalculate_after_completion():
    result = recalculate_after_completion("2026-06-15", 90)
    assert result["last_maintenance_date"] == "2026-06-15"
    assert result["next_due_date"] == "2026-09-13"
    assert result["is_overdue"] is False
    assert result["overdue_days"] == 0


def test_upcoming_window():
    schedules = [
        {"next_due_date": "2026-08-25"},
        {"next_due_date": "2026-09-15"},
        {"next_due_date": "2026-08-20"},
    ]
    result = upcoming_window(schedules, as_of="2026-08-20", horizon_days=7)
    # Both 2026-08-20 and 2026-08-25 are within the 7-day horizon from 2026-08-20
    assert len(result) == 2
    due_dates = {r["next_due_date"] for r in result}
    assert "2026-08-25" in due_dates
    assert "2026-08-20" in due_dates


def test_overdue_schedules():
    schedules = [
        {"next_due_date": "2026-08-01"},
        {"next_due_date": "2026-09-15"},
    ]
    result = overdue_schedules(schedules, as_of="2026-08-20")
    assert len(result) == 1
    assert result[0]["next_due_date"] == "2026-08-01"
