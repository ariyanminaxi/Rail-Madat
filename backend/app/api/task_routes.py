"""
RailMadat — Task Routes

Handles AI classification hand-off, task creation, and task retrieval.
Uses Supabase client for all queries.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException

from app.database.database import get_supabase_admin
from app.contracts.maintenance_task import TaskOut, AIClassificationIn
from app.authentication.auth import CurrentUser, get_current_user

router = APIRouter(tags=["Tasks"])


def _gen_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().int % 900 + 100}"


def _log_audit(user_id, role, action, resource_type, resource_id, result):
    admin = get_supabase_admin()
    try:
        admin.table("audit_events").insert({
            "audit_id": f"AUD-{uuid.uuid4().int % 900 + 100}",
            "user_id": user_id, "role": role, "action": action,
            "resource_type": resource_type, "resource_id": resource_id, "status": result,
        }).execute()
    except Exception:
        pass


@router.post("/ai/classifications", status_code=201)
def receive_ai_classification(
    payload: AIClassificationIn,
    user: CurrentUser = Depends(get_current_user),
):
    """Receive AI classification result and create a maintenance task."""
    admin = get_supabase_admin()

    # Verify complaint exists
    complaint = admin.table("complaints").select("*").eq("complaint_id", payload.complaint_id).limit(1).execute()
    if not complaint.data:
        raise HTTPException(400, f"Unknown complaint_id {payload.complaint_id}")

    # Create task
    task_id = _gen_id("T")
    task_data = {
        "task_id": task_id,
        "complaint_id": payload.complaint_id,
        "asset_id": complaint.data[0].get("asset_id", ""),
        "section_id": complaint.data[0].get("section_id", ""),
        "department": payload.department,
        "priority": payload.base_priority,
        "status": "Under_Review" if payload.human_review_required else "Waiting_for_Block",
    }
    admin.table("maintenance_tasks").insert(task_data).execute()

    # Update complaint status
    admin.table("complaints").update({"status": task_data["status"]}).eq("complaint_id", payload.complaint_id).execute()

    _log_audit(user.user_id, user.role, "CREATE", "task", task_id, "success")
    return task_data


@router.post("/tasks/{task_id}/approve")
def approve_task(task_id: str, user: CurrentUser = Depends(get_current_user)):
    admin = get_supabase_admin()
    result = admin.table("maintenance_tasks").select("*").eq("task_id", task_id).limit(1).execute()
    if not result.data:
        raise HTTPException(404, "Task not found")
    task = result.data[0]
    if task.get("status") not in ("Waiting_for_Block", "Under_Review", "Reported"):
        raise HTTPException(400, f"Task is {task.get('status')}, cannot approve")
    admin.table("maintenance_tasks").update({"status": "Scheduled"}).eq("task_id", task_id).execute()
    # Also update complaint status
    complaint_id = task.get("complaint_id")
    if complaint_id:
        admin.table("complaints").update({"status": "Scheduled"}).eq("complaint_id", complaint_id).execute()
    _log_audit(user.user_id, user.role, "APPROVE", "task", task_id, "success")

    # Notify reporter that their complaint is being worked on
    try:
        from app.notifications.alert_helper import notify_reporter_work_completed
        complaint_id = task.get("complaint_id")
        if complaint_id:
            comp = admin.table("complaints").select("reporter_user_id").eq("complaint_id", complaint_id).limit(1).execute()
            if comp.data:
                notify_reporter_work_completed(complaint_id, comp.data[0].get("reporter_user_id", ""))
    except Exception:
        pass

    return {"task_id": task_id, "status": "Scheduled"}


@router.post("/tasks/{task_id}/reject")
def reject_task(task_id: str, reason: str = "", user: CurrentUser = Depends(get_current_user)):
    admin = get_supabase_admin()
    result = admin.table("maintenance_tasks").select("*").eq("task_id", task_id).limit(1).execute()
    if not result.data:
        raise HTTPException(404, "Task not found")
    admin.table("maintenance_tasks").update({"status": "Deferred"}).eq("task_id", task_id).execute()
    # Also update complaint status
    complaint_id = task.get("complaint_id")
    if complaint_id:
        admin.table("complaints").update({"status": "Deferred"}).eq("complaint_id", complaint_id).execute()
    _log_audit(user.user_id, user.role, "REJECT", "task", task_id, "success")

    # Notify reporter their complaint was deferred
    try:
        from app.notifications.alert_helper import notify_reporter_complaint_rejected
        complaint_id = task.get("complaint_id")
        if complaint_id:
            comp = admin.table("complaints").select("reporter_user_id").eq("complaint_id", complaint_id).limit(1).execute()
            if comp.data:
                notify_reporter_complaint_rejected(complaint_id, comp.data[0].get("reporter_user_id", ""), "Task deferred by manager")
    except Exception:
        pass

    return {"task_id": task_id, "status": "Deferred"}


@router.get("/tasks/{task_id}")
def get_task(task_id: str, user: CurrentUser = Depends(get_current_user)):
    admin = get_supabase_admin()
    result = admin.table("maintenance_tasks").select("*").eq("task_id", task_id).limit(1).execute()
    if not result.data:
        raise HTTPException(404, "Task not found")
    return result.data[0]


@router.get("/tasks")
def list_tasks(status_filter: Optional[str] = None, user: CurrentUser = Depends(get_current_user)):
    admin = get_supabase_admin()
    try:
        q = admin.table("maintenance_tasks").select("*")
        if status_filter:
            q = q.eq("status", status_filter)
        result = q.limit(100).execute()
        return result.data or []
    except Exception:
        return []
