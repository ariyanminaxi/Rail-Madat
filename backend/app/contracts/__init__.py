"""
RailMaintain — Pydantic Request/Response Contracts

Schemas are split by domain entity. Import from specific submodules
or use this package-level import for convenience.
"""

from app.contracts.authentication import LoginRequest, LoginResponse
from app.contracts.user import ProfileOut
from app.contracts.complaint import ComplaintCreate, ComplaintOut
from app.contracts.asset import AssetCreate, AssetOut
from app.contracts.maintenance_task import TaskOut, AIClassificationIn
from app.contracts.scheduling_block import BlockOut, ApprovalCreate, ApprovalOut
from app.contracts.completion_report import WorkCompletionReportCreate
from app.contracts.audit_event import AuditLogOut

__all__ = [
    "LoginRequest", "LoginResponse",
    "ProfileOut",
    "ComplaintCreate", "ComplaintOut",
    "AssetCreate", "AssetOut",
    "TaskOut", "AIClassificationIn",
    "BlockOut", "ApprovalCreate", "ApprovalOut",
    "WorkCompletionReportCreate",
    "AuditLogOut",
]
