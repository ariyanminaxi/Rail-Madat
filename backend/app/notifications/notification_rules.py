"""
RailMaintain - Notification Rules
Role 6: Notifications

These rules create notifications from results produced by other modules.
They do NOT make railway safety decisions or authorize maintenance blocks.
"""

# ---------------------------------------------------------------------
# Notification types
# ---------------------------------------------------------------------

CRITICAL_COMPLAINT = "CRITICAL_COMPLAINT"
UPCOMING_MAINTENANCE = "UPCOMING_MAINTENANCE"
OVERDUE_MAINTENANCE = "OVERDUE_MAINTENANCE"
APPROVAL_PENDING = "APPROVAL_PENDING"
FAILED_SYNC = "FAILED_SYNC"

EMERGENCY = "EMERGENCY"
INCOMPLETE_WORK = "INCOMPLETE_WORK"
MATERIALS_UNAVAILABLE = "MATERIALS_UNAVAILABLE"
HUMAN_VERIFICATION_PENDING = "HUMAN_VERIFICATION_PENDING"

TEAM_REASSIGNED = "TEAM_REASSIGNED"
RESOURCE_FAILURE = "RESOURCE_FAILURE"

# Additional alert types per the spec
CRITICAL_TASK = "CRITICAL_TASK"
EMERGENCY_TASK = "EMERGENCY_TASK"
HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
WORK_INTERRUPTED = "WORK_INTERRUPTED"
TASK_REQUEUED = "TASK_REQUEUED"
RESOURCE_UNAVAILABLE = "RESOURCE_UNAVAILABLE"
SCHEDULING_APPROVAL_REQUIRED = "SCHEDULING_APPROVAL_REQUIRED"
BUNDLE_INVALIDATED = "BUNDLE_INVALIDATED"


# ---------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------

def make_notification(
    notification_type: str,
    title: str,
    message: str,
    **extra,
) -> dict:
    """Create a standard notification dictionary."""

    notification = {
        "notification_type": notification_type,
        "title": title,
        "message": message,
    }

    notification.update(extra)
    return notification


# ---------------------------------------------------------------------
# 1. Critical complaint
# ---------------------------------------------------------------------

def critical_complaint_notification(priority_result: dict) -> dict | None:
    """Create an alert when complaint priority is Critical."""

    if priority_result.get("final_priority") != "Critical":
        return None

    complaint_id = priority_result.get("complaint_id", "UNKNOWN")

    return make_notification(
        CRITICAL_COMPLAINT,
        "Critical Complaint",
        (
            f"Complaint {complaint_id} has Critical priority "
            "and requires immediate human attention."
        ),
        complaint_id=complaint_id,
        priority="Critical",
        suggested_action=priority_result.get(
            "suggested_action",
            "Immediate inspection",
        ),
        human_review_required=priority_result.get(
            "human_review_required",
            True,
        ),
    )


# ---------------------------------------------------------------------
# 2. Upcoming maintenance
# ---------------------------------------------------------------------

def upcoming_maintenance_notification(
    maintenance_task: dict,
    days_until_due: int,
) -> dict | None:
    """Alert when preventive maintenance is approaching."""

    if days_until_due < 0 or days_until_due > 7:
        return None

    task_id = maintenance_task.get("task_id", "UNKNOWN")
    asset_id = maintenance_task.get("asset_id", "UNKNOWN")

    return make_notification(
        UPCOMING_MAINTENANCE,
        "Upcoming Maintenance",
        (
            f"Maintenance task {task_id} for asset {asset_id} "
            f"is due in {days_until_due} day(s)."
        ),
        task_id=task_id,
        asset_id=asset_id,
        days_until_due=days_until_due,
    )


# ---------------------------------------------------------------------
# 3. Overdue maintenance
# ---------------------------------------------------------------------

def overdue_maintenance_notification(
    maintenance_task: dict,
) -> dict | None:
    """Alert when preventive maintenance is overdue."""

    days_overdue = maintenance_task.get("days_overdue", 0)

    if days_overdue <= 0:
        return None

    task_id = maintenance_task.get("task_id", "UNKNOWN")
    asset_id = maintenance_task.get("asset_id", "UNKNOWN")

    return make_notification(
        OVERDUE_MAINTENANCE,
        "Overdue Maintenance",
        (
            f"Maintenance task {task_id} for asset {asset_id} "
            f"is overdue by {days_overdue} day(s)."
        ),
        task_id=task_id,
        asset_id=asset_id,
        days_overdue=days_overdue,
    )


# ---------------------------------------------------------------------
# 4. Approval pending
# ---------------------------------------------------------------------

