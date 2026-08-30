"""
compatibility_checker.py — Scheduling and Resource Allocation Engine

Implements task grouping per the "grouping is NOT same-section=combine" rule.
Every candidate group of tasks resolves to exactly one outcome:
  - "Recommended Bundle"  : fully compatible, no conditions needed
  - "Conditional Bundle"  : compatible only if specific conditions hold
  - "Rejected Bundle"     : cannot be combined, must be scheduled separately

TODO (blocking): the real fault_category compatibility matrix and the full
list of non-groupable combinations live in note "12 Task Grouping &
Compatibility", which has not been shared yet. The matrix below is a
reasonable placeholder covering the one example given in the brief
(electrical isolation vs energized-equipment testing). Replace
FAULT_CATEGORY_CONFLICTS with the real matrix as soon as you have it --
everything else in this module is written to just work once you do.
"""

# TODO: replace with the real matrix from note 12.
# Key: frozenset of two fault_category values that can NEVER be bundled together.
FAULT_CATEGORY_CONFLICTS = {
    frozenset({"Electrical Isolation Check", "Energized Equipment Testing"}),
}


def is_emergency(task) -> bool:
    if task.get("is_emergency"):
        return True
    fault = (task.get("fault_category") or "").lower()
    return fault.startswith("emergency")


def classify_bundle(tasks):
    """Decide the grouping outcome for a candidate set of tasks in one section.

    Returns: (grouping_status, conditions: list[str], reasons: list[str])
    """
    if len(tasks) <= 1:
        return "Recommended Bundle", [], ["Single task, no grouping conflicts possible."]

    # Rule: emergencies never auto-group with anything else.
    emergencies = [t for t in tasks if is_emergency(t)]
    if emergencies:
        ids = ", ".join(t["task_id"] for t in emergencies)
        return (
            "Rejected Bundle",
            [],
            [f"Emergency task(s) {ids} must never be auto-grouped; scheduled individually."],
        )

    # Rule: hard fault-category conflicts (see TODO above).
    categories = {t.get("fault_category") for t in tasks if t.get("fault_category")}
    for pair in FAULT_CATEGORY_CONFLICTS:
        if pair.issubset(categories):
            a, b = tuple(pair)
            return (
                "Rejected Bundle",
                [],
                [f"'{a}' and '{b}' can never be performed in the same block."],
            )

    # Rule: different departments sharing a block need supervisor sign-off
    # (placeholder condition until note 12 specifies the real conditions list).
    departments = {t.get("department") for t in tasks}
    if len(departments) > 1:
        return (
            "Conditional Bundle",
            ["Requires cross-department supervisor sign-off before approval."],
            [f"Tasks span departments: {', '.join(sorted(departments))}."],
        )

    return (
        "Recommended Bundle",
        [],
        ["All tasks share department, no fault-category conflicts, no emergencies."],
    )


def compute_block_duration_minutes(tasks, setup_minutes=10):
    """Compute required block duration using each task's execution_mode.

    - Tasks marked "Sequential" (or teams that necessarily work one after
      another) have their durations summed.
    - Tasks marked "Parallel" can run alongside other parallel tasks; the
      parallel group's duration is its longest task + a setup allowance.
    - "Either" tasks are treated as parallel when grouped with other
      parallel-compatible tasks (best case), else sequential.

    Returns total minutes needed for the block.
    """
    sequential_tasks = [t for t in tasks if t.get("execution_mode") == "Sequential"]
    parallel_tasks = [t for t in tasks if t.get("execution_mode") in ("Parallel", "Either")]

    sequential_total = sum(t["duration_minutes"] for t in sequential_tasks)
    parallel_total = (
        max((t["duration_minutes"] for t in parallel_tasks), default=0) + setup_minutes
        if parallel_tasks else 0
    )

    # Same-team tasks always run sequentially regardless of execution_mode,
    # since one team can't do two things at once.
    team_totals = {}
    for t in tasks:
        team_totals[t["required_team"]] = team_totals.get(t["required_team"], 0) + t["duration_minutes"]
    same_team_floor = max(team_totals.values()) if team_totals else 0

    return max(sequential_total + parallel_total, same_team_floor)
