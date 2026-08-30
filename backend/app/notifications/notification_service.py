"""
RailMaintain - Notification Service

Role 6:
Receives notification data from notification_rules.py,
stores notifications for the MVP dashboard, and provides
simple functions to retrieve and mark notifications.

MVP storage is in memory.
A production system can replace this with a database/queue.

Dashboard alerts (the MVP deliverable) are the primary output.
External delivery (email, SMS, push) is deferred to post-MVP.
"""

from datetime import datetime, timezone
from typing import Optional
import threading


# ---------------------------------------------------------------------------
# Dashboard alert types matching the spec
# ---------------------------------------------------------------------------

CRITICAL_TASK = "CRITICAL_TASK"
EMERGENCY_TASK = "EMERGENCY_TASK"
HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
OVERDUE_MAINTENANCE = "OVERDUE_MAINTENANCE"
UPCOMING_MAINTENANCE = "UPCOMING_MAINTENANCE"
WORK_INTERRUPTED = "WORK_INTERRUPTED"
TASK_REQUEUED = "TASK_REQUEUED"
RESOURCE_UNAVAILABLE = "RESOURCE_UNAVAILABLE"
SCHEDULING_APPROVAL_REQUIRED = "SCHEDULING_APPROVAL_REQUIRED"
BUNDLE_INVALIDATED = "BUNDLE_INVALIDATED"
TEAM_REASSIGNED = "TEAM_REASSIGNED"
FAILED_SYNC = "FAILED_SYNC"
INCOMPLETE_WORK = "INCOMPLETE_WORK"
MATERIALS_UNAVAILABLE = "MATERIALS_UNAVAILABLE"
EMERGENCY = "EMERGENCY"


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

class NotificationService:
    """Simple notification manager for the RailMaintain MVP."""

    def __init__(self):
        self._notifications: list[dict] = []
        self._next_id = 1
        self._lock = threading.Lock()

    def create_notification(
        self,
        notification: dict,
        recipient_role: Optional[str] = None,
        recipient_user_id: Optional[str] = None,
    ) -> dict:
        """Store a notification and return the stored record."""

        if not isinstance(notification, dict):
            raise TypeError("notification must be a dictionary")

        if not notification.get("notification_type"):
            raise ValueError("notification_type is required")

        if not notification.get("title"):
            raise ValueError("notification title is required")

        with self._lock:
            current_id = self._next_id
            self._next_id += 1

        record = {
            "notification_id": f"N-{current_id:04d}",
            "notification_type": notification["notification_type"],
            "title": notification["title"],
            "message": notification.get("message", ""),
            "recipient_role": recipient_role,
            "recipient_user_id": recipient_user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "read": False,
            "status": "ACTIVE",
            **{
                key: value
                for key, value in notification.items()
                if key not in {
                    "notification_type",
                    "title",
                    "message",
                }
            },
        }

        with self._lock:
            self._notifications.append(record)

        return record

    def get_notifications(
        self,
        unread_only: bool = False,
        notification_type: Optional[str] = None,
    ) -> list[dict]:
        """Return notifications, optionally filtered."""

        with self._lock:
            results = list(self._notifications)

        if unread_only:
            results = [n for n in results if not n["read"]]

        if notification_type:
            results = [
                n for n in results
                if n["notification_type"] == notification_type
            ]

        return results

    def mark_as_read(self, notification_id: str) -> bool:
        """Mark a notification as read. Returns True if found."""
        with self._lock:
            for n in self._notifications:
                if n["notification_id"] == notification_id:
                    n["read"] = True
                    return True
        return False

    def reset(self) -> None:
        """Clear all notifications. FOR TEST USE ONLY."""
        with self._lock:
            self._notifications.clear()
            self._next_id = 1


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_default_service = NotificationService()


def get_notification_service() -> NotificationService:
    """Return the module-level notification service singleton."""
    return _default_service


# ---------------------------------------------------------------------------
# Dashboard alert convenience functions
# ---------------------------------------------------------------------------

def create_dashboard_alert(
    user_id: str,
    alert_type: str,
    title: str,
    message: str,
    resource_type: str,
    resource_id: str,
    priority: Optional[str] = None,
) -> dict:
    """Create a dashboard alert and store it via the notification service.

    Returns the stored alert record with an alert_id field.
    """
    if not user_id:
        raise ValueError("user_id is required")
    if not alert_type:
        raise ValueError("alert_type is required")
    if not resource_type:
        raise ValueError("resource_type is required")
    if not resource_id:
        raise ValueError("resource_id is required")

    notification = {
        "notification_type": alert_type,
        "title": title,
        "message": message,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "priority": priority,
    }

    record = _default_service.create_notification(
        notification=notification,
        recipient_user_id=user_id,
    )

    # Map notification_id to alert_id for spec compliance
    record["alert_id"] = record["notification_id"]
    record["is_read"] = record["read"]

    return record


def get_dashboard_alerts(
    user_id: Optional[str] = None,
    unread_only: bool = False,
) -> list[dict]:
    """Retrieve dashboard alerts, optionally filtered by user and read status."""
    alerts = _default_service.get_notifications(unread_only=unread_only)

    if user_id:
        alerts = [
            a for a in alerts
            if a.get("recipient_user_id") == user_id
        ]

    # Add is_read alias
    for a in alerts:
        a["is_read"] = a["read"]

    return alerts


def mark_alert_as_read(alert_id: str, user_id: str) -> bool:
    """Mark a dashboard alert as read. Returns True if found."""
    return _default_service.mark_as_read(alert_id)


# ---------------------------------------------------------------------------
# Supabase-backed dashboard alerts (DATA_MODE=supabase)
# ---------------------------------------------------------------------------

def _get_supabase_client():
    """Lazy-load the Supabase client for dashboard alerts."""
    try:
        from app.config import SUPABASE_URL, SUPABASE_ANON_KEY
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            return None
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    except Exception:
        return None


def create_dashboard_alert_supabase(
    user_id: str,
    alert_type: str,
    title: str,
    message: str,
    resource_type: str,
    resource_id: str,
    priority: Optional[str] = None,
) -> dict:
    """Create a dashboard alert and persist to Supabase."""
    client = _get_supabase_client()
    if client is None:
        # Fall back to in-memory storage
        return create_dashboard_alert(
            user_id, alert_type, title, message,
            resource_type, resource_id, priority,
        )

    from datetime import datetime, timezone
    alert = {
        "user_id": user_id,
        "alert_type": alert_type,
        "title": title,
        "message": message,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "priority": priority or "Medium",
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    result = client.table("dashboard_alerts").insert(alert).execute()
    if result.data:
        return result.data[0]
    return alert


def get_dashboard_alerts_supabase(
    user_id: str,
    unread_only: bool = False,
) -> list[dict]:
    """Retrieve dashboard alerts from Supabase."""
    client = _get_supabase_client()
    if client is None:
        return get_dashboard_alerts(user_id=user_id, unread_only=unread_only)

    query = (
        client.table("dashboard_alerts")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
    )

    if unread_only:
        query = query.eq("is_read", False)

    result = query.execute()
    return result.data or []


def mark_alert_as_read_supabase(alert_id: str, user_id: str) -> bool:
    """Mark a dashboard alert as read in Supabase."""
    client = _get_supabase_client()
    if client is None:
        return mark_alert_as_read(alert_id, user_id)

    result = (
        client.table("dashboard_alerts")
        .update({"is_read": True})
        .eq("id", alert_id)
        .eq("user_id", user_id)
        .execute()
    )
    return bool(result.data)
