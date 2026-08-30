"""
RailMaintain — Offline Queue Model

Maps to Supabase offline_queue table.
"""

from datetime import datetime
from dataclasses import dataclass
from typing import Optional

SYNC_STATUSES = ("DRAFT", "QUEUED", "SYNCING", "SYNCED", "FAILED_RETRY", "NEEDS_REVIEW")


@dataclass
class OfflineQueueEntry:
    """Maps to Supabase offline_queue table."""
    id: int = 0
    client_complaint_id: str = ""
    payload: str = ""
    created_at: Optional[datetime] = None
    queued_at: Optional[datetime] = None
    retry_count: int = 0
    last_retry_at: Optional[datetime] = None
    sync_status: str = "QUEUED"
    last_error: Optional[str] = None
