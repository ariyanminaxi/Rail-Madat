"""
Tests for notification_service.py — Dashboard alert creation,
retrieval, filtering, and mark-as-read.
"""

import pytest
from app.notifications.notification_service import (
    NotificationService,
    create_dashboard_alert,
    get_dashboard_alerts,
    mark_alert_as_read,
)


# ---------------------------------------------------------
# Fixtures
# ---------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_service():
    """Reset the global notification service before each test."""
    from app.notifications import notification_service
    notification_service._default_service.reset()
    yield
    notification_service._default_service.reset()


# ---------------------------------------------------------
# 1. Dashboard alert creation
# ---------------------------------------------------------

def test_create_dashboard_alert_returns_record():
    alert = create_dashboard_alert(
        user_id="USER-MANAGER-001",
        alert_type="HUMAN_REVIEW_REQUIRED",
        title="Critical task requires review",
        message="Task T-001 requires manager verification.",
        resource_type="maintenance_task",
        resource_id="T-001",
        priority="Critical",
    )
    assert "alert_id" in alert
    assert alert["notification_type"] == "HUMAN_REVIEW_REQUIRED"
    assert alert["title"] == "Critical task requires review"
    assert alert["priority"] == "Critical"
    assert alert["is_read"] is False


def test_create_alert_has_iso_timestamp():
    alert = create_dashboard_alert(
        user_id="U-001",
        alert_type="OVERDUE_MAINTENANCE",
        title="Overdue",
        message="Task is overdue",
        resource_type="maintenance_task",
        resource_id="T-002",
    )
    assert "T" in alert["created_at"]


# ---------------------------------------------------------
# 2. Alert retrieval
# ---------------------------------------------------------

def test_get_dashboard_alerts_returns_list():
    create_dashboard_alert(
        user_id="U-001",
        alert_type="CRITICAL_TASK",
        title="Critical",
        message="msg",
        resource_type="task",
        resource_id="T-1",
    )
    alerts = get_dashboard_alerts()
    assert len(alerts) >= 1


def test_get_dashboard_alerts_filter_by_user():
    create_dashboard_alert(
        user_id="U-001",
        alert_type="CRITICAL_TASK",
        title="Critical",
        message="msg",
        resource_type="task",
        resource_id="T-1",
    )
    create_dashboard_alert(
        user_id="U-002",
        alert_type="CRITICAL_TASK",
        title="Critical",
        message="msg",
        resource_type="task",
        resource_id="T-2",
    )
    alerts_u1 = get_dashboard_alerts(user_id="U-001")
    assert all(a["recipient_user_id"] == "U-001" for a in alerts_u1)


# ---------------------------------------------------------
# 3. Unread-only filtering
# ---------------------------------------------------------

def test_unread_only_filtering():
    alert = create_dashboard_alert(
        user_id="U-001",
        alert_type="TASK_REQUEUED",
        title="Requeued",
        message="msg",
        resource_type="task",
        resource_id="T-3",
    )
    # All unread initially
    unread = get_dashboard_alerts(unread_only=True)
    assert len(unread) >= 1

    # Mark one as read
    mark_alert_as_read(alert["alert_id"], "U-001")
    unread_after = get_dashboard_alerts(unread_only=True)
    assert not any(a["alert_id"] == alert["alert_id"] for a in unread_after)


# ---------------------------------------------------------
# 4. Mark alert as read
# ---------------------------------------------------------

def test_mark_alert_as_read():
    alert = create_dashboard_alert(
        user_id="U-001",
        alert_type="WORK_INTERRUPTED",
        title="Interrupted",
        message="msg",
        resource_type="task",
        resource_id="T-4",
    )
    result = mark_alert_as_read(alert["alert_id"], "U-001")
    assert result is True

    alerts = get_dashboard_alerts()
    for a in alerts:
        if a["alert_id"] == alert["alert_id"]:
            assert a["is_read"] is True


def test_mark_nonexistent_alert_returns_false():
    result = mark_alert_as_read("N-9999", "U-001")
    assert result is False


# ---------------------------------------------------------
# 5. Error handling
# ---------------------------------------------------------

def test_missing_user_id_raises():
    with pytest.raises(ValueError, match="user_id"):
        create_dashboard_alert(
            user_id="",
            alert_type="EMERGENCY",
            title="Emergency",
            message="msg",
            resource_type="task",
            resource_id="T-5",
        )


def test_missing_resource_id_raises():
    with pytest.raises(ValueError, match="resource_id"):
        create_dashboard_alert(
            user_id="U-001",
            alert_type="EMERGENCY",
            title="Emergency",
            message="msg",
            resource_type="task",
            resource_id="",
        )


def test_missing_alert_type_raises():
    with pytest.raises(ValueError, match="alert_type"):
        create_dashboard_alert(
            user_id="U-001",
            alert_type="",
            title="Emergency",
            message="msg",
            resource_type="task",
            resource_id="T-5",
        )


# ---------------------------------------------------------
# 6. NotificationService direct usage
# ---------------------------------------------------------

def test_notification_service_create_and_get():
    svc = NotificationService()
    svc.create_notification({
        "notification_type": "TEST",
        "title": "Test Notification",
        "message": "Hello",
    })
    notes = svc.get_notifications()
    assert len(notes) == 1
    assert notes[0]["notification_type"] == "TEST"


def test_notification_service_type_error():
    svc = NotificationService()
    with pytest.raises(TypeError, match="dictionary"):
        svc.create_notification("not a dict")


def test_notification_service_missing_type():
    svc = NotificationService()
    with pytest.raises(ValueError, match="notification_type"):
        svc.create_notification({"title": "T"})


def test_notification_service_missing_title():
    svc = NotificationService()
    with pytest.raises(ValueError, match="title"):
        svc.create_notification({"notification_type": "X"})


# ---------------------------------------------------------
# 7. No external provider dependency
# ---------------------------------------------------------

def test_no_external_provider_imports():
    """The notification service should not import smtplib, twilio, etc."""
    import app.notifications.notification_service as ns_mod
    import inspect
    source = inspect.getsource(ns_mod)
    for forbidden in ["smtplib", "twilio", "firebase", "websocket", "requests.post"]:
        assert forbidden not in source
