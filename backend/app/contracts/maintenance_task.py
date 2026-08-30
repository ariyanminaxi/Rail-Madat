"""
RailMaintain — Maintenance Task and AI Classification Schemas
"""

from typing import Optional
from pydantic import BaseModel


class TaskOut(BaseModel):
    task_id: str
    source_type: str
    source_id: str
    asset_id: str
    asset_type: str
    section_id: str
    department: str
    maintenance_type: str
    base_priority: str
    final_priority: str
    duration_minutes: int
    due_date: Optional[str] = None
    block_required: bool
    status: str

    class Config:
        from_attributes = True


class AIClassificationIn(BaseModel):
    complaint_id: str
    asset_type: str
    department: str
    fault_category: str
    base_priority: str
    confidence: int
    human_review_required: bool
    reason: str
    suggested_action: Optional[str] = None
