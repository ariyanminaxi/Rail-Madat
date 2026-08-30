"""Shared Maintenance Intelligence prediction contract used by FastAPI and the service."""

from typing import List, Optional
from pydantic import BaseModel


class MaintenancePrediction(BaseModel):
    department: str
    fault_category: str
    severity: str
    base_priority: str
    final_priority: str
    recommended_action: str
    confidence: Optional[float] = None
    human_review_required: bool
    explanation: List[str]
