"""
conflict_detector.py — Scheduling and Resource Allocation Engine

Handles: reading train timings, detecting train conflicts, finding free
windows. Works with full ISO 8601 datetimes (with timezone), not plain
HH:MM, per the updated data contract.

IMPORTANT: Per the spec, all "now" / current-time comparisons must use a
backend-provided timestamp, never the client's local clock. This module
never calls datetime.now() for that reason -- the caller must always pass
in explicit datetimes.
"""

from datetime import datetime, timedelta


def parse_iso(dt_str: str) -> datetime:
    """Parse an ISO 8601 datetime string like '2026-08-25T10:00:00+05:30'."""
    return datetime.fromisoformat(dt_str)


def to_iso(dt: datetime) -> str:
    return dt.isoformat()


def get_trains_for_section(trains, section_id):
    return [t for t in trains if t["section_id"] == section_id]


def find_free_windows(section_trains, day_start: datetime, day_end: datetime,
                       buffer_minutes: int):
    """Return list of (start_dt, end_dt) free gaps in [day_start, day_end)
    after applying a safety buffer before/after each train's occupation."""
    if not section_trains:
        return [(day_start, day_end)]

    buffer = timedelta(minutes=buffer_minutes)
    occupied = []
    for t in section_trains:
        start = parse_iso(t["start_time"]) - buffer
        end = parse_iso(t["end_time"]) + buffer
        occupied.append((max(day_start, start), min(day_end, end)))

    occupied.sort(key=lambda w: w[0])

    merged = [occupied[0]]
    for start, end in occupied[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    free = []
    cursor = day_start
    for start, end in merged:
        if start > cursor:
            free.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < day_end:
        free.append((cursor, day_end))

    return free


def has_train_conflict(window_start: datetime, window_end: datetime,
                        section_trains, buffer_minutes: int) -> bool:
    """True if the given window overlaps any train (with buffer applied)."""
    buffer = timedelta(minutes=buffer_minutes)
    for t in section_trains:
        t_start = parse_iso(t["start_time"]) - buffer
        t_end = parse_iso(t["end_time"]) + buffer
        if window_start < t_end and t_start < window_end:
            return True
    return False
