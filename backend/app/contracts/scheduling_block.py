"""
RailMaintain — Scheduling Block and Approval Schemas
"""

from typing import Optional
from pydantic import BaseModel


class BlockOut(BaseModel):
    block_id: str
    section_id: str
    start_time: str
    end_time: str
    safety_buffer_minutes: int
    recommendation_reason: str
    approval_status: str

    class Config:
        from_attributes = True


class ApprovalCreate(BaseModel):
    block_id: str
    decision: str
    reason: Optional[str] = None


class ApprovalOut(BaseModel):
    approval_id: str
    block_id: str
    approver_user_id: str
    decision: str
    reason: Optional[str] = None
    decided_at: Optional[str] = None

    class Config:
        from_attributes = True
