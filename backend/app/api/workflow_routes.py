"""
RailMadat — Workflow / Audit Routes

Returns workflow_status_history entries, optionally filtered by complaint_id.
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.database.database import get_supabase_admin
from app.authentication.auth import CurrentUser, get_current_user

router = APIRouter(tags=["Workflow"])


@router.get("/workflow/history")
def get_workflow_history(
    complaint_id: Optional[str] = Query(None),
    task_id: Optional[str] = Query(None),
    user: CurrentUser = Depends(get_current_user),
):
    """Get workflow status history, optionally filtered by complaint_id or task_id."""
    admin = get_supabase_admin()
    q = admin.table("workflow_status_history").select("*")

    if complaint_id:
        q = q.eq("complaint_id", complaint_id)
    if task_id:
        q = q.eq("task_id", task_id)

    result = q.order("changed_at", desc=False).limit(200).execute()
    return result.data or []
