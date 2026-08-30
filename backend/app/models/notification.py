"""
RailMaintain — Notification Model

Maps to Supabase notifications table.
"""

from datetime import datetime
from dataclasses import dataclass
from typing import Optional

PRIORITIES = ("Low", "Medium", "High", "Critical")


@dataclass
class Notification:
    """Maps to Supabase notifications table."""
    notification_id: str = ""
    notification_type: str = ""
    message: str = ""
    related_task_id: Optional[str] = None
    related_asset_id: Optional[str] = None
    priority: str = ""
    created_at: Optional[datetime] = None
    is_read: bool = False
