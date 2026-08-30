"""
RailMaintain — Scheduling Block and Approval Models

Maps to Supabase maintenance_blocks and approvals tables.
"""

from datetime import datetime
from dataclasses import dataclass
from typing import Optional

BLOCK_APPROVAL_STATUSES = ("Pending", "Approved", "Rejected", "Modified")
GROUPING_STATUSES = ("Recommended Bundle", "Conditional Bundle", "Rejected Bundle")


@dataclass
class Block:
    """Maps to Supabase maintenance_blocks table."""
    block_id: str = ""
    section_id: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    combined_tasks: Optional[str] = None
    affected_trains: Optional[str] = None
    safety_buffer_minutes: int = 15
    resource_conflicts: Optional[str] = None
    recommendation_reason: str = ""
    rejected_alternatives: Optional[str] = None
    approval_status: str = "Pending"
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    grouping_status: Optional[str] = None
    execution_plan: Optional[str] = None
    conditions: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class Approval:
    """Maps to Supabase approvals table."""
    approval_id: str = ""
    block_id: str = ""
    approver_user_id: str = ""
    decision: str = ""
    reason: Optional[str] = None
    decided_at: Optional[datetime] = None
