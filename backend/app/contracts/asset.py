"""
RailMaintain — Asset Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AssetCreate(BaseModel):
    asset_id: str
    asset_type: str
    section_id: str
    department: str
    asset_criticality: str
    maintenance_interval_days: int
    last_maintenance_date: Optional[datetime] = None
    next_due_date: Optional[datetime] = None


class AssetOut(AssetCreate):
    current_status: str
    is_overdue: bool

    class Config:
        from_attributes = True
