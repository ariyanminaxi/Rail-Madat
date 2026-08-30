"""
RailMadat — User Profile Model

The users table is managed directly via Supabase.
This module provides a simple data class for type hints.
"""

from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

USER_ROLES = ("Reporter", "Maintenance staff", "Maintenance Manager", "Administrator")


@dataclass
class Profile:
    """Maps to the Supabase users table."""
    id: str = ""
    supabase_user_id: Optional[str] = None
    email: str = ""
    full_name: str = ""
    display_name: str = ""  # alias for full_name
    role: str = ""
    department: Optional[str] = None
    section_id: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.display_name and self.full_name:
            self.display_name = self.full_name
