"""
preventive_maintenance_cycle.py — Maintenance Workflows

Two responsibilities:

1. generate_due_maintenance_tasks()
   The central maintenance job described in 09_Session_&_Frontend_Behavior.md:
   ONE job, not one per logged-in user, called on admin-dashboard open /
   backend start / an admin button / once-a-day cron. Turns overdue-or-due
   `maintenance_schedules` rows into `maintenance_task` objects using the
   canonical "Preventive (from schedule)" schema from
   03_Keywords_&_Data_Dictionary.md. Idempotent: a schedule that already has
   an open task is skipped, so the same preventive task is never generated
   twice.

2. process_completion_report()
   The receiver-completion queue decision from
   12_Work_Completion_&_Receiver_Reports.md. Given a work_completion_report,
   returns exactly what the backend API should write to the task and the asset —
   never silently closes, cancels, or downgrades a task
   (see 07_Safety_&_Ground_Rules.md).

Both functions are pure: inputs in, a plan dict out. No DB/network I/O —
the backend API is the one that actually performs the writes.
"""
from datetime import date
from .maintenance_due_dates import is_overdue, overdue_days, recalculate_after_completion

DEPARTMENT_TEAM_PREFIX = {
    "Track": "TEAM-TRK",
    "Signalling": "TEAM-SIG",
    "Electrical": "TEAM-ELE",
}

PRIORITY_LADDER = ["Low", "Medium", "High", "Critical"]


# ---------------------------------------------------------------------------
# 1. Recurring preventive-task generation
# ---------------------------------------------------------------------------
def generate_due_maintenance_tasks(schedules, existing_open_task_schedule_ids, current_time=None):
    """
    schedules: list[dict] from maintenance_schedules.csv, each with at least
        schedule_id, asset_id, section_id, department, next_due_date,
        interval_days, assigned_team_id, status
    existing_open_task_schedule_ids: set[str] of schedule_ids that already
        have a non-terminal task open — prevents duplicate generation.
    current_time: date to evaluate against (default: today)

    Returns: list[dict] of new maintenance_task objects, one per due/overdue
    schedule that doesn't already have an open task.
    """
    as_of = current_time or date.today()
    new_tasks = []

    for sched in schedules:
        if sched["schedule_id"] in existing_open_task_schedule_ids:
            continue  # uniqueness rule — never double-generate

        due = is_overdue(sched["next_due_date"], as_of) or sched.get("status") == "Overdue"
        if not due:
            continue

        new_tasks.append({
            "task_id": None,  # assigned by the backend DB on insert
            "source_type": "scheduled",
            "source_id": sched["schedule_id"],
            "asset_id": sched["asset_id"],
            "section_id": sched["section_id"],
            "department": sched["department"],
            "maintenance_type": "Preventive",
            "base_priority": "High" if is_overdue(sched["next_due_date"], as_of) else "Medium",
            "duration_minutes": 60,
            "required_team": sched.get("assigned_team_id")
                or f"{DEPARTMENT_TEAM_PREFIX.get(sched['department'], 'TEAM')}-01",
            "required_equipment": [],
            "due_date": sched["next_due_date"],
            "block_required": True,
            "status": "Reported",
            "overdue_days": overdue_days(sched["next_due_date"], as_of),
        })
    return new_tasks


# ---------------------------------------------------------------------------
# 2. Receiver-completion queue decision
# ---------------------------------------------------------------------------
def process_completion_report(report: dict, task: dict, asset_interval_days: int) -> dict:
    """
    report: a work_completion_report dict (task_id, work_status,
        completion_percentage, remaining_work_minutes, failure_reason, ...)
    task: the current maintenance_task dict — needs at least final_priority;
        deferral_count / escalation_level default to 0 if absent.
    asset_interval_days: the asset's maintenance_interval_days, needed to
        recompute next_due_date on a Completed report.

    Returns a dict of exactly what the backend API should write — mirrors the
    queue-decision logic in 12_Work_Completion_&_Receiver_Reports.md.
    """
    work_status = report["work_status"]
    deferral_count = task.get("deferral_count", 0)
    escalation_level = task.get("escalation_level", 0)
    final_priority = task.get("final_priority", "Medium")

    if work_status == "Completed":
        due_fields = recalculate_after_completion(report["received_at"][:10], asset_interval_days)
        return {
            "task_status": "Completed",
            "final_priority": final_priority,   # never changed on completion
            "queue_again": False,
            "maintenance_record_created": True,
            "audit_log_required": True,
            "notification_required": True,
            **due_fields,
        }

    if work_status in ("Not Completed", "Partially Completed", "Interrupted", "Awaiting Materials"):
        bumps_deferral = work_status in ("Not Completed", "Interrupted")
        new_deferral_count = deferral_count + 1 if bumps_deferral else deferral_count
        new_escalation_level = escalation_level + (1 if bumps_deferral else 0)
        escalated_priority = _escalate_priority(final_priority, new_escalation_level)
        status_map = {
            "Not Completed": "Deferred",
            "Partially Completed": "Partially Completed",
            "Interrupted": "Interrupted",
            "Awaiting Materials": "Awaiting Materials",
        }
        return {
            "task_status": status_map[work_status],
            "final_priority": escalated_priority,
            "escalation_level": new_escalation_level,
            "deferral_count": new_deferral_count,
            "queue_again": True,
            "maintenance_record_created": True,
            "audit_log_required": True,
            "notification_required": True,
            "human_review_required": work_status in ("Partially Completed", "Interrupted"),
        }

    if work_status == "Cancelled":
        return {
            "task_status": "Cancelled",
            "final_priority": final_priority,
            "queue_again": False,
            "requires_manager_approval": True,   # never closes without this
            "cancelled_reason": report.get("failure_reason", ""),
            "audit_log_required": True,
            "notification_required": True,
        }

    if work_status == "Emergency":
        return {
            "task_status": "Emergency",
            "final_priority": "Critical",          # emergency is always Critical
            "queue_again": False,
            "automatic_block_approval": False,      # never auto-authorized
            "human_review_required": True,
            "audit_log_required": True,
            "notification_required": True,
            "notify_control_role": True,
        }

    raise ValueError(f"Unrecognized work_status: {work_status!r}")


def _escalate_priority(current_priority: str, escalation_level: int) -> str:
    """
    Priority never auto-downgrades. Critical always stays Critical.
    Each escalation_level step moves one rung up Low->Medium->High->Critical,
    per the escalation example in 02_MVP_Scope.md.
    """
    if current_priority == "Critical":
        return "Critical"
    idx = PRIORITY_LADDER.index(current_priority)
    new_idx = min(idx + escalation_level, len(PRIORITY_LADDER) - 1)
    return PRIORITY_LADDER[new_idx]
