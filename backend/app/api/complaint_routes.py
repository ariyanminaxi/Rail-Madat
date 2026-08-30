"""
RailMadat — Complaint Routes

Handles complaint creation, retrieval, and listing.
Enriches complaints with AI classification data (priority, severity, etc.).
Uses Supabase client for all queries.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException

from app.database.database import get_supabase_admin
from app.contracts.complaint import ComplaintCreate
from app.authentication.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/complaints", tags=["Complaints"])


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


def _enrich_complaint(complaint, ai_map=None):
    if ai_map is None:
        ai_map = {}
    cid = complaint.get("complaint_id", "")
    ai = ai_map.get(cid, {})
    complaint["priority"] = complaint.get("priority") or ai.get("base_priority") or "Medium"
    complaint["severity"] = ai.get("severity", "")
    complaint["department"] = ai.get("department", "")
    complaint["fault_category"] = ai.get("fault_category", "")
    complaint["confidence_score"] = ai.get("confidence", None)
    return complaint


def _build_ai_map():
    admin = get_supabase_admin()
    try:
        result = admin.table("ai_classifications").select(
            "complaint_id,base_priority,severity,department,fault_category,confidence"
        ).execute()
        return {r["complaint_id"]: r for r in (result.data or [])}
    except Exception:
        return {}


@router.post("", status_code=201)
def create_complaint(payload: ComplaintCreate, user: CurrentUser = Depends(get_current_user)):
    admin = get_supabase_admin()
    complaint_id = _gen_id("C")

    complaint_data = {
        "complaint_id": complaint_id,
        "reporter_user_id": user.user_id,
        "state": payload.state,
        "city": payload.city,
        "description": payload.description,
        "asset_type": payload.asset_type,
        "section_id": payload.section_id,
        "asset_id": payload.asset_id,
        "status": "Reported",
        "priority": "Medium",
    }

    try:
        admin.table("complaints").insert(complaint_data).execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create complaint: {str(e)}")

    _log_audit(user.user_id, user.role, "CREATE", "complaint", complaint_id, "success")
    return complaint_data


@router.get("/{complaint_id}")
def get_complaint(complaint_id: str, user: CurrentUser = Depends(get_current_user)):
    admin = get_supabase_admin()
    result = admin.table("complaints").select("*").eq("complaint_id", complaint_id).limit(1).execute()
    if not result.data:
        raise HTTPException(404, "Complaint not found")

    complaint = result.data[0]
    if user.role == "Reporter" and complaint.get("reporter_user_id") != user.user_id:
        raise HTTPException(403, "Not authorized to view this complaint")

    ai_map = _build_ai_map()
    return _enrich_complaint(complaint, ai_map)


@router.get("")
def list_complaints(user: CurrentUser = Depends(get_current_user)):
    admin = get_supabase_admin()
    q = admin.table("complaints").select("*")
    if user.role == "Reporter":
        q = q.eq("reporter_user_id", user.user_id)
    result = q.order("created_at", desc=True).limit(100).execute()
    complaints = result.data or []
    ai_map = _build_ai_map()
    return [_enrich_complaint(c, ai_map) for c in complaints]
