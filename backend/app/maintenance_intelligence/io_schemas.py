"""Pydantic schemas for Maintenance Intelligence input/output contracts."""

from typing import List, Optional
from pydantic import BaseModel


class ComplaintInput(BaseModel):
    """Stable input schema consumed by the Maintenance Intelligence Service."""

    complaint_text: str
    asset_type: Optional[str] = "Unknown"
    asset_criticality: Optional[str] = "Non-Critical"
    current_status: Optional[str] = "New"
    days_overdue: Optional[int] = 0
    failure_count_30_days: Optional[int] = 0
    safety_risk_level: Optional[str] = "Low"
    service_impact_level: Optional[str] = "Minor"
    asset_id: Optional[str] = None
    deferral_count: Optional[int] = 0
    reopen_count: Optional[int] = 0


class ServiceOutput(BaseModel):
    """Canonical output returned by the Maintenance Intelligence Service."""

    department: str
    fault_category: str
    severity: str
    base_priority: str
    final_priority: str
    recommended_action: str
    confidence: Optional[float] = None
    human_review_required: bool
    explanation: List[str]


class FeatureVector(BaseModel):
    """Internal feature representation for a single case."""

    complaint_text: str
    asset_type: str
    asset_criticality: str
    current_status: str
    days_overdue: int
    failure_count_30_days: int
    safety_risk_level: str
    service_impact_level: str


class ClassificationResult(BaseModel):
    """Raw classification output before prioritization rules."""

    department: str
    fault_category: str
    severity: str
    base_priority: str
    confidence: float
    recommended_action: str
