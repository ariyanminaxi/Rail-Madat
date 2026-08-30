"""
task_scheduler.py — Scheduling and Resource Allocation Engine

Main entry point. Wires together conflict_detector, compatibility_checker,
scheduling_scorer, scheduling_explanations, and resource_allocator into
the full pipeline:

1. Load tasks + trains (+ teams)
2. Group tasks per section into bundles (Recommended / Conditional / Rejected)
3. For each bundle: compute duration, find free windows, rank them
4. Check team/resource availability (fallback chain) for tasks in the bundle
5. Build the final block_recommendation JSON per the updated schema

NOTE: this file expects tasks/trains in the wrapped input contract:
    {"maintenance_tasks": [...], "trains": [...], "safety_buffer_minutes": 15}
See load_payload_from_files() for building that from the sample data files.
"""

import json
import csv
from datetime import datetime, timedelta

from .conflict_detector import (
    parse_iso, to_iso, get_trains_for_section, find_free_windows, has_train_conflict,
)
from .compatibility_checker import classify_bundle, compute_block_duration_minutes, is_emergency
from .scheduling_scorer import rank_windows
from .scheduling_explanations import build_recommendation_reason, build_alternative_reason, build_rejection_reason
from .resource_allocator import allocate_team


# ---------- loading ----------

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def load_trains_csv(paths):
    """Reads one train CSV or a list of them and merges into one list.
    Accepts either a single path string or a list of path strings.
    Duplicate train_id entries (same train listed in more than one file)
    are kept only once, first occurrence wins."""
    if isinstance(paths, str):
        paths = [paths]

    trains = []
    seen_ids = set()
    for path in paths:
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                if row["train_id"] in seen_ids:
                    continue  # skip duplicate train_id across files
                seen_ids.add(row["train_id"])
                trains.append(row)  # start_time/end_time already ISO strings
    return trains


def load_payload_from_files(tasks_path, trains_csv_paths, safety_buffer_minutes=15):
    """trains_csv_paths can be a single path or a list of paths."""
    return {
        "maintenance_tasks": load_json(tasks_path),
        "trains": load_trains_csv(trains_csv_paths),
        "safety_buffer_minutes": safety_buffer_minutes,
    }


# ---------- grouping ----------

def get_waiting_tasks_for_section(tasks, section_id):
    return [
        t for t in tasks
        if t["section_id"] == section_id
        and t.get("block_required")
        and t.get("status") == "Waiting for block"
    ]


def build_groups_for_section(section_tasks):
    """Splits a section's waiting tasks into bundles per the 3-outcome model.
    Returns list of (tasks_in_group, grouping_status, conditions, reasons)."""
    groups = []
    remaining = list(section_tasks)

    # Emergencies are always scheduled individually, never auto-grouped.
    emergencies = [t for t in remaining if is_emergency(t)]
    for e in emergencies:
        remaining.remove(e)
        groups.append(([e], "Recommended Bundle", [],
                        ["Emergency task; never auto-grouped, scheduled individually."]))

    if remaining:
        status, conditions, reasons = classify_bundle(remaining)
        if status == "Rejected Bundle":
            # Fall back to scheduling each task in its own block.
            for t in remaining:
                groups.append(([t], "Recommended Bundle", [],
                                ["Split from a rejected bundle; scheduled individually."] + reasons))
        else:
            groups.append((remaining, status, conditions, reasons))

    return groups


# ---------- per-group block building ----------

