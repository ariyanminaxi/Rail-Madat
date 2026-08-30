"""
RailMadat — Models

All models are simple dataclasses that map to Supabase tables.
No SQLAlchemy Base or engine needed.
"""

from app.models.user import Profile
from app.models.asset import Asset, MaintenanceRecord
from app.models.complaint import Complaint
from app.models.maintenance_task import Task, AIClassification, MaintenanceEvent
from app.models.scheduling_block import Block, Approval
from app.models.audit_event import AuditLog, Report
from app.models.notification import Notification
from app.models.work_completion import WorkCompletionReport
from app.models.maintenance_team import MaintenanceTeam
from app.models.offline_queue import OfflineQueueEntry

__all__ = [
    "Profile", "Asset", "MaintenanceRecord", "Complaint",
    "Task", "AIClassification", "MaintenanceEvent",
    "Block", "Approval", "AuditLog", "Report",
    "Notification", "WorkCompletionReport", "MaintenanceTeam",
    "OfflineQueueEntry",
]
