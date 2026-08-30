"""Maintenance Analytics — data analysis and reporting for the Maintenance Data Service.

This module provides analytics capabilities for maintenance data,
replacing the previous analytics notebook with a proper Python module.

Responsibilities:
  - Maintenance trend analysis
  - Overdue schedule reporting
  - Asset health scoring
  - Maintenance cycle efficiency metrics
"""

import os
import csv
from datetime import date, datetime
from typing import Optional

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.data_services.asset_registry_service import load_asset_registry
from app.data_services.maintenance_history_service import load_maintenance_history
from app.data_services.preventive_schedule_service import load_preventive_schedules
from app.maintenance_workflows.maintenance_due_dates import is_overdue, overdue_days


def analyze_overdue_schedules(as_of: Optional[date] = None) -> list:
    """Return all overdue schedules with overdue_days calculated."""
    if as_of is None:
        as_of = date.today()
    schedules = load_preventive_schedules()
    overdue = []
    for s in schedules:
        if is_overdue(s["next_due_date"], as_of):
            overdue.append({
                **s,
                "overdue_days": overdue_days(s["next_due_date"], as_of),
            })
    return sorted(overdue, key=lambda x: x["overdue_days"], reverse=True)


def analyze_maintenance_by_department() -> dict:
    """Return maintenance task counts grouped by department."""
    history = load_maintenance_history()
    dept_counts = {}
    for h in history:
        dept = h.get("department", "Unknown")
        dept_counts[dept] = dept_counts.get(dept, 0) + 1
    return dept_counts


def analyze_failure_rates() -> dict:
    """Calculate failure rates per fault category from maintenance history."""
    history = load_maintenance_history()
    category_stats = {}
    for h in history:
        cat = h.get("fault_category", "Unknown")
        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "failures": 0}
        category_stats[cat]["total"] += 1
        if h.get("work_status") in ("Not Completed", "Interrupted"):
            category_stats[cat]["failures"] += 1

    for cat in category_stats:
        total = category_stats[cat]["total"]
        failures = category_stats[cat]["failures"]
        category_stats[cat]["failure_rate"] = round(failures / total, 3) if total > 0 else 0.0
    return category_stats


if __name__ == "__main__":
    print("=== Overdue Schedules ===")
    for s in analyze_overdue_schedules(date(2026, 8, 20)):
        print(f"  {s['schedule_id']}: {s['asset_id']} - {s['overdue_days']} days overdue")

    print("\n=== Tasks by Department ===")
    for dept, count in analyze_maintenance_by_department().items():
        print(f"  {dept}: {count}")

    print("\n=== Failure Rates ===")
    for cat, stats in analyze_failure_rates().items():
        print(f"  {cat}: {stats['failure_rate']:.1%} ({stats['failures']}/{stats['total']})")
