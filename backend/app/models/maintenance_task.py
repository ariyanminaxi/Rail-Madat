"""
RailMaintain — Task, AI Classification, and Maintenance Event Models

Maps to Supabase maintenance_tasks, ai_classifications, workflow_status_history.
"""

from datetime import datetime
from dataclasses import dataclass
from typing import Optional

MAINTENANCE_TYPES = ("Corrective", "Preventive")
PRIORITIES = ("Low", "Medium", "High", "Critical")
TASK_STATUSES = (
    "Reported", "Under Review", "Assigned", "Waiting for Block",
    "Scheduled", "In Progress", "Completed", "Deferred", "Rejected",
    "Duplicate", "Partially Completed", "Interrupted", "Cancelled",
    "Blocked", "Emergency", "Awaiting Materials",
    "Awaiting Human Verification", "Awaiting Communication",
    "Requires Inspection",
)
GROUPING_STATUSES = ("Recommended Bundle", "Conditional Bundle", "Rejected Bundle")
EXECUTION_MODES = ("Sequential", "Parallel", "Either")


@dataclass
class AIClassification:
    """Maps to Supabase ai_classifications table."""
    id: int = 0
    complaint_id: str = ""
    asset_type: str = ""
    department: str = ""
    fault_category: str = ""
    base_priority: str = ""
    confidence: int = 0
    human_review_required: bool = False
    reason: str = ""
    suggested_action: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class Task:
    """Maps to Supabase maintenance_tasks table."""
    task_id: str = ""
    source_type: str = ""
    source_id: str = ""
    complaint_id: Optional[str] = None
    schedule_id: Optional[str] = None
    asset_id: str = ""
    asset_type: str = ""
    section_id: str = ""
    department: str = ""
    fault_category: Optional[str] = None
    maintenance_type: str = "Corrective"
    base_priority: str = ""
    asset_criticality: Optional[str] = None
    overdue_days: int = 0
    deferral_count: int = 0
    escalation_level: int = 0
    final_priority: str = ""
    duration_minutes: int = 60
    required_team: Optional[str] = None
    required_equipment: Optional[str] = None
    due_date: Optional[datetime] = None
    block_required: bool = True
    status: str = "Reported"
    bundle_status: Optional[str] = None
    assigned_to: Optional[str] = None
    block_id: Optional[str] = None
    interruption_reason: Optional[str] = None
    exception_type: Optional[str] = None
    safety_status: Optional[str] = None
    remaining_work_minutes: Optional[int] = None
    resume_required: bool = False
    next_review_time: Optional[datetime] = None
    cancelled_reason: Optional[str] = None
    material_status: Optional[str] = None
    communication_status: Optional[str] = None
    last_known_location: Optional[str] = None
    execution_mode: Optional[str] = None
    work_area: Optional[str] = None
    safety_requirements: Optional[str] = None
    dependencies: Optional[str] = None
    grouping_allowed: bool = True
    grouping_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class MaintenanceEvent:
    """Maps to Supabase workflow_status_history table."""
    event_id: str = ""
    task_id: str = ""
    event_type: str = ""
    old_status: Optional[str] = None
    new_status: str = ""
    event_reason: Optional[str] = None
    reported_by: Optional[str] = None
    created_at: Optional[datetime] = None
    remaining_work_minutes: Optional[int] = None
    final_priority: Optional[str] = None
