"""
RailMadat — Database Configuration

Uses Supabase client for all queries (no direct PostgreSQL needed).
This avoids needing DATABASE_URL with a password.
"""

import os
from functools import lru_cache
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")


@lru_cache
def get_supabase_anon() -> Client:
    """RLS-respecting client for user-scoped queries."""
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


@lru_cache
def get_supabase_admin() -> Client:
    """RLS-bypassing client for server-side operations."""
    if not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is not set in .env")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


# Compatibility shims for old code that imports get_db, Base, engine
# These are no longer needed but kept for import compatibility
def get_db():
    """No-op: kept for backward compatibility."""
    raise RuntimeError("Use get_supabase_anon() or get_supabase_admin() instead")
    yield  # Make it a generator


class _FakeBase:
    """Placeholder for SQLAlchemy Base — not used with Supabase client."""
    metadata = None


Base = _FakeBase()
engine = None
SessionLocal = None
