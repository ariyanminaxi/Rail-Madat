"""
RailMadat — Asset Routes

Uses Supabase client for all queries.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException

from app.database.database import get_supabase_admin
from app.contracts.asset import AssetCreate, AssetOut
from app.authentication.auth import CurrentUser, get_current_user, require_role

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.post("", status_code=201)
def create_asset(
    payload: AssetCreate,
    user: CurrentUser = Depends(require_role("Administrator", "Maintenance Manager")),
):
    admin = get_supabase_admin()
    existing = admin.table("asset_registry").select("asset_id").eq("asset_id", payload.asset_id).limit(1).execute()
    if existing.data:
        raise HTTPException(409, f"Asset {payload.asset_id} already exists")

    admin.table("asset_registry").insert({
        "asset_id": payload.asset_id,
        "asset_type": payload.asset_type,
        "section_id": payload.section_id,
        "department": payload.department,
        "asset_criticality": payload.asset_criticality,
        "operational_status": "Reported",
        "is_overdue": False,
    }).execute()

    return {"asset_id": payload.asset_id, "status": "created"}


@router.get("/{asset_id}")
def get_asset(asset_id: str, user: CurrentUser = Depends(get_current_user)):
    admin = get_supabase_admin()
    result = admin.table("asset_registry").select("*").eq("asset_id", asset_id).limit(1).execute()
    if not result.data:
        raise HTTPException(404, "Asset not found")
    return result.data[0]


@router.get("")
def list_assets(user: CurrentUser = Depends(get_current_user)):
    admin = get_supabase_admin()
    result = admin.table("asset_registry").select("*").limit(200).execute()
    return result.data or []
