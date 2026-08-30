"""Tests for data_normalizer.py — Maintenance Data Service."""
import sys
import os
from datetime import date, datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.data_services.data_normalizer import (
    normalize_date,
    normalize_datetime,
    normalize_task,
    normalize_schedule,
)


def test_normalize_date_string():
    assert normalize_date("2026-08-20") == "2026-08-20"


def test_normalize_date_none():
    assert normalize_date(None) is None


def test_normalize_date_object():
    d = date(2026, 8, 20)
    assert normalize_date(d) == "2026-08-20"


def test_normalize_date_invalid():
    assert normalize_date("not-a-date") is None


def test_normalize_datetime_string():
    result = normalize_datetime("2026-08-20T10:00:00+05:30")
    assert "2026-08-20" in result


def test_normalize_datetime_none():
    assert normalize_datetime(None) is None


def test_normalize_task_defaults():
    result = normalize_task({})
    assert result["status"] == "Reported"
    assert result["maintenance_type"] == "Corrective"
    assert result["duration_minutes"] == 60
    assert result["block_required"] is True
    assert result["overdue_days"] == 0
    assert result["deferral_count"] == 0
    assert result["escalation_level"] == 0


def test_normalize_task_preserves_values():
    result = normalize_task({"task_id": "T-001", "status": "In Progress", "duration_minutes": 120})
    assert result["task_id"] == "T-001"
    assert result["status"] == "In Progress"
    assert result["duration_minutes"] == 120


def test_normalize_schedule_defaults():
    result = normalize_schedule({})
    assert result["status"] == "Active"


def test_normalize_schedule_preserves_values():
    result = normalize_schedule({"schedule_id": "SCH-001", "next_due_date": "2026-08-20"})
    assert result["schedule_id"] == "SCH-001"
    assert result["next_due_date"] == "2026-08-20"
