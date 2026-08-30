"""
preemption_manager.py — Scheduling and Resource Allocation Engine

Determines whether a team's currently active work can be safely paused to
free them up for a higher-priority task. Hard rule from the brief: never
auto-interrupt non-preemptible work (active isolation, unsafe-if-halted
work, emergency protection).

TODO: the exact list of non-preemptible fault_category / work-type values
should come from note "13 Final Status Model & Resource Fallback" once you
have it. NON_PREEMPTIBLE_CATEGORIES below is a placeholder covering the
three examples explicitly named in the brief.
"""

# TODO: replace with the authoritative list from note 13.
NON_PREEMPTIBLE_CATEGORIES = {
    "Electrical Isolation Check",
    "Unsafe-if-Halted Work",
    "Emergency Protection",
}


def get_preemption_status(active_task: dict) -> str:
    """Returns 'Preemptible' or 'Non-Preemptible' for a task currently in
    progress that a team might be pulled off of."""
    if active_task.get("is_emergency"):
        return "Non-Preemptible"
    if active_task.get("fault_category") in NON_PREEMPTIBLE_CATEGORIES:
        return "Non-Preemptible"
    return "Preemptible"


def can_preempt(active_task: dict) -> bool:
    """Check whether preemption is permitted for the given active task."""
    return get_preemption_status(active_task) == "Preemptible"


def record_preemption_reason(active_task: dict, reason: str) -> dict:
    """Build a preemption record with the displaced task and reason."""
    return {
        "displaced_task_id": active_task.get("task_id"),
        "preemption_status": get_preemption_status(active_task),
        "reason": reason,
        "requires_human_approval": not can_preempt(active_task),
    }
