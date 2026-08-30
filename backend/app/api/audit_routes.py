"""
RailMadat — Audit Routes

Uses Supabase client for all queries.
"""

from fastapi import APIRouter, Depends

from app.database.database import get_supabase_admin
from app.authentication.auth import CurrentUser, require_role

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/logs")
def list_audit_logs(
    user: CurrentUser = Depends(require_role("Maintenance Manager", "Administrator")),
):
    admin = get_supabase_admin()
    try:
        result = admin.table("audit_events").select("*").order("timestamp", desc=True).limit(200).execute()
        return result.data or []
    except Exception:
        return []
