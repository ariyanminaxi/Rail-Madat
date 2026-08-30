"""
RailMaintain — API Routes

All route modules are registered here for inclusion in main.py.
"""

from app.api.auth_routes import router as auth_router
from app.api.complaint_routes import router as complaint_router
from app.api.task_routes import router as task_router
from app.api.asset_routes import router as asset_router
from app.api.scheduling_routes import router as scheduling_router
from app.api.work_completion_routes import router as work_completion_router
from app.api.audit_routes import router as audit_router
from app.api.health_routes import router as health_router
from app.api.dashboard_routes import router as dashboard_router
from app.api.inspection_routes import router as inspection_router
from app.api.team_routes import router as team_router
from app.api.workflow_routes import router as workflow_router

ALL_ROUTERS = [
    auth_router,
    complaint_router,
    task_router,
    asset_router,
    scheduling_router,
    work_completion_router,
    audit_router,
    health_router,
    dashboard_router,
    inspection_router,
    team_router,
    workflow_router,
]

__all__ = ["ALL_ROUTERS"]
