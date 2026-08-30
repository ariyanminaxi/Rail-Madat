"""
resource_allocator.py — Scheduling and Resource Allocation Engine

Fallback chain when a task's required_team is busy or unavailable:
  1. Primary team (same department, same section) — if free
  2. Reserve team (same department) — if free
  3. Cross-section qualified team — if free
  4. Preemptible active team — if safe and manager-approved
  5. Human verification required — no suitable team found

Hard rules:
  - Never auto-interrupt non-preemptible work.
  - Preemption requires safety validation AND manager approval.
  - Emergency isolation, safety protection, and unsafe worksite
    work are NEVER preemptible.
"""

from .preemption_manager import get_preemption_status


def allocate_team(task, teams, active_assignments):
    """
    Fallback chain:
      1. Primary team (same department, same section) — if free
      2. Reserve team (same department) — if free
      3. Cross-section qualified team — if free
      4. Preemptible active team — if safe AND manager approval required
      5. Human verification required

    task: the maintenance task needing a team
    teams: list of team dicts
    active_assignments: dict team_id -> currently active task dict (or None)

    Returns a dict describing the outcome.
    """
    required = task.get("required_team")
    section_id = task.get("section_id")
    department = task.get("department")
    task_priority = task.get("final_priority", task.get("base_priority", "Medium"))

    # 1. Primary team (same department, same section), if free
    for team in teams:
        if team["team_id"] == required and team.get("resource_status") in ("Available", "available", None):
            return {
                "team_assigned": required,
                "resource_status": "Assigned (primary team)",
                "preemption_status": None,
                "requires_approval": False,
                "escalated": False,
                "reason": "Primary required team was available.",
            }

    # 2. Reserve team (same department)
    for team in teams:
        is_reserve = team.get("is_reserve_team", team.get("is_reserve", False))
        team_status = team.get("resource_status", team.get("status", ""))
        if (team.get("department") == department
                and is_reserve
                and team_status in ("Available", "available")):
            return {
                "team_assigned": team["team_id"],
                "resource_status": "Assigned (reserve team)",
                "preemption_status": None,
                "requires_approval": False,
                "escalated": False,
                "reason": f"Primary team {required} busy; reserve team {team['team_id']} used.",
            }

    # 3. Cross-section qualified team
    for team in teams:
        quals = team.get("qualification", [])
        if isinstance(quals, str):
            quals = [q.strip() for q in quals.split(";")]
        team_status = team.get("resource_status", team.get("status", ""))
        if team_status in ("Available", "available") and department in quals:
            return {
                "team_assigned": team["team_id"],
                "resource_status": "Assigned (cross-section team)",
                "preemption_status": None,
                "requires_approval": False,
                "escalated": False,
                "reason": f"No local team free; cross-section qualified team {team['team_id']} used.",
            }

    # 4. Preemptible active team (requires safety validation + manager approval)
    for team in teams:
        team_id = team["team_id"]
        active_task = active_assignments.get(team_id)
        if active_task is None:
            continue

        status = get_preemption_status(active_task)
        if status == "Preemptible":
            return {
                "team_assigned": team_id,
                "resource_status": "Assigned (preempted lower-priority work)",
                "preemption_status": status,
                "requires_approval": True,  # Manager approval required
                "escalated": False,
                "reason": (
                    f"Team {team_id}'s current task {active_task.get('task_id')} "
                    "is preemptible and lower priority; requires manager approval "
                    "before reassignment is final."
                ),
            }

    # 5. No suitable team found — human verification required
    return {
        "team_assigned": None,
        "resource_status": "Unresolved - human verification required",
        "preemption_status": None,
        "requires_approval": True,
        "escalated": True,
        "reason": (
            f"No available or safely reassignable team found for {required}. "
            "Human verification and manager approval required."
        ),
    }
