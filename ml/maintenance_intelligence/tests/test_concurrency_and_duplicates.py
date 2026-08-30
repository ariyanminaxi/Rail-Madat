"""Concurrency and duplicate submission tests."""

import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.inference.classifier import classify_case
from app.maintenance_intelligence.prioritization.priority_engine import calculate_final_priority
from app.maintenance_intelligence.io_schemas import ComplaintInput


class TestTCConcurrent001:
    def test_same_complaint_same_result(self):
        c = ComplaintInput(complaint_text="Signal near S-02 is flickering.", asset_type="Signal",
                           asset_criticality="Safety-Critical", safety_risk_level="High")
        r1 = classify_case(c)
        r2 = classify_case(c)
        assert r1["department"] == r2["department"]
        assert r1["base_priority"] == r2["base_priority"]

    def test_idempotent(self):
        c = ComplaintInput(complaint_text="Track defect at km 45.", asset_type="Track", safety_risk_level="Medium")
        results = [classify_case(c) for _ in range(5)]
        for r in results:
            assert r["department"] == results[0]["department"]


class TestTCConcurrent002:
    def test_two_status_updates_consistent(self):
        prediction = {"base_priority": "High"}
        r1 = calculate_final_priority(prediction, {"asset_criticality": "Safety-Critical", "current_status": "Interrupted", "safety_risk_level": "High"})
        r2 = calculate_final_priority(prediction, {"asset_criticality": "Safety-Critical", "current_status": "Reopened", "safety_risk_level": "High"})
        assert r1["final_priority"] == "Critical"
        assert r2["final_priority"] == "Critical"


class TestTCConcurrent003:
    def test_deterministic(self):
        for _ in range(10):
            result = calculate_final_priority(
                {"base_priority": "Medium"},
                {"asset_criticality": "Safety-Critical", "current_status": "Escalated", "safety_risk_level": "High"},
            )
            assert result["final_priority"] == "Critical"


class TestTCConcurrent004:
    def test_concurrent_priority_rules(self):
        test_cases = [
            ({"base_priority": "Low"}, {"asset_criticality": "Non-Critical", "current_status": "New", "safety_risk_level": "Low"}),
            ({"base_priority": "High"}, {"asset_criticality": "Safety-Critical", "current_status": "Interrupted", "safety_risk_level": "High"}),
            ({"base_priority": "Medium"}, {"asset_criticality": "Non-Critical", "current_status": "New", "safety_risk_level": "Extreme"}),
        ]
        results = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(calculate_final_priority, p, c) for p, c in test_cases]
            for f in as_completed(futures):
                results.append(f.result())
        priorities = {r["final_priority"] for r in results}
        assert "Low" in priorities
        assert "Critical" in priorities
        assert "Emergency" in priorities
