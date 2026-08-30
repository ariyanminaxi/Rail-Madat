"""
RailMaintain — Asset and Maintenance Record Models

Maps to Supabase asset_registry and maintenance_history tables.
"""

from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

DEPARTMENTS = ("Track", "Signalling", "Electrical")
ASSET_TYPES = ("Track", "Signal", "Electrical Equipment", "Point Machine", "Station Machinery")
PRIORITIES = ("Low", "Medium", "High", "Critical")
RECEIVER_WORK_STATUSES = ("Completed", "Partially Completed", "Not Completed", "Interrupted", "Awaiting Materials", "Cancelled", "Emergency")


@dataclass
class Asset:
    """Maps to Supabase asset_registry table."""
    id: int = 0
    asset_id: str = ""
    asset_type: str = ""
    asset_subtype: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    section_id: str = ""
    department: str = ""
    asset_criticality: str = ""
    operational_status: str = "Working"
    last_maintenance_date: Optional[datetime] = None
    next_due_date: Optional[datetime] = None
    is_overdue: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    current_status: str = "Reported"  # compatibility alias
    maintenance_interval_days: int = 0


@dataclass
class MaintenanceRecord:
    """Maps to Supabase maintenance_history table."""
    record_id: str = ""
    task_id: Optional[str] = None
    asset_id: str = ""
    scheduled_date: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    performed_by: Optional[str] = None
    inspection_result: Optional[str] = None
    defects_found: Optional[str] = None
    corrective_action: Optional[str] = None
    materials_used: Optional[str] = None
    completion_status: Optional[str] = None
    next_due_date: Optional[datetime] = None
    remarks: Optional[str] = None
