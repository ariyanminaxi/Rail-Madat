"""
RailMadat — Authentication Routes

Handles login (proxied to Supabase Auth) and user profile retrieval.
Uses Supabase client for all queries.
"""

import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import create_client

from app.config import SUPABASE_URL, SUPABASE_ANON_KEY
from app.database.database import get_supabase_admin
from app.contracts.authentication import LoginRequest, LoginResponse
from app.contracts.user import ProfileOut
from app.authentication.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def _log_audit(user_id, role, action: str,
               resource_type: str, resource_id, result: str) -> None:
    """Write an audit entry."""
    admin = get_supabase_admin()
    try:
        admin.table("audit_events").insert({
            "audit_id": f"AUD-{uuid.uuid4().int % 900 + 100}",
            "user_id": user_id,
            "role": role,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "status": result,
        }).execute()
    except Exception:
        pass


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    """Authenticate user via Supabase Auth and return access token."""
    try:
        result = supabase.auth.sign_in_with_password(
            {"email": payload.email, "password": payload.password}
        )
    except Exception:
        _log_audit(None, None, "LOGIN", "session", None, "denied")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    supa_user = result.user

    # Look up profile by supabase_user_id first, then by email as fallback
    admin = get_supabase_admin()
    profile_result = (
        admin.table("users")
        .select("*")
        .eq("supabase_user_id", supa_user.id)
        .limit(1)
        .execute()
    )

    # Fallback: match by email if supabase_user_id not linked yet
    if not profile_result.data and supa_user.email:
        profile_result = (
            admin.table("users")
            .select("*")
            .eq("email", supa_user.email)
            .limit(1)
            .execute()
        )
        # Auto-link the supabase_user_id for next time
        if profile_result.data:
            try:
                admin.table("users").update(
                    {"supabase_user_id": supa_user.id}
                ).eq("id", profile_result.data[0]["id"]).execute()
            except Exception:
                pass

    if not profile_result.data:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Login succeeded but no role is assigned — ask an Administrator to set one up.",
        )

    profile = profile_result.data[0]
    _log_audit(profile["id"], profile["role"], "LOGIN", "session", None, "success")

    return LoginResponse(
        access_token=result.session.access_token,
        user_id=profile["id"],
        role=profile["role"],
        display_name=profile.get("full_name", profile.get("display_name", "User")),
    )


@router.get("/me", response_model=ProfileOut)
def whoami(user: CurrentUser = Depends(get_current_user)):
    """Return the current authenticated user's profile."""
    admin = get_supabase_admin()
    result = (
        admin.table("users")
        .select("*")
        .eq("id", user.user_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(404, "Profile not found")
    return result.data[0]
