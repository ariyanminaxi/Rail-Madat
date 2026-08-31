"""
RailMadat — Scheduling & Approval Routes

Uses Supabase client for all queries.
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException

from app.database.database import get_supabase_admin
from app.contracts.scheduling_block import ApprovalCreate
from app.authentication.auth import CurrentUser, get_current_user, require_role

router = APIRouter(tags=["Scheduling"])


def _gen_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().int % 900 + 100}"


@router.get("/blocks")
def list_blocks(user: CurrentUser = Depends(get_current_user)):
    admin = get_supabase_admin()
    try:
        result = admin.table("maintenance_blocks").select("*").order("created_at", desc=True).limit(50).execute()
        return result.data or []
    except Exception:
        return []


@router.get("/blocks/{block_id}")
def get_block(block_id: str, user: CurrentUser = Depends(get_current_user)):
    admin = get_supabase_admin()
    result = admin.table("maintenance_blocks").select("*").eq("block_id", block_id).limit(1).execute()
    if not result.data:
        raise HTTPException(404, "Block not found")
    return result.data[0]


@router.post("/approvals", status_code=201)
def create_approval(
    payload: ApprovalCreate,
    user: CurrentUser = Depends(require_role("Maintenance Manager")),
):
    admin = get_supabase_admin()
    block = admin.table("maintenance_blocks").select("*").eq("block_id", payload.block_id).limit(1).execute()
    if not block.data:
        raise HTTPException(400, f"Unknown block_id {payload.block_id}")
    if payload.decision not in ("Approved", "Rejected", "Modified"):
        raise HTTPException(400, "decision must be Approved | Rejected | Modified")

    approval_id = _gen_id("A")
    admin.table("approvals").insert({
        "approval_id": approval_id,
        "block_id": payload.block_id,
        "approver_user_id": user.user_id,
        "decision": payload.decision,
        "reason": payload.reason,
    }).execute()

    admin.table("maintenance_blocks").update({
        "approval_status": payload.decision,
        "approved_by": user.user_id,
        "approved_at": datetime.now(timezone.utc).isoformat(),
    }).eq("block_id", payload.block_id).execute()

    return {"approval_id": approval_id, "block_id": payload.block_id, "decision": payload.decision}
