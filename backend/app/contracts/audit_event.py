"""
RailMaintain — Audit Log and Report Schemas
"""

from typing import Optional
from pydantic import BaseModel


class AuditLogOut(BaseModel):
    audit_id: str
    user_id: Optional[str] = None
    role: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    timestamp: Optional[str] = None
    status: str

    class Config:
        from_attributes = True
