"""
RailMadat — Alert Helper

Creates and manages notifications in the dashboard_alerts table.
Called from workflow routes to generate notifications at each step.

Flow:
  1. Reporter files complaint    → Notify Inspectors
  2. Inspector verifies          → Notify Scheduler/Manager
  3. Inspector rejects           → Notify Reporter (closed)
  4. Manager approves block      → Notify assigned Staff
  5. Staff completes work        → Notify Reporter (resolved)
  6. Work interrupted/re-queued  → Notify Manager + Staff (re-opened)
  7. Complaint completed         → Clear related notifications
"""

import uuid
from datetime import datetime, timezone
from app.database.database import get_supabase_admin


def _gen_alert_id() -> str:
    return f"ALT-{uuid.uuid4().int % 9000 + 1000}"


def _get_admin():
    return get_supabase_admin()


def create_alert(
    user_id: str,
    alert_type: str,
    title: str,
    message: str,
    resource_type: str,
    resource_id: str,
    severity: str = "Medium",
) -> dict:
    """Create a notification in dashboard_alerts table."""
    admin = _get_admin()
    alert = {
        "alert_id": _gen_alert_id(),
        "user_id": user_id,
        "alert_type": alert_type,
        "title": title,
        "message": message,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "severity": severity,
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        result = admin.table("dashboard_alerts").insert(alert).execute()
        return result.data[0] if result.data else alert
    except Exception as e:
        print(f"[AlertHelper] Failed to create alert: {e}")
        return alert


def notify_inspectors_new_complaint(complaint_id: str, asset_type: str, city: str, priority: str):
    """Step 1: Reporter files complaint → Notify all inspectors."""
    admin = _get_admin()
    try:
        inspectors = admin.table("users").select("id").eq("role", "Inspector").eq("is_active", True).execute()
        for ins in (inspectors.data or []):
            create_alert(
                user_id=ins["id"],
                alert_type="new_complaint",
                title=f"New Complaint: {complaint_id}",
                message=f"New {priority} priority {asset_type} complaint reported at {city}. Requires inspection before AI analysis.",
                resource_type="complaint",
                resource_id=complaint_id,
                severity=priority,
            )
    except Exception as e:
        print(f"[AlertHelper] notify_inspectors error: {e}")


def notify_reporter_complaint_verified(complaint_id: str, reporter_user_id: str):
    """Step 2: Inspector verifies → Notify reporter it's been forwarded."""
    create_alert(
        user_id=reporter_user_id,
        alert_type="complaint_verified",
        title=f"Complaint {complaint_id} Verified",
        message=f"Your complaint {complaint_id} has been verified by an inspector and forwarded to AI analysis.",
        resource_type="complaint",
        resource_id=complaint_id,
        severity="Medium",
    )


def notify_reporter_complaint_rejected(complaint_id: str, reporter_user_id: str, reason: str):
    """Step 3: Inspector rejects → Notify reporter it's been closed."""
    create_alert(
        user_id=reporter_user_id,
        alert_type="complaint_rejected",
        title=f"Complaint {complaint_id} Rejected",
        message=f"Your complaint {complaint_id} was not verified. Reason: {reason}",
        resource_type="complaint",
        resource_id=complaint_id,
        severity="Low",
    )


def notify_managers_scheduling_needed(complaint_id: str, task_id: str, asset_type: str, priority: str):
    """Step 4: AI classified → Notify managers that scheduling is needed."""
    admin = _get_admin()
    try:
        managers = admin.table("users").select("id").in_("role", ["Maintenance_Manager", "Administrator"]).eq("is_active", True).execute()
        for m in (managers.data or []):
            create_alert(
                user_id=m["id"],
                alert_type="scheduling_needed",
                title=f"Scheduling Required: {task_id}",
                message=f"Task {task_id} for {asset_type} ({priority}) needs a maintenance block. Please review and approve.",
                resource_type="task",
                resource_id=task_id,
                severity=priority,
            )
    except Exception as e:
        print(f"[AlertHelper] notify_managers error: {e}")


def notify_staff_task_assigned(task_id: str, team_id: str, asset_type: str, section_id: str):
    """Step 5: Block approved → Notify assigned staff team."""
    admin = _get_admin()
    try:
        # Get team members (or notify by section/department)
        create_alert(
            user_id=team_id,  # team_id used as user_id for team notifications
            alert_type="task_assigned",
            title=f"Task Assigned: {task_id}",
            message=f"You have been assigned task {task_id} for {asset_type} in section {section_id}. Work block has been approved.",
            resource_type="task",
            resource_id=task_id,
            severity="High",
        )
    except Exception as e:
        print(f"[AlertHelper] notify_staff error: {e}")


def notify_reporter_work_completed(complaint_id: str, reporter_user_id: str):
    """Step 6: Work completed → Notify reporter issue is resolved."""
    create_alert(
        user_id=reporter_user_id,
        alert_type="work_completed",
        title=f"Issue Resolved: {complaint_id}",
        message=f"Your complaint {complaint_id} has been completed. The issue has been addressed.",
        resource_type="complaint",
        resource_id=complaint_id,
        severity="Low",
    )


def notify_work_interrupted(task_id: str, complaint_id: str, reason: str):
    """Step 7: Work interrupted → Notify managers and re-open pipeline."""
    admin = _get_admin()
    try:
        managers = admin.table("users").select("id").in_("role", ["Maintenance_Manager", "Administrator"]).eq("is_active", True).execute()
        for m in (managers.data or []):
            create_alert(
                user_id=m["id"],
                alert_type="work_interrupted",
                title=f"Work Interrupted: {task_id}",
                message=f"Task {task_id} for complaint {complaint_id} was interrupted. Reason: {reason}. Re-entering scheduling pipeline.",
                resource_type="task",
                resource_id=task_id,
                severity="High",
            )
    except Exception as e:
        print(f"[AlertHelper] notify_interrupted error: {e}")


def clear_notifications_for_resource(resource_type: str, resource_id: str):
    """Clear all notifications for a completed/resolved resource."""
    admin = _get_admin()
    try:
        result = (
            admin.table("dashboard_alerts")
            .select("id")
            .eq("resource_type", resource_type)
            .eq("resource_id", resource_id)
            .execute()
        )
        for row in (result.data or []):
            admin.table("dashboard_alerts").delete().eq("id", row["id"]).execute()
        return len(result.data or [])
    except Exception as e:
        print(f"[AlertHelper] clear_notifications error: {e}")
        return 0


def get_notifications_for_user(user_id: str, unread_only: bool = False):
    """Get notifications for a specific user."""
    admin = _get_admin()
    try:
        q = admin.table("dashboard_alerts").select("*").eq("user_id", user_id)
        if unread_only:
            q = q.eq("is_read", False)
        result = q.order("created_at", desc=True).limit(50).execute()
        return result.data or []
    except Exception:
        return []


def mark_notification_read(alert_id: str):
    """Mark a notification as read."""
    admin = _get_admin()
    try:
        admin.table("dashboard_alerts").update({"is_read": True}).eq("alert_id", alert_id).execute()
        return True
    except Exception:
        return False
