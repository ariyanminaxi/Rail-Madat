"""ID Generator — generates prefixed unique identifiers for all entities."""

import uuid
from datetime import datetime, timezone


def gen_id(prefix: str) -> str:
    """Generate a unique ID with the given prefix.

    Format: PREFIX-XXXXXXXX where X is a hex character.
    Example: TASK-a1b2c3d4, AUD-e5f6a7b8
    """
    short = uuid.uuid4().hex[:8]
    return f"{prefix}-{short}"


def gen_complaint_id() -> str:
    """Generate a complaint ID: C-XXXXXXXX."""
    return gen_id("C")


def gen_task_id() -> str:
    """Generate a maintenance task ID: T-XXXXXXXX."""
    return gen_id("T")


def gen_audit_log_id() -> str:
    """Generate an audit log ID: LOG-XXXXXXXX."""
    return gen_id("LOG")


def gen_report_id(report_type: str) -> str:
    """Generate a report ID: RPT-{TYPE}-XXXXXXXX."""
    type_map = {
        "WORK_COMPLETION": "COMP",
        "WORK_INTERRUPTION": "INT",
        "TASK_REQUEUE": "REQUEUE",
        "RECOMMENDED_BLOCK": "BLOCK",
        "RESOURCE_FAILURE": "RES",
    }
    short_type = type_map.get(report_type, report_type[:4].upper())
    return gen_id(f"RPT-{short_type}")


def gen_block_id() -> str:
    """Generate a scheduling block ID: B-XXXXXXXX."""
    return gen_id("B")


def gen_approval_id() -> str:
    """Generate an approval ID: A-XXXXXXXX."""
    return gen_id("A")


def gen_alert_id() -> str:
    """Generate a dashboard alert ID: ALT-XXXXXXXX."""
    return gen_id("ALT")


def gen_notification_id() -> str:
    """Generate a notification ID: N-XXXXXXXX."""
    return gen_id("N")
