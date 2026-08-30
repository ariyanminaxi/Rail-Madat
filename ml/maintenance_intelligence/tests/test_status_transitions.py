"""Status transition tests."""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import VALID_PRIORITIES
from app.maintenance_intelligence.prioritization.priority_engine import (
    calculate_final_priority, priority_order, requires_human_review,
)
from app.contracts.workflow_status import VALID_STATUSES


class TestValidStatuses:
    @pytest.mark.parametrize("status", VALID_STATUSES)
    def test_valid_status_no_crash(self, status):
        result = calculate_final_priority(
            {"base_priority": "Medium"},
            {"asset_criticality": "Non-Critical", "current_status": status, "safety_risk_level": "Low"},
        )
        assert result["final_priority"] in VALID_PRIORITIES

    def test_escalated_escalates(self):
        result = calculate_final_priority(
            {"base_priority": "Low"},
            {"asset_criticality": "Non-Critical", "current_status": "Escalated", "safety_risk_level": "Low"},
        )
        assert result["final_priority"] == "Critical"

    def test_completed_no_escalation(self):
        result = calculate_final_priority(
            {"base_priority": "Low"},
            {"asset_criticality": "Non-Critical", "current_status": "Completed", "safety_risk_level": "Low"},
        )
        assert result["final_priority"] == "Low"


class TestInvalidStatuses:
    @pytest.mark.parametrize("status", ["RandomStatus", "AwaitingMaterials", "Deferred", "Closed", ""])
    def test_invalid_status_no_crash(self, status):
        result = calculate_final_priority(
            {"base_priority": "Medium"},
            {"asset_criticality": "Non-Critical", "current_status": status, "safety_risk_level": "Low"},
        )
        assert result["final_priority"] in VALID_PRIORITIES


class TestStatusPriorityBehaviors:
    def test_safety_critical_interrupted_critical(self):
        result = calculate_final_priority(
            {"base_priority": "Low"},
            {"asset_criticality": "Safety-Critical", "current_status": "Interrupted", "safety_risk_level": "High"},
        )
        assert result["final_priority"] == "Critical"

    def test_extreme_risk_always_emergency(self):
        for status in ["New", "In Progress", "Interrupted", "Reopened", "Completed"]:
            result = calculate_final_priority(
                {"base_priority": "Low"},
                {"asset_criticality": "Non-Critical", "current_status": status, "safety_risk_level": "Extreme"},
            )
            assert result["final_priority"] == "Emergency"
