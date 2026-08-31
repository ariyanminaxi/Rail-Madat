"""
RailMadat — Work Completion Routes

Uses Supabase client for all queries.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException

from app.database.database import get_supabase_admin
from app.authentication.auth import CurrentUser, get_current_user, require_role

router = APIRouter(tags=["Work Completion"])


@router.post("/work-completion-reports", status_code=201)
def submit_completion_report(
    payload: dict,
    user: CurrentUser = Depends(require_role("Maintenance staff", "Maintenance Manager")),
):
    admin = get_supabase_admin()
    task_id = payload.get("task_id")
    if not task_id:
        raise HTTPException(400, "task_id is required")

    task = admin.table("maintenance_tasks").select("*").eq("task_id", task_id).limit(1).execute()
    if not task.data:
        raise HTTPException(400, f"Unknown task_id {task_id}")

    report_id = f"WCR-{uuid.uuid4().int % 900 + 100}"
    admin.table("work_completions").insert({
        "completion_report_id": report_id,
        "task_id": task_id,
        "receiver_department": payload.get("receiver_department", ""),
        "received_by": user.user_id,
        "work_status": payload.get("work_status", ""),
        "completion_percentage": payload.get("completion_percentage"),
        "inspection_result": payload.get("inspection_result"),
        "failure_reason": payload.get("failure_reason"),
        "remaining_work_minutes": payload.get("remaining_work_minutes"),
        "material_status": payload.get("material_status"),
        "safety_status": payload.get("safety_status"),
        "next_action": payload.get("next_action"),
        "remarks": payload.get("remarks"),
    }).execute()

    # Update task status
    new_status = "Completed" if payload.get("work_status") == "Completed" else payload.get("work_status", "Interrupted")
    admin.table("maintenance_tasks").update({"status": new_status}).eq("task_id", task_id).execute()

    # Notifications based on work status
    try:
        from app.notifications.alert_helper import (
            notify_reporter_work_completed,
            notify_work_interrupted,
            clear_notifications_for_resource,
        )
        complaint_id = task.data[0].get("complaint_id")
        if complaint_id:
            comp = admin.table("complaints").select("reporter_user_id").eq("complaint_id", complaint_id).limit(1).execute()
            reporter_id = comp.data[0].get("reporter_user_id", "") if comp.data else ""

            if new_status == "Completed":
                # Notify reporter and clear pending notifications
                if reporter_id:
                    notify_reporter_work_completed(complaint_id, reporter_id)
                admin.table("complaints").update({"status": "Completed"}).eq("complaint_id", complaint_id).execute()
                clear_notifications_for_resource("complaint", complaint_id)
                clear_notifications_for_resource("task", task_id)
            else:
                # Work interrupted - notify managers, re-enter pipeline
                notify_work_interrupted(task_id, complaint_id, payload.get("failure_reason", "Work interrupted"))
                admin.table("maintenance_tasks").update({"status": "Waiting_for_Block"}).eq("task_id", task_id).execute()
                admin.table("complaints").update({"status": "Under_Review"}).eq("complaint_id", complaint_id).execute()
    except Exception:
        pass

    return {"completion_report_id": report_id, "task_status": new_status}
