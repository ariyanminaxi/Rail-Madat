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

    comp = complaint.data[0]

    if decision == "verified":
        # Forward to AI classification pipeline
        # Map complaint to AI classification input
        asset_type = comp.get("asset_type", "Unknown")
        section_id = comp.get("section_id", "")
        description = comp.get("description", "")

        # Auto-classify based on asset type
        dept_map = {
            "Track": "Track",
            "Signal": "Signalling",
            "Electrical Equipment": "Electrical",
            "Point Machine": "Signalling",
            "Station Machinery": "Electrical",
        }
        department = dept_map.get(asset_type, "Track")

        # Map asset type to fault category
        fault_map = {
            "Track": "Track fracture",
            "Signal": "Signal malfunction",
            "Electrical Equipment": "Cable insulation fault",
            "Point Machine": "Point machine failure",
            "Station Machinery": "Station machinery breakdown",
        }
        fault_category = fault_map.get(asset_type, "General fault")

        # Determine priority from complaint priority
        priority = comp.get("priority", "Medium")

        # Create AI classification record
        ai_id = f"AI-{uuid.uuid4().int % 900 + 100}"
        admin.table("ai_classifications").insert({
            "classification_id": ai_id,
            "complaint_id": complaint_id,
            "department": department,
            "fault_category": fault_category,
            "severity": "High" if priority == "Critical" else "Medium",
            "base_priority": priority,
            "confidence": 0.85,
            "human_review_required": False,
        }).execute()

        # Create maintenance task (enters the main pipeline)
        import uuid as _uuid
        from datetime import datetime, timedelta, timezone
        task_id = f"T-{_uuid.uuid4().int % 900 + 100}"
        due = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        admin.table("maintenance_tasks").insert({
            "task_id": task_id,
            "source_type": "complaint",
            "source_id": complaint_id,
            "complaint_id": complaint_id,
            "asset_id": comp.get("asset_id", ""),
            "asset_type": asset_type,
            "section_id": section_id,
            "department": department,
            "fault_category": fault_category,
            "maintenance_type": "Corrective",
            "base_priority": priority,
            "final_priority": priority,
            "duration_minutes": 60,
            "due_date": due,
            "block_required": True,
            "status": "Waiting for Block",
        }).execute()

        # Update complaint status
        admin.table("complaints").update({"status": "Under Review"}).eq("complaint_id", complaint_id).execute()

        new_status = "Under Review"
    else:
        # Rejected - complaint is closed, ID is NOT reused
        admin.table("complaints").update({
            "status": "Rejected",
            "priority": "Low",
        }).eq("complaint_id", complaint_id).execute()
        new_status = "Rejected"

    # Audit log
    admin.table("audit_events").insert({
        "audit_id": f"AUD-{uuid.uuid4().int % 900 + 100}",
        "user_id": user.user_id,
        "role": user.role,
        "action": "INSPECTION_VERIFIED" if decision == "verified" else "INSPECTION_REJECTED",
        "resource_type": "complaint",
        "resource_id": complaint_id,
        "status": "SUCCESS",
    }).execute()

    return {
        "complaint_id": complaint_id,
        "status": new_status,
        "decision": decision,
        "notes": notes,
        "pipeline": "AI classification + task created" if decision == "verified" else None,
    }
