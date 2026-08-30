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
    due = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    task_data = {
        "task_id": task_id,
        "source_type": "complaint",
        "source_id": payload.complaint_id,
        "complaint_id": payload.complaint_id,
        "asset_id": complaint.data[0].get("asset_id", ""),
        "asset_type": payload.asset_type,
        "section_id": complaint.data[0].get("section_id", ""),
        "department": payload.department,
        "fault_category": payload.fault_category,
        "maintenance_type": "Corrective",
        "base_priority": payload.base_priority,
        "final_priority": payload.base_priority,
        "duration_minutes": 60,
        "due_date": due,
        "block_required": True,
        "status": "Under Review" if payload.human_review_required else "Waiting for Block",
    }
    admin.table("maintenance_tasks").insert(task_data).execute()

    # Update complaint status
    admin.table("complaints").update({"status": task_data["status"]}).eq("complaint_id", payload.complaint_id).execute()

    _log_audit(user.user_id, user.role, "CREATE", "task", task_id, "success")
    return task_data


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