def approval_pending_notification(
    maintenance_block: dict,
) -> dict | None:
    """Alert when a recommended maintenance block needs approval."""

    status = str(
        maintenance_block.get("status", "")
    ).upper()

    if status not in {
        "PENDING_APPROVAL",
        "APPROVAL_PENDING",
    }:
        return None

    block_id = maintenance_block.get("block_id", "UNKNOWN")

    return make_notification(
        APPROVAL_PENDING,
        "Approval Pending",
        (
            f"Recommended maintenance block {block_id} "
            "is waiting for human approval."
        ),
        block_id=block_id,
        human_approval_required=True,
    )


# ---------------------------------------------------------------------
# 5. Failed synchronization
# ---------------------------------------------------------------------

def failed_sync_notification(
    resource_id: str,
    details: str = "Data synchronization failed.",
) -> dict:
    """Create a notification when synchronization fails."""

    return make_notification(
        FAILED_SYNC,
        "Synchronization Failed",
        details,
        resource_id=resource_id,
    )


# ---------------------------------------------------------------------
# 6. Emergency
# ---------------------------------------------------------------------

def emergency_notification(
    resource_id: str,
    message: str = "Emergency condition requires human attention.",
) -> dict:
    """Create an emergency notification."""

    return make_notification(
        EMERGENCY,
        "Emergency Alert",
        message,
        resource_id=resource_id,
        human_review_required=True,
    )


# ---------------------------------------------------------------------
# 7. Incomplete work
# ---------------------------------------------------------------------

def incomplete_work_notification(
    task_id: str,
    details: str = "Maintenance work was not completed.",
) -> dict:
    """Alert when maintenance work is incomplete."""

    return make_notification(
        INCOMPLETE_WORK,
        "Incomplete Maintenance Work",
        details,
        task_id=task_id,
    )


# ---------------------------------------------------------------------
# 8. Materials unavailable
# ---------------------------------------------------------------------

def materials_unavailable_notification(
    task_id: str,
    material: str = "Required material",
) -> dict:
    """Alert when required maintenance material is unavailable."""

    return make_notification(
        MATERIALS_UNAVAILABLE,
        "Materials Unavailable",
        f"{material} is unavailable for maintenance task {task_id}.",
        task_id=task_id,
        material=material,
    )


# ---------------------------------------------------------------------
# 9. Human verification pending
# ---------------------------------------------------------------------

def human_verification_notification(
    task_id: str,
) -> dict:
    """Alert when human verification is required."""

    return make_notification(
        HUMAN_VERIFICATION_PENDING,
        "Human Verification Pending",
        (
            f"Maintenance task {task_id} requires "
            "human verification before completion."
        ),
        task_id=task_id,
        human_review_required=True,
    )


# ---------------------------------------------------------------------
# 10. Team reassignment
# ---------------------------------------------------------------------

def team_reassignment_notification(
    team_id: str,
    old_block: str,
    new_task: str,
) -> dict:
    """Notify when a maintenance team is reassigned."""

    return make_notification(
        TEAM_REASSIGNED,
        "Maintenance Team Reassigned",
        (
            f"Team {team_id} was reassigned from "
            f"{old_block} to critical task {new_task}."
        ),
        team_id=team_id,
        old_block=old_block,
        new_task=new_task,
    )


# ---------------------------------------------------------------------
# 11. Resource failure
# ---------------------------------------------------------------------

def resource_failure_notification(
    resource_id: str,
    details: str,
) -> dict:
    """Alert when a required resource becomes unavailable."""

    return make_notification(
        RESOURCE_FAILURE,
        "Resource Failure",
        details,
        resource_id=resource_id,
    )


# ---------------------------------------------------------------------
# Quick smoke test
# ---------------------------------------------------------------------

if __name__ == "__main__":

    critical = critical_complaint_notification({
        "complaint_id": "C-205",
        "final_priority": "Critical",
        "suggested_action": "Immediate inspection",
        "human_review_required": True,
    })

    upcoming = upcoming_maintenance_notification(
        {
            "task_id": "T-101",
            "asset_id": "SIG-S02-04",
        },
        3,
    )

    overdue = overdue_maintenance_notification({
        "task_id": "T-102",
        "asset_id": "TRK-S01-02",
        "days_overdue": 5,
    })

    approval = approval_pending_notification({
        "block_id": "B-301",
        "status": "PENDING_APPROVAL",
    })

    print("CRITICAL:", critical)
    print("UPCOMING:", upcoming)
    print("OVERDUE:", overdue)
    print("APPROVAL:", approval)
