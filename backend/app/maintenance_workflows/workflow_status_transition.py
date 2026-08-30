"""
Workflow Status Transition — validates and records status changes.

Every status transition is:
  1. Validated against allowed transitions.
  2. Recorded in workflow_status_history.
  3. Audited with actor and reason.

Certain transitions require a reason:
  Interrupted, Cancelled, Rejected, Reopened, Deferred, Escalated

Invalid transitions are rejected with a ValueError.
"""

from datetime import datetime, timezone
from typing import Optional


# ---------------------------------------------------------------------------
# Allowed transitions (source -> set of valid targets)
# ---------------------------------------------------------------------------

ALLOWED_TRANSITIONS = {
    "Reported": {"Under Review", "Emergency"},
    "Under Review": {"Assigned", "Rejected", "Duplicate"},
    "Assigned": {"Waiting for Block"},
    "Waiting for Block": {"Scheduled"},
    "Scheduled": {"In Progress"},
    "In Progress": {"Completed", "Partially Completed", "Interrupted", "Deferred"},
    "Partially Completed": {"Completed", "Interrupted", "Deferred"},
    "Interrupted": {"Scheduled", "Awaiting Materials", "Cancelled", "Deferred"},
    "Deferred": {"Scheduled", "Awaiting Materials", "Cancelled"},
    "Awaiting Materials": {"Scheduled", "Cancelled"},
    "Awaiting Human Verification": {"Completed", "Rejected"},
    "Awaiting Communication": {"Scheduled", "Cancelled"},
    "Requires Inspection": {"Scheduled", "Cancelled"},
    "Completed": {"Reopened"},
    "Reopened": {"Under Review", "Scheduled"},
    "Rejected": {"Under Review"},
    "Cancelled": set(),  # terminal
    "Emergency": {"Scheduled", "In Progress", "Cancelled"},
}

# Transitions that require a reason
REQUIRES_REASON = frozenset({
    "Interrupted",
    "Cancelled",
    "Rejected",
    "Reopened",
    "Deferred",
    "Emergency",
})


def validate_status_transition(
    previous_status: str,
    new_status: str,
) -> bool:
    """Validate that a status transition is allowed.

    Raises ValueError if the transition is invalid.
    Returns True if valid.
    """
    allowed = ALLOWED_TRANSITIONS.get(previous_status)
    if allowed is None:
        raise ValueError(
            f"Unknown previous status: {previous_status!r}"
        )
    if new_status not in allowed:
        raise ValueError(
            f"Invalid status transition: {previous_status!r} -> {new_status!r}. "
            f"Allowed targets: {sorted(allowed)}"
        )
    return True


def record_status_transition(
    task_id: str,
    previous_status: Optional[str],
    new_status: str,
    changed_by: Optional[str] = None,
    reason: Optional[str] = None,
    priority_at_change: Optional[str] = None,
    escalation_level: Optional[int] = None,
) -> dict:
    """Validate and record a workflow status transition.

    Args:
        task_id: The maintenance task identifier.
        previous_status: The status before the transition (None for initial).
        new_status: The target status.
        changed_by: User or system that performed the change.
        reason: Required for Interrupted, Cancelled, Rejected, Reopened,
                Deferred, Emergency.
        priority_at_change: The task's priority at the time of transition.
        escalation_level: The task's escalation level at the time of transition.

    Returns:
        A dict representing the workflow status history record.

    Raises:
        ValueError: If the transition is invalid or a required reason
                    is missing.
    """
    # Validate the transition
    if previous_status is not None:
        validate_status_transition(previous_status, new_status)

    # Require reason for certain transitions
    if new_status in REQUIRES_REASON and not reason:
        raise ValueError(
            f"Status transition to {new_status!r} requires a reason"
        )

    return {
        "task_id": task_id,
        "previous_status": previous_status,
        "new_status": new_status,
        "changed_by": changed_by,
        "reason": reason,
        "priority_at_change": priority_at_change,
        "escalation_level": escalation_level,
        "changed_at": datetime.now(timezone.utc).isoformat(),
    }
