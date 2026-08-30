import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from datetime import datetime
from app.scheduling.conflict_detector import parse_iso, find_free_windows, has_train_conflict
from app.scheduling.compatibility_checker import classify_bundle, compute_block_duration_minutes, is_emergency
from app.scheduling.scheduling_scorer import rank_windows


def test_free_windows_finds_night_gap():
    trains = [
        {"start_time": "2026-08-24T05:00:00+05:30", "end_time": "2026-08-24T05:20:00+05:30"},
    ]
    day_start = parse_iso("2026-08-24T00:00:00+05:30")
    day_end = parse_iso("2026-08-24T23:59:59+05:30")
    windows = find_free_windows(trains, day_start, day_end, buffer_minutes=15)
    assert windows[0][0] == day_start


def test_conflict_detection_true_when_overlap():
    trains = [{"start_time": "2026-08-24T10:00:00+05:30", "end_time": "2026-08-24T10:30:00+05:30"}]
    start = parse_iso("2026-08-24T09:50:00+05:30")
    end = parse_iso("2026-08-24T10:10:00+05:30")
    assert has_train_conflict(start, end, trains, buffer_minutes=15) is True


def test_conflict_detection_false_when_clear():
    trains = [{"start_time": "2026-08-24T10:00:00+05:30", "end_time": "2026-08-24T10:30:00+05:30"}]
    start = parse_iso("2026-08-24T00:00:00+05:30")
    end = parse_iso("2026-08-24T01:00:00+05:30")
    assert has_train_conflict(start, end, trains, buffer_minutes=15) is False


def test_emergency_never_auto_grouped():
    tasks = [
        {"task_id": "T-1", "is_emergency": True, "department": "Signalling", "fault_category": "Emergency Signal Failure"},
        {"task_id": "T-2", "is_emergency": False, "department": "Signalling", "fault_category": "Preventive Inspection"},
    ]
    status, conditions, reasons = classify_bundle(tasks)
    assert status == "Rejected Bundle"
    assert is_emergency(tasks[0]) is True


def test_conflicting_fault_categories_rejected():
    tasks = [
        {"task_id": "T-1", "department": "Electrical", "fault_category": "Electrical Isolation Check"},
        {"task_id": "T-2", "department": "Electrical", "fault_category": "Energized Equipment Testing"},
    ]
    status, conditions, reasons = classify_bundle(tasks)
    assert status == "Rejected Bundle"


def test_block_duration_mixes_sequential_and_parallel():
    tasks = [
        {"required_team": "TEAM-A", "duration_minutes": 60, "execution_mode": "Sequential"},
        {"required_team": "TEAM-B", "duration_minutes": 90, "execution_mode": "Parallel"},
    ]
    duration = compute_block_duration_minutes(tasks, setup_minutes=10)
    # sequential (60) + parallel (90 + 10 setup) = 160
    assert duration == 160


def test_rank_windows_prefers_night_and_critical():
    windows = [
        (parse_iso("2026-08-24T09:00:00+05:30"), parse_iso("2026-08-24T10:00:00+05:30")),
        (parse_iso("2026-08-24T02:00:00+05:30"), parse_iso("2026-08-24T03:00:00+05:30")),
    ]
    ranked = rank_windows(windows, has_critical=True, has_overdue=False)
    assert ranked[0][0].hour == 2  # night window wins
