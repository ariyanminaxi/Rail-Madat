"""
RailMadat — Complaint Schemas
"""

from typing import Optional
from pydantic import BaseModel


class ComplaintCreate(BaseModel):
    state: str
    city: str
    description: str
    asset_type: str
    section_id: str
    asset_id: str


class ComplaintOut(BaseModel):
    complaint_id: str
    reporter_user_id: str
    state: str
    city: str
    description: str
    asset_type: str
    section_id: str
    asset_id: str
    status: str
    priority: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
