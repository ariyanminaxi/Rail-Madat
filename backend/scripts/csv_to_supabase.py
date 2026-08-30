"""
RailMadat CSV -> Supabase Import Script (v2)
Handles enum mapping, empty values, and new tables.
"""

import os
import csv
from dotenv import load_dotenv

load_dotenv()

from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SERVICE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
admin = create_client(SUPABASE_URL, SERVICE_KEY)

CSV_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "csv_data")

# Status mapping: CSV value -> DB enum value (spaces to underscores)
STATUS_MAP = {
    "Reported": "Reported",
    "Under Review": "Under_Review",
    "Assigned": "Assigned",
    "Waiting for Block": "Waiting_for_Block",
    "Scheduled": "Scheduled",
    "In Progress": "In_Progress",
    "Completed": "Completed",
    "Deferred": "Deferred",
    "Emergency": "Emergency",
    "Rejected": "Rejected",
    "Cancelled": "Cancelled",
    "Partially Completed": "Partially_Completed",
    "Interrupted": "Interrupted",
}

# Criticality mapping
CRITICALITY_MAP = {
    "Critical": "Safety-Critical",
    "Safety-Critical": "Safety-Critical",
    "High": "High",
    "Medium": "Medium",
    "Low": "Low",
}


def clean(val):
    if val is None or val == "":
        return None
    val = str(val).strip()
    if val.lower() == "true":
        return True
    if val.lower() == "false":
        return False
    return val


def map_status(val):
    """Map CSV status to valid DB enum value."""
    if not val:
        return None
    return STATUS_MAP.get(val, val.replace(" ", "_"))


def map_criticality(val):
    if not val:
        return "Medium"
    return CRITICALITY_MAP.get(val, val)


