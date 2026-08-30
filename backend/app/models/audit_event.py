"""
RailMaintain — Audit Log and Report Models

Maps to Supabase audit_events and reports tables.
"""

from datetime import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class AuditLog:
    """Maps to Supabase audit_events table."""
    audit_id: str = ""
    user_id: Optional[str] = None
    role: Optional[str] = None
    action: str = ""
    resource_type: str = ""
    resource_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    status: str = ""


@dataclass
class Report:
    """Maps to Supabase reports table."""
    report_id: str = ""
    report_type: str = ""
    generated_at: Optional[datetime] = None
    data_summary: Optional[str] = None
    download_url: Optional[str] = None
