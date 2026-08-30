"""
RailMaintain — Work Completion Report Model

Maps to Supabase work_completions table.
"""

from datetime import datetime
from dataclasses import dataclass
from typing import Optional

DEPARTMENTS = ("Track", "Signalling", "Electrical")
RECEIVER_WORK_STATUSES = ("Completed", "Partially Completed", "Not Completed", "Interrupted", "Awaiting Materials", "Cancelled", "Emergency")


@dataclass
class WorkCompletionReport:
    """Maps to Supabase work_completions table."""
    completion_report_id: str = ""
    task_id: str = ""
    receiver_department: str = ""
    received_by: Optional[str] = None
    received_at: Optional[datetime] = None
    work_status: str = ""
    completion_percentage: Optional[int] = None
    inspection_result: Optional[str] = None
    failure_reason: Optional[str] = None
    remaining_work_minutes: Optional[int] = None
    material_status: Optional[str] = None
    safety_status: Optional[str] = None
    next_action: Optional[str] = None
    remarks: Optional[str] = None
    created_at: Optional[datetime] = None
