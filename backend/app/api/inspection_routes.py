"""
RailMadat — Inspection Routes

Handles inspector verification workflow.
Uses Supabase client for all queries.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException

from app.database.database import get_supabase_admin
from app.authentication.auth import CurrentUser, get_current_user, require_role

router = APIRouter(prefix="/inspections", tags=["Inspections"])


@router.get("/pending")
def get_pending_inspections(
    user: CurrentUser = Depends(require_role("Inspector", "Maintenance Manager", "Administrator")),
):
    admin = get_supabase_admin()
    result = (
        admin.table("complaints")
        .select("*")
        .in_("status", ["Reported", "Under Review"])
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return result.data or []


@router.post("/verify")
def verify_complaint(
    payload: dict,
    user: CurrentUser = Depends(require_role("Inspector", "Maintenance Manager", "Administrator")),
):
    admin = get_supabase_admin()
    complaint_id = payload.get("complaint_id")
    decision = payload.get("decision")
    notes = payload.get("notes", "")

    if not complaint_id or decision not in ("verified", "rejected"):
        raise HTTPException(400, "complaint_id and decision (verified/rejected) are required")

    complaint = admin.table("complaints").select("*").eq("complaint_id", complaint_id).limit(1).execute()
    if not complaint.data:
        raise HTTPException(404, "Complaint not found")

    new_status = "Under Review" if decision == "verified" else "Rejected"
    admin.table("complaints").update({"status": new_status}).eq("complaint_id", complaint_id).execute()

    admin.table("audit_events").insert({
        "audit_id": f"AUD-{uuid.uuid4().int % 900 + 100}",
        "user_id": user.user_id,
        "role": user.role,
        "action": "INSPECTION_VERIFIED" if decision == "verified" else "INSPECTION_REJECTED",
        "resource_type": "complaint",
        "resource_id": complaint_id,
        "status": "SUCCESS",
    }).execute()

    return {"complaint_id": complaint_id, "status": new_status, "decision": decision, "notes": notes}
