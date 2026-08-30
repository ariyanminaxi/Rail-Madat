"""
RailMaintain — Work Completion Report Schema
"""

from typing import Optional
from pydantic import BaseModel


class WorkCompletionReportCreate(BaseModel):
    task_id: str
    receiver_department: str
    work_status: str
    completion_percentage: Optional[int] = None
    inspection_result: Optional[str] = None
    failure_reason: Optional[str] = None
    remaining_work_minutes: Optional[int] = None
    material_status: Optional[str] = None
    safety_status: Optional[str] = None
    next_action: Optional[str] = None
    remarks: Optional[str] = None