def read_csv(filename):
    path = os.path.join(CSV_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def safe_insert(table, rows, batch=50):
    ok = 0
    err = 0
    for i in range(0, len(rows), batch):
        chunk = rows[i : i + batch]
        try:
            admin.table(table).insert(chunk).execute()
            ok += len(chunk)
        except Exception:
            for row in chunk:
                try:
                    admin.table(table).insert(row).execute()
                    ok += 1
                except Exception as e:
                    err += 1
                    if err <= 5:
                        print(f"    ERR: {str(e)[:120]}")
    return ok, err


def clear_table(table, filter_col=None, filter_vals=None):
    """Clear existing data from a table."""
    try:
        if filter_col and filter_vals:
            for v in filter_vals:
                admin.table(table).delete().eq(filter_col, v).execute()
        else:
            r = admin.table(table).select("id").execute()
            for row in r.data:
                admin.table(table).delete().eq("id", row["id"]).execute()
            return len(r.data)
    except:
        pass
    return 0


# =============================================================
# 1. ASSET_MASTER -> ASSET_REGISTRY
# =============================================================
def import_assets():
    print("\n=== asset_master.csv -> asset_registry ===")
    rows = read_csv("asset_master.csv")
    print(f"  Read {len(rows)} rows")

    # Check existing assets for upsert
    existing = admin.table("asset_registry").select("asset_id").execute()
    existing_ids = {e["asset_id"] for e in existing.data}
    print(f"  Found {len(existing_ids)} existing assets")

    converted = []
    for r in rows:
        converted.append(
            {
                "asset_id": r["asset_id"],
                "asset_type": r["asset_type"],
                "asset_subtype": r.get("asset_subtype") or None,
                "state": r["state"],
                "city": r["city"],
                "section_id": r["section_id"],
                "department": r["department"],
                "asset_criticality": map_criticality(r.get("asset_criticality")),
                "operational_status": r.get("current_status", "Operational"),
                "last_maintenance_date": r.get("last_maintenance_date") or None,
                "next_due_date": r.get("next_due_date") or None,
                "is_overdue": r.get("is_overdue", "False") == "True",
            }
        )

    # Upsert: insert new, update existing
    new_rows = [r for r in converted if r["asset_id"] not in existing_ids]
    update_rows = [r for r in converted if r["asset_id"] in existing_ids]
    
    if new_rows:
        ok, err = safe_insert("asset_registry", new_rows)
        print(f"  Inserted {ok} new assets, {err} errors")
    if update_rows:
        for r in update_rows:
            try:
                admin.table("asset_registry").update(r).eq("asset_id", r["asset_id"]).execute()
            except Exception as e:
                print(f"    Update ERR: {str(e)[:100]}")
        print(f"  Updated {len(update_rows)} existing assets")


# =============================================================
# 2. TEAMS -> MAINTENANCE_TEAMS
# =============================================================
def import_teams():
    print("\n=== teams.csv -> maintenance_teams ===")
    rows = read_csv("teams.csv")
    print(f"  Read {len(rows)} rows")

    existing = admin.table("maintenance_teams").select("team_id").execute()
    existing_ids = {e["team_id"] for e in existing.data}
    print(f"  Found {len(existing_ids)} existing teams")

    converted = []
    for r in rows:
        converted.append(
            {
                "team_id": r["team_id"],
                "team_name": r["team_id"].replace("TEAM-", "Team ").replace("-", " ").title(),
                "department": r["department"],
                "section_id": r["home_section_id"],
                "team_lead_user_id": None,
                "member_count": 4,
                "status": r.get("resource_status", "Available"),
                "current_task_id": r.get("current_task_id") or None,
            }
        )

    new_rows = [r for r in converted if r["team_id"] not in existing_ids]
    update_rows = [r for r in converted if r["team_id"] in existing_ids]
    
    if new_rows:
        ok, err = safe_insert("maintenance_teams", new_rows)
        print(f"  Inserted {ok} new teams, {err} errors")
    if update_rows:
        for r in update_rows:
            try:
                admin.table("maintenance_teams").update(r).eq("team_id", r["team_id"]).execute()
            except Exception as e:
                print(f"    Update ERR: {str(e)[:100]}")
        print(f"  Updated {len(update_rows)} existing teams")


# =============================================================
# 3. STATUS_HISTORY -> WORKFLOW_STATUS_HISTORY
# =============================================================
def import_status_history():
    print("\n=== maintenance_status_history.csv -> workflow_status_history ===")
    rows = read_csv("maintenance_status_history.csv")
    print(f"  Read {len(rows)} rows")

    # Clear old
    clear_table("workflow_status_history")
    print("  Cleared old records")

    converted = []
    for r in rows:
        converted.append(
            {
                "task_id": r.get("task_id"),
                "complaint_id": r.get("case_id") or r.get("complaint_id"),
                "previous_status": map_status(r.get("previous_status")),
                "new_status": map_status(r["new_status"]),
                "changed_by_user_id": None,
                "reason": r.get("event_reason") or None,
                "changed_at": r.get("created_at"),
            }
        )

    ok, err = safe_insert("workflow_status_history", converted)
    print(f"  Result: {ok} inserted, {err} errors")


# =============================================================
# 4. WORK_COMPLETION_REPORTS -> WORK_COMPLETION_REPORTS table
# =============================================================
def import_completion_reports():
    print("\n=== work_completion_reports.csv -> work_completion_reports ===")
    rows = read_csv("work_completion_reports.csv")
    print(f"  Read {len(rows)} rows")

    converted = []
    for r in rows:
        converted.append(
            {
                "completion_report_id": r["completion_report_id"],
                "task_id": r["task_id"],
                "receiver_department": r.get("receiver_department"),
                "received_by": r.get("received_by"),
                "received_at": r.get("received_at") or None,
                "work_status": r.get("work_status", "Completed"),
                "completion_percentage": int(r.get("completion_percentage", 0) or 0),
                "inspection_result": r.get("inspection_result") or None,
                "failure_reason": r.get("failure_reason") or None,
                "remaining_work_minutes": int(r.get("remaining_work_minutes", 0) or 0),
                "material_status": r.get("material_status") or None,
                "safety_status": r.get("safety_status") or None,
                "next_action": r.get("next_action") or None,
                "remarks": r.get("remarks") or None,
            }
        )

    ok, err = safe_insert("work_completion_reports", converted)
    print(f"  Result: {ok} inserted, {err} errors")


# =============================================================
# 5. MAINTENANCE_HISTORY -> MAINTENANCE_HISTORY table
# =============================================================
def import_maintenance_history():
    print("\n=== maintenance_history.csv -> maintenance_history ===")
    rows = read_csv("maintenance_history.csv")
    print(f"  Read {len(rows)} rows")

    converted = []
    for r in rows:
        # Handle empty timestamps
        started = r.get("started_at") or None
        completed = r.get("completed_at") or None
        if started == "":
            started = None
        if completed == "":
            completed = None

        converted.append(
            {
                "record_id": r["record_id"],
                "asset_id": r["asset_id"],
                "task_id": r.get("task_id") or None,
                "scheduled_date": r.get("scheduled_date") or None,
                "maintenance_date": r.get("maintenance_date") or None,
                "started_at": started,
                "completed_at": completed,
                "maintenance_type": r.get("maintenance_type") or None,
                "fault_category": r.get("fault_category") or None,
                "root_cause": r.get("root_cause") or None,
                "performed_by": r.get("performed_by") or None,
                "inspection_result": r.get("inspection_result") or None,
                "defects_found": r.get("defects_found", "False") == "True",
                "corrective_action": r.get("corrective_action") or None,
                "materials_used": r.get("materials_used") or None,
                "work_performed": r.get("work_performed") or None,
                "resolution_type": r.get("resolution_type") or None,
                "downtime_minutes": int(r.get("downtime_minutes", 0) or 0),
                "completion_status": r.get("completion_status") or None,
                "next_due_date": r.get("next_due_date") or None,
                "remarks": r.get("remarks") or None,
            }
        )

    ok, err = safe_insert("maintenance_history", converted)
    print(f"  Result: {ok} inserted, {err} errors")


# =============================================================
# 6. MAINTENANCE_SCHEDULES -> MAINTENANCE_SCHEDULES table
# =============================================================
def import_schedules():
    print("\n=== maintenance_schedules.csv -> maintenance_schedules ===")
    rows = read_csv("maintenance_schedules.csv")
    print(f"  Read {len(rows)} rows")

    converted = []
    for r in rows:
        converted.append(
            {
                "schedule_id": r["schedule_id"],
                "asset_id": r["asset_id"],
                "section_id": r["section_id"],
                "department": r["department"],
                "maintenance_type": r["maintenance_type"],
                "activity": r["activity"],
                "interval_days": int(r.get("interval_days", 90) or 90),
                "last_maintenance_date": r.get("last_maintenance_date") or None,
                "next_due_date": r.get("next_due_date") or None,
                "is_overdue": r.get("is_overdue", "False") == "True",
                "status": r.get("status", "Upcoming"),
                "assigned_team_id": r.get("assigned_team_id") or None,
            }
        )

    ok, err = safe_insert("maintenance_schedules", converted)
    print(f"  Result: {ok} inserted, {err} errors")


# =============================================================
# 7. EQUIPMENT -> EQUIPMENT table
# =============================================================
def import_equipment():
    print("\n=== equipment.csv -> equipment ===")
    rows = read_csv("equipment.csv")
    print(f"  Read {len(rows)} rows")

    converted = []
    for r in rows:
        converted.append(
            {
                "equipment_id": r["equipment_id"],
                "equipment_type": r["equipment_type"],
                "department": r["department"],
                "home_section_id": r["home_section_id"],
                "status": r.get("status", "Available"),
                "assigned_team_id": r.get("assigned_team_id") or None,
                "last_calibration_date": r.get("last_calibration_date") or None,
                "calibration_due_date": r.get("calibration_due_date") or None,
            }
        )

    ok, err = safe_insert("equipment", converted)
    print(f"  Result: {ok} inserted, {err} errors")


# =============================================================
# VERIFICATION
# =============================================================
def verify():
    print("\n" + "=" * 60)
    print("FINAL VERIFICATION")
    print("=" * 60)
    tables = [
        "asset_registry",
        "maintenance_teams",
        "workflow_status_history",
        "maintenance_tasks",
        "work_completion_reports",
        "maintenance_history",
        "maintenance_schedules",
        "equipment",
        "complaints",
        "ai_classifications",
        "dashboard_alerts",
        "audit_events",
    ]
    for t in tables:
        try:
            r = admin.table(t).select("*", count="exact").execute()
            print(f"  {t}: {r.count} rows")
        except Exception as e:
            print(f"  {t}: ERROR - {str(e)[:60]}")


# =============================================================
# MAIN
# =============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("RailMadat CSV Import to Supabase (v2)")
    print("=" * 60)

    import_assets()
    import_teams()
    import_status_history()
    import_completion_reports()
    import_maintenance_history()
    import_schedules()
    import_equipment()
    verify()

    print("\nDone!")
