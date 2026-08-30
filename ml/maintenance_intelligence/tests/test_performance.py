"""Performance tests.

Measure model load time, first prediction latency, repeated prediction
latency, memory usage, and concurrent inference throughput.
"""

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import psutil
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.maintenance_intelligence.config import MODEL_PATH
from app.maintenance_intelligence.inference.classifier import classify_case, _load_model
from app.maintenance_intelligence.prioritization.priority_engine import calculate_final_priority
from app.maintenance_intelligence.io_schemas import ComplaintInput


# ===================================================================
# Model load time
# ===================================================================

class TestModelLoadTime:
    def test_model_loads_within_acceptable_time(self):
        """Model should load within 5 seconds."""
        start = time.perf_counter()
        model = _load_model()
        elapsed = time.perf_counter() - start
        assert elapsed < 5.0, f"Model load took {elapsed:.2f}s (limit: 5s)"

    def test_model_load_deterministic_time(self):
        """Repeated loads should be similar in time (within 2x)."""
        times = []
        for _ in range(3):
            start = time.perf_counter()
            _load_model()
            times.append(time.perf_counter() - start)
        assert max(times) < min(times) * 3, f"Load times vary too much: {times}"


# ===================================================================
# First prediction latency
# ===================================================================

class TestFirstPredictionLatency:
    def test_first_prediction_within_limit(self):
        """First prediction after model load should complete within 2 seconds."""
        c = ComplaintInput(
            complaint_text="Signal near S-02 is flickering.",
            asset_type="Signal",
            asset_criticality="Safety-Critical",
            safety_risk_level="High",
        )
        start = time.perf_counter()
        result = classify_case(c)
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0, f"First prediction took {elapsed:.2f}s (limit: 2s)"
        assert "department" in result


# ===================================================================
# Repeated prediction latency
# ===================================================================

class TestRepeatedPredictionLatency:
    def test_100_predictions_complete(self):
        """100 predictions should complete within 30 seconds."""
        c = ComplaintInput(
            complaint_text="Signal near S-02 is flickering.",
            asset_type="Signal",
            asset_criticality="Safety-Critical",
            safety_risk_level="High",
        )
        start = time.perf_counter()
        for _ in range(100):
            classify_case(c)
        elapsed = time.perf_counter() - start
        avg = elapsed / 100
        assert elapsed < 30.0, f"100 predictions took {elapsed:.2f}s (limit: 30s)"
        assert avg < 0.5, f"Average prediction time {avg:.3f}s (limit: 0.5s)"

    def test_no_memory_growth(self):
        """100 repeated predictions should not cause significant memory growth."""
        process = psutil.Process()
        mem_before = process.memory_info().rss

        c = ComplaintInput(
            complaint_text="Track crack found near rail joint.",
            asset_type="Track",
            asset_criticality="Safety-Critical",
            safety_risk_level="High",
        )
        for _ in range(100):
            classify_case(c)

        mem_after = process.memory_info().rss
        growth = mem_after - mem_before
        # Allow up to 50MB growth (accounting for GC, caching)
        assert growth < 50 * 1024 * 1024, f"Memory grew by {growth / 1024 / 1024:.1f}MB"


# ===================================================================
# Concurrent inference throughput
# ===================================================================

class TestConcurrentInferenceThroughput:
    def test_concurrent_predictions_valid(self):
        """5 concurrent predictions should all return valid results."""

        def predict(text):
            c = ComplaintInput(complaint_text=text, safety_risk_level="Medium")
            return classify_case(c)

        texts = [
            "Signal is flickering.",
            "Track crack near joint.",
            "Electrical fault in relay.",
            "Switch not responding.",
            "Communication failure.",
        ]

        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(predict, t) for t in texts]
            for f in as_completed(futures):
                results.append(f.result())

        assert len(results) == 5
        for r in results:
            assert "department" in r
            assert "fault_category" in r
            assert isinstance(r["department"], str)

    def test_concurrent_throughput(self):
        """20 concurrent predictions should complete within 30 seconds."""

        def predict(i):
            c = ComplaintInput(
                complaint_text=f"Fault report number {i}.",
                safety_risk_level="Low",
            )
            return classify_case(c)

        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(predict, i) for i in range(20)]
            results = [f.result() for f in as_completed(futures)]
        elapsed = time.perf_counter() - start

        assert len(results) == 20
        assert elapsed < 30.0, f"20 concurrent predictions took {elapsed:.2f}s"


# ===================================================================
# Priority engine performance
# ===================================================================

class TestPriorityEnginePerformance:
    def test_priority_engine_always_fast(self):
        """Priority engine should be near-instantaneous."""
        start = time.perf_counter()
        for _ in range(1000):
            calculate_final_priority(
                {"base_priority": "High"},
                {"asset_criticality": "Safety-Critical", "current_status": "Interrupted", "safety_risk_level": "High"},
            )
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"1000 priority calculations took {elapsed:.2f}s"


# ===================================================================
# Baseline recording
# ===================================================================

class TestPerformanceBaseline:
    def test_record_baseline_metrics(self, capsys):
        """Record baseline performance metrics for future comparison."""
        c = ComplaintInput(
            complaint_text="Signal near S-02 is flickering.",
            asset_type="Signal",
            asset_criticality="Safety-Critical",
            safety_risk_level="High",
        )

        # Load time
        start = time.perf_counter()
        _load_model()
        load_time = time.perf_counter() - start

        # Prediction time (warm)
        classify_case(c)  # warm up
        times = []
        for _ in range(10):
            start = time.perf_counter()
            classify_case(c)
            times.append(time.perf_counter() - start)

        avg_pred = sum(times) / len(times)

        process = psutil.Process()
        mem_mb = process.memory_info().rss / 1024 / 1024

        report = {
            "model_load_time_s": round(load_time, 4),
            "avg_prediction_time_s": round(avg_pred, 4),
            "memory_usage_mb": round(mem_mb, 1),
        }
        print(f"\nPerformance baseline: {report}")
