"""Date Utilities — ISO 8601 timestamps and timezone helpers."""

from datetime import datetime, timezone


def now_utc() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


def iso_timestamp() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return now_utc().isoformat()


def parse_iso(value: str) -> datetime:
    """Parse an ISO 8601 string into a datetime object."""
    return datetime.fromisoformat(value)


def days_between(start: str, end: str) -> int:
    """Return the number of days between two ISO date strings."""
    d1 = parse_iso(start) if isinstance(start, str) else start
    d2 = parse_iso(end) if isinstance(end, str) else end
    if isinstance(d1, datetime):
        d1 = d1.date()
    if isinstance(d2, datetime):
        d2 = d2.date()
    return (d2 - d1).days


def is_overdue(next_due_date: str) -> bool:
    """Check if a due date has passed."""
    due = parse_iso(next_due_date) if isinstance(next_due_date, str) else next_due_date
    return now_utc() > due
