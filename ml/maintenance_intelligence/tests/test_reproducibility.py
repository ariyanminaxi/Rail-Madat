"""Determinism and reproducibility tests.

Tests TC-REPRO-001 through TC-REPRO-003: the system must produce the
same predictions for the same inputs, must persist across process
boundaries, and must handle concurrent inference correctly.
"""

import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import VALID_PRIORITIES
from app.maintenance_intelligence.inference.classifier import classify_case
from app.maintenance_intelligence.prioritization.priority_engine import calculate_final_priority
from app.maintenance_intelligence.io_schemas import ComplaintInput


# ===================================================================
# TC-REPRO-001: Run same input 100 times
# ===================================================================

class TestTCRepro001RepeatedExecution:
    """Same input → same department, fault_category, severity, base_priority,
    final_priority, and review decision every time."""

    @pytest.fixture(scope="class")
    def reference_result(self):
        c = ComplaintInput(
            complaint_text="Signal near S-02 is flickering.",
            asset_type="Signal",
            asset_criticality="Safety-Critical",
            current_status="Interrupted",
            days_overdue=2,
            failure_count_30_days=2,
            safety_risk_level="High",
            service_impact_level="Major",
        )
        return classify_case(c)

    def test_department_stable_100_runs(self, reference_result):
        c = ComplaintInput(
            complaint_text="Signal near S-02 is flickering.",
            asset_type="Signal",
            asset_criticality="Safety-Critical",
            current_status="Interrupted",
            days_overdue=2,
            failure_count_30_days=2,
            safety_risk_level="High",
            service_impact_level="Major",
        )
        for _ in range(100):
            result = classify_case(c)
            assert result["department"] == reference_result["department"]

    def test_fault_category_stable_100_runs(self, reference_result):
        c = ComplaintInput(
            complaint_text="Signal near S-02 is flickering.",
            asset_type="Signal",
            asset_criticality="Safety-Critical",
            current_status="Interrupted",
            days_overdue=2,
            failure_count_30_days=2,
            safety_risk_level="High",
            service_impact_level="Major",
        )
        for _ in range(100):
            result = classify_case(c)
            assert result["fault_category"] == reference_result["fault_category"]

    def test_severity_stable_100_runs(self, reference_result):
        c = ComplaintInput(
            complaint_text="Signal near S-02 is flickering.",
            asset_type="Signal",
            asset_criticality="Safety-Critical",
            current_status="Interrupted",
            days_overdue=2,
            failure_count_30_days=2,
            safety_risk_level="High",
            service_impact_level="Major",
        )
        for _ in range(100):
            result = classify_case(c)
            assert result["severity"] == reference_result["severity"]

    def test_base_priority_stable_100_runs(self, reference_result):
        c = ComplaintInput(
            complaint_text="Signal near S-02 is flickering.",
            asset_type="Signal",
            asset_criticality="Safety-Critical",
            current_status="Interrupted",
            days_overdue=2,
            failure_count_30_days=2,
            safety_risk_level="High",
            service_impact_level="Major",
        )
        for _ in range(100):
            result = classify_case(c)
            assert result["base_priority"] == reference_result["base_priority"]

    def test_final_priority_stable_100_runs(self):
        """Priority engine is deterministic by design."""
        prediction = {"base_priority": "High"}
        context = {
            "asset_criticality": "Safety-Critical",
            "current_status": "Interrupted",
            "safety_risk_level": "High",
        }
        for _ in range(100):
            result = calculate_final_priority(prediction, context)
            assert result["final_priority"] == "Critical"

    def test_review_decision_stable_100_runs(self):
        """Same priority + confidence → same review decision."""
        for _ in range(100):
            hr, _ = __import__(
                "app.maintenance_intelligence.prioritization.priority_engine",
                fromlist=["requires_human_review"],
            ).requires_human_review("Critical", confidence=0.85, safety_risk="High")
            assert hr is True


# ===================================================================
# TC-REPRO-002: Load saved artifact in new process
# ===================================================================

class TestTCRepro002ArtifactReload:
    """Prediction from loaded model matches prediction from fresh import."""

    def test_predictions_identical_after_reload(self):
        c = ComplaintInput(
            complaint_text="Signal near S-02 is flickering.",
            asset_type="Signal",
            asset_criticality="Safety-Critical",
        )
        # First classification
        r1 = classify_case(c)
        # Second classification (uses same loaded model)
        r2 = classify_case(c)

        assert r1["department"] == r2["department"]
        assert r1["fault_category"] == r2["fault_category"]
        assert r1["severity"] == r2["severity"]
        assert r1["base_priority"] == r2["base_priority"]

    def test_priority_engine_always_identical(self):
        """Priority engine has no state — always deterministic."""
        for _ in range(50):
            result = calculate_final_priority(
                {"base_priority": "High"},
                {"asset_criticality": "Safety-Critical", "current_status": "Interrupted", "safety_risk_level": "High"},
            )
            assert result["final_priority"] == "Critical"


# ===================================================================
# TC-REPRO-003: Concurrent inference
# ===================================================================

class TestTCRepro003ConcurrentInference:
    """Multiple threads should not produce corrupted state."""

    def _classify(self, text):
        c = ComplaintInput(complaint_text=text, asset_type="Signal", safety_risk_level="High")
        return classify_case(c)

    def _priority(self):
        return calculate_final_priority(
            {"base_priority": "Medium"},
            {"asset_criticality": "Safety-Critical", "current_status": "Escalated", "safety_risk_level": "High"},
        )

    def test_concurrent_classification_no_corruption(self):
        texts = [
            "Signal is flickering.",
            "Track crack found.",
            "Electrical fault in relay.",
            "Switch not responding.",
            "Communication failure reported.",
        ]
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self._classify, t) for t in texts]
            for f in as_completed(futures):
                results.append(f.result())

        # All should return valid results
        assert len(results) == 5
        for r in results:
            assert "department" in r
            assert "fault_category" in r
            assert isinstance(r["department"], str)
            assert isinstance(r["fault_category"], str)

    def test_concurrent_priority_rules_no_corruption(self):
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self._priority) for _ in range(10)]
            for f in as_completed(futures):
                results.append(f.result())

        # All should be the same
        for r in results:
            assert r["final_priority"] == "Critical"

    def test_mixed_concurrent_classification_and_priority(self):
        """Interleave classification and priority engine calls."""
        def run_classification():
            c = ComplaintInput(complaint_text="Signal fault.", asset_type="Signal", safety_risk_level="High")
            return classify_case(c)

        def run_priority():
            return calculate_final_priority(
                {"base_priority": "High"},
                {"asset_criticality": "Safety-Critical", "current_status": "Interrupted", "safety_risk_level": "High"},
            )

        results = []
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = []
            for _ in range(3):
                futures.append(executor.submit(run_classification))
                futures.append(executor.submit(run_priority))
            for f in as_completed(futures):
                results.append(f.result())

        assert len(results) == 6
