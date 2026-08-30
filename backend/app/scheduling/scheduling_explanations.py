"""
scheduling_explanations.py — Scheduling and Resource Allocation Engine

Implements differentiating feature #1 (explainable coordination) and
feature #3 (conflict-resilient alternatives with reasons) from the brief:
every recommendation and every rejected alternative gets a human-readable
reason, not just raw data.
"""


def build_recommendation_reason(tasks, grouping_status, grouping_reasons, has_critical):
    task_ids = ", ".join(t["task_id"] for t in tasks)
    parts = [f"Block covers task(s) {task_ids} ({grouping_status})."]
    parts.extend(grouping_reasons)
    if has_critical:
        parts.append("Contains a Critical-priority task, scheduled at the earliest safe slot.")
    parts.append("No train conflict exists in the chosen window after applying the safety buffer.")
    return " ".join(parts)


def build_alternative_reason(window_start, window_end, rank_position):
    return (
        f"Valid window from {window_start.strftime('%H:%M')} to "
        f"{window_end.strftime('%H:%M')}, but ranked #{rank_position} "
        f"(later / non-night-time / lower priority fit than the top pick)."
    )


def build_rejection_reason(reasons):
    return " ".join(reasons) if reasons else "No free window long enough was found for this date."
