"""
RailMaintain — Maintenance Team Model

Maps to Supabase maintenance_teams table.
"""

from datetime import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class MaintenanceTeam:
    """Maps to Supabase maintenance_teams table."""
    id: int = 0
    team_id: str = ""
    team_name: str = ""
    department: str = ""
    section_id: Optional[str] = None
    team_lead_user_id: Optional[str] = None
    member_count: int = 0
    status: str = "Available"
    current_task_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
