"""
RailMaintain — Complaint Model

Maps to Supabase complaints table.
"""

from datetime import datetime
from dataclasses import dataclass
from typing import Optional

COMPLAINT_STATUSES = (
    "Reported", "Under Review", "Assigned", "Waiting for Block",
    "Scheduled", "In Progress", "Completed", "Deferred", "Rejected",
    "Duplicate", "Partially Completed", "Interrupted", "Cancelled",
    "Blocked", "Emergency", "Awaiting Materials",
)


@dataclass
class Complaint:
    """Maps to Supabase complaints table."""
    complaint_id: str = ""
    client_complaint_id: str = ""
    reporter_user_id: str = ""
    state: str = ""
    city: str = ""
    description: str = ""
    asset_type: str = ""
    section_id: str = ""
    asset_id: str = ""
    status: str = "Reported"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
