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
    try:
        q = admin.table("dashboard_alerts").select("*")
        if unread_only:
            q = q.eq("is_read", False)
        result = q.order("created_at", desc=True).limit(50).execute()
        return result.data or []
    except Exception:
        return []


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
