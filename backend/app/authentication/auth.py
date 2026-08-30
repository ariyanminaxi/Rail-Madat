"""
RailMadat — Authentication & Authorization

Verifies Supabase-issued JWTs via Supabase API (handles ES256/HS256 automatically).
Uses Supabase client for all profile lookups.
"""

import uuid
from fastapi import Depends, Header, HTTPException, status

from app.database.database import get_supabase_admin


class CurrentUser:
    """Authenticated user context attached to every request."""

    def __init__(self, user_id, role: str, display_name: str):
        self.user_id = user_id
        self.role = role
        self.display_name = display_name


def _log_audit(user_id, role, action: str,
               resource_type: str, resource_id, result: str) -> None:
    """Write an audit entry via Supabase client."""
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


def get_current_user(
    authorization: str = Header(..., alias="Authorization"),
) -> CurrentUser:
    """FastAPI dependency: verify the current user via Supabase API."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Missing or malformed bearer token",
        )

    token = authorization.split(" ", 1)[1]

    # Verify token via Supabase API (handles ES256/HS256 automatically)
    admin = get_supabase_admin()
    try:
        user_response = admin.auth.get_user(token)
    except Exception as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            f"Invalid or expired token: {exc}",
        )

    if not user_response or not user_response.user:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid or expired token",
        )

    supabase_user_id = user_response.user.id

    # Look up profile by supabase_user_id
    profile_result = (
        admin.table("users")
        .select("*")
        .eq("supabase_user_id", supabase_user_id)
        .limit(1)
        .execute()
    )

    if not profile_result.data:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "No profile found for this account — ask an Administrator to assign a role.",
        )

    profile = profile_result.data[0]

    if not profile.get("is_active", True):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Account is deactivated.",
        )

    return CurrentUser(
        user_id=profile["id"],
        role=profile["role"],
        display_name=profile.get("full_name", profile.get("display_name", "User")),
    )


def require_role(*allowed_roles: str):
    """Dependency factory enforcing RBAC."""

    def checker(
        user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if user.role not in allowed_roles:
            _log_audit(
                user.user_id, user.role,
                "ACCESS_DENIED", "endpoint", None, "denied",
            )
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Not authorized for this action",
            )
        return user

    return checker
