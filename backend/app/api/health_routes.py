"""
RailMaintain — Health Check Routes
"""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
def health():
    """Basic health check endpoint."""
    return {"status": "ok"}
