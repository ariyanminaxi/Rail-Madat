"""
RailMadat — Dashboard Routes

Uses Supabase client for all queries.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.database.database import get_supabase_admin
from app.authentication.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/alerts")
def get_alerts(
    unread_only: bool = False,
    user: CurrentUser = Depends(get_current_user),
):
    admin = get_supabase_admin()
    alerts = []

    # Try dashboard_alerts table first - filter by current user
    try:
        q = admin.table("dashboard_alerts").select("*").eq("user_id", user.user_id)
        if unread_only:
            q = q.eq("is_read", False)
        result = q.order("created_at", desc=True).limit(50).execute()
        alerts = result.data or []
    except Exception:
        pass

    # If empty, generate alerts from real data
    if not alerts:
        try:
            # Overdue assets
            assets = admin.table("asset_registry").select("*").eq("is_overdue", True).limit(10).execute()
            for a in (assets.data or []):
                alerts.append({
                    "alert_id": "ALT-" + a.get("asset_id", ""),
                    "alert_type": "overdue_maintenance",
                    "title": "Overdue Asset Maintenance",
                    "message": f"Asset {a.get('asset_id', '')} ({a.get('asset_type', '')}) is overdue for maintenance. Last maintained: {a.get('last_maintenance_date', 'N/A')}. Next due: {a.get('next_due_date', 'N/A')}.",
                    "severity": "High" if a.get("asset_criticality") in ("Critical", "High") else "Medium",
                    "created_at": a.get("next_due_date", ""),
                })
        except Exception:
            pass

        try:
            # Faulty assets
            faulty = admin.table("asset_registry").select("*").eq("current_status", "Faulty").limit(10).execute()
            for a in (faulty.data or []):
                alerts.append({
                    "alert_id": "ALT-FAULTY-" + a.get("asset_id", ""),
                    "alert_type": "faulty_asset",
                    "title": "Faulty Asset Reported",
                    "message": f"Asset {a.get('asset_id', '')} ({a.get('asset_type', '')}) at {a.get('city', '')} is currently faulty and needs attention.",
                    "severity": "High",
                    "created_at": a.get("next_due_date", ""),
                })
        except Exception:
            pass

        try:
            # Overdue schedules
            schedules = admin.table("maintenance_schedules").select("*").eq("is_overdue", True).limit(10).execute()
            for s in (schedules.data or []):
                alerts.append({
                    "alert_id": "ALT-SCH-" + s.get("schedule_id", ""),
                    "alert_type": "overdue_schedule",
                    "title": "Overdue Maintenance Schedule",
                    "message": f"Schedule {s.get('schedule_id', '')} for asset {s.get('asset_id', '')} is overdue. Activity: {s.get('activity', '')}.",
                    "severity": "Medium",
                    "created_at": s.get("next_due_date", ""),
                })
        except Exception:
            pass

        try:
            # Critical/High priority tasks
            tasks = admin.table("maintenance_tasks").select("*").in_("priority", ["Critical", "High"]).in_("status", ["Reported", "Under Review", "Waiting for Block"]).limit(10).execute()
            for t in (tasks.data or []):
                alerts.append({
                    "alert_id": "ALT-TASK-" + t.get("task_id", ""),
                    "alert_type": "pending_task",
                    "title": "High Priority Task Pending",
                    "message": f"Task {t.get('task_id', '')} for {t.get('asset_id', '')} ({t.get('fault_category', '')}) is {t.get('status', '')}.",
                    "severity": t.get("priority", "Medium"),
                    "created_at": t.get("due_date", ""),
                })
        except Exception:
            pass

    # Sort by severity then date
    sev_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    alerts.sort(key=lambda a: (sev_order.get(a.get("severity", "Medium"), 2), a.get("created_at", "")), reverse=True)

    return alerts[:50]


@router.post("/alerts/{alert_id}/read")
def mark_alert_read(alert_id: str, user: CurrentUser = Depends(get_current_user)):
    admin = get_supabase_admin()
    try:
        admin.table("notifications").update({"is_read": True}).eq("notification_id", alert_id).execute()
    except Exception:
        pass
    return {"status": "ok"}


@router.get("/stats")
def get_stats(user: CurrentUser = Depends(get_current_user)):
    admin = get_supabase_admin()

    # Safely query each table
    try:
        complaints = admin.table("complaints").select("complaint_id, status, reporter_user_id").execute()
        all_complaints = complaints.data or []
    except Exception:
        all_complaints = []

    try:
        tasks = admin.table("maintenance_tasks").select("task_id, status, priority, assigned_team_id").execute()
        all_tasks = tasks.data or []
    except Exception:
        all_tasks = []

    try:
        audits = admin.table("audit_events").select("audit_id, status").execute()
        all_audits = audits.data or []
    except Exception:
        all_audits = []

    stats = {
        "total_complaints": len(all_complaints),
        "open_complaints": len([c for c in all_complaints if c.get("status") in ("Reported", "Under Review", "Assigned")]),
        "in_progress": len([c for c in all_complaints if c.get("status") == "In Progress"]),
        "completed": len([c for c in all_complaints if c.get("status") == "Completed"]),
        "total_tasks": len(all_tasks),
        "critical_tasks": len([t for t in all_tasks if t.get("priority") == "Critical"]),
        "overdue_tasks": len([t for t in all_tasks if t.get("status") == "Overdue"]),
        "pending_audits": len([a for a in all_audits if a.get("status") == "denied"]),
    }

    role = user.role
    if role == "Reporter":
        stats["my_complaints"] = len([c for c in all_complaints if c.get("reporter_user_id") == user.user_id])
    elif role == "Maintenance staff":
        stats["my_tasks"] = len([t for t in all_tasks if t.get("assigned_team_id")])
    elif role in ("Maintenance Manager", "Administrator"):
        stats["pending_approvals"] = len([t for t in all_tasks if t.get("status") == "Waiting for Block"])

    return stats
