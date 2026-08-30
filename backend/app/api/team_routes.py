"""
RailMadat — Team Routes

Uses Supabase client for all queries.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.database.database import get_supabase_admin
from app.authentication.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("")
def list_teams(user: CurrentUser = Depends(get_current_user)):
    admin = get_supabase_admin()
    result = admin.table("maintenance_teams").select("*").execute()
    return result.data or []


@router.get("/{team_id}")
def get_team(team_id: str, user: CurrentUser = Depends(get_current_user)):
    admin = get_supabase_admin()
    result = admin.table("maintenance_teams").select("*").eq("team_id", team_id).limit(1).execute()
    if not result.data:
        raise HTTPException(404, "Team not found")
    return result.data[0]