def build_block_for_group(tasks, section_id, trains, day_start, day_end,
                           safety_buffer_minutes, grouping_status, conditions,
                           grouping_reasons, teams, active_assignments, block_counter):
    section_trains = get_trains_for_section(trains, section_id)
    duration = compute_block_duration_minutes(tasks)

    free_windows = find_free_windows(section_trains, day_start, day_end, safety_buffer_minutes)
    candidates = [
        (start, start + timedelta(minutes=duration))
        for start, end in free_windows
        if (end - start).total_seconds() / 60 >= duration
    ]

    has_critical = any(t.get("final_priority") == "Critical" for t in tasks)
    has_overdue = any(t.get("fault_category", "").lower().startswith("overdue") for t in tasks)

    if not candidates:
        return {
            "section_id": section_id,
            "combined_tasks": [t["task_id"] for t in tasks],
            "source_ids": [t.get("source_id") for t in tasks],
            "grouping_status": grouping_status,
            "conditions": conditions,
            "approval_status": "Rejected",
            "recommendation_reason": build_rejection_reason(
                grouping_reasons + ["No free window in this day is long enough for the combined duration."]
            ),
        }

    ranked = rank_windows(candidates, has_critical, has_overdue)
    best_start, best_end = ranked[0]

    alternatives = [
        {
            "start_time": to_iso(s),
            "end_time": to_iso(e),
            "reason": build_alternative_reason(s, e, i + 2),  # +2 since best is #1
        }
        for i, (s, e) in enumerate(ranked[1:4])
    ]

    # Resource / team availability check per task (fallback chain).
    resource_notes = []
    for t in tasks:
        outcome = allocate_team(t, teams, active_assignments)
        resource_notes.append({"task_id": t["task_id"], **outcome})

    return {
        "block_id": f"B-{block_counter:03d}",
        "section_id": section_id,
        "start_time": to_iso(best_start),
        "end_time": to_iso(best_end),
        "combined_tasks": [t["task_id"] for t in tasks],
        "source_ids": [t.get("source_id") for t in tasks],
        "grouping_status": grouping_status,
        "conditions": conditions,
        "affected_trains": [
            tr["train_id"] for tr in section_trains
            if has_train_conflict(best_start, best_end, [tr], safety_buffer_minutes)
        ],
        "safety_buffer_minutes": safety_buffer_minutes,
        "resource_allocation": resource_notes,
        "recommendation_reason": build_recommendation_reason(
            tasks, grouping_status, grouping_reasons, has_critical
        ),
        "rejected_alternatives": alternatives,
        "approval_status": "Pending",
    }


# ---------- top-level ----------

def schedule_tasks(payload: dict, schedule_date: str):
    """
    payload: {"maintenance_tasks": [...], "trains": [...], "safety_buffer_minutes": N}
    schedule_date: 'YYYY-MM-DD' - the day being scheduled (backend-provided,
                   never taken from a client clock)
    teams / active_assignments: optional, loaded separately for the resource
                   fallback chain (see data/teams.json).
    """
    tasks = payload["maintenance_tasks"]
    trains = payload["trains"]
    buffer_minutes = payload.get("safety_buffer_minutes", 15)

    try:
        teams = load_json("data/teams.json")
    except FileNotFoundError:
        teams = []
    active_assignments = {}  # TODO: populate from the backend in-progress tasks feed

    day_start = parse_iso(f"{schedule_date}T00:00:00+05:30")
    day_end = parse_iso(f"{schedule_date}T23:59:59+05:30")

    sections = sorted({t["section_id"] for t in tasks})
    results = []
    counter = 301
    for section_id in sections:
        section_tasks = get_waiting_tasks_for_section(tasks, section_id)
        if not section_tasks:
            continue
        for group_tasks, grouping_status, conditions, reasons in build_groups_for_section(section_tasks):
            block = build_block_for_group(
                group_tasks, section_id, trains, day_start, day_end,
                buffer_minutes, grouping_status, conditions, reasons,
                teams, active_assignments, counter,
            )
            results.append(block)
            counter += 1

    return results


# Keep backward compatibility alias
generate_all_recommendations = schedule_tasks


if __name__ == "__main__":
    # Single file:
    #   load_payload_from_files("data/tasks.json", "data/trains.csv", ...)
    # Multiple files (e.g. one per week or one per teammate):
    #   load_payload_from_files("data/tasks.json",
    #       ["data/trains_week1.csv", "data/trains_week2.csv"], ...)
    payload = load_payload_from_files("data/tasks.json", "data/trains.csv", safety_buffer_minutes=15)
    output = schedule_tasks(payload, schedule_date="2026-08-24")
    with open("data/blocks_output.json", "w") as f:
        json.dump(output, f, indent=2)
    print(json.dumps(output, indent=2))
