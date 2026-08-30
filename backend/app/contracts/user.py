"""
RailMaintain — User Profile Schema
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class ProfileOut(BaseModel):
    id: str
    supabase_user_id: str | None = None
    email: str
    full_name: str
    role: str
    department: str | None = None
    section_id: str | None = None
    phone: str | None = None
    is_active: bool | str = True
    created_at: datetime | None = None

    class Config:
        from_attributes = True
