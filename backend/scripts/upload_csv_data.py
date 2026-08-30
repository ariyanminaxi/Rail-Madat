"""
Upload all CSV files to Supabase database.
Run from backend directory: python scripts/upload_csv_data.py
"""

import os
import csv
import sys
from io import StringIO
from dotenv import load_dotenv

load_dotenv()

from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SERVICE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

admin = create_client(SUPABASE_URL, SERVICE_KEY)

# CSV file paths (relative to project root)
CSV_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "csv_data")

# Table mapping: CSV file -> Supabase table name
TABLE_MAP = {
    "asset_master.csv": "asset_registry",
    "teams.csv": "maintenance_teams",
    "equipment.csv": "equipment",
    "maintenance_history.csv": "maintenance_history",
    "maintenance_schedules.csv": "maintenance_schedules",
    "maintenance_status_history.csv": "workflow_status_history",
    "work_completion_reports.csv": "work_completion_reports",
}

# Column mapping for tables where CSV columns differ from DB columns
COLUMN_MAP = {
    "asset_registry": {
        # CSV has 'current_status' but DB has 'operational_status'
        # CSV has 'is_overdue' as string 'True'/'False'
    },
    "maintenance_teams": {
        # CSV team_id needs to match existing format
    },
}


def clean_value(val):
    """Clean a CSV value for database insertion."""
    if val is None or val == "":
        return None
    val = val.strip()
    if val.lower() == "true":
        return True
    if val.lower() == "false":
        return False
    return val


def read_csv(filepath):
    """Read CSV file and return list of dicts."""
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cleaned = {}
            for k, v in row.items():
                cleaned[k] = clean_value(v)
            rows.append(cleaned)
    return rows


def upload_to_table(table_name, rows, batch_size=50):
    """Upload rows to a Supabase table."""
    total = len(rows)
    success = 0
    errors = 0

    for i in range(0, total, batch_size):
        batch = rows[i : i + batch_size]
        try:
            result = admin.table(table_name).insert(batch).execute()
            success += len(batch)
        except Exception as e:
            error_msg = str(e)
            # If batch fails, try one by one
            for row in batch:
                try:
                    admin.table(table_name).insert(row).execute()
                    success += 1
                except Exception as e2:
                    errors += 1
                    if errors <= 5:
                        print(f"  ERROR: {e2}")

    return success, errors


def process_role4_dataset(filepath):
    """Process the role4 classification dataset into complaints, ai_classifications, and maintenance_tasks."""
    rows = read_csv(filepath)
    
    complaints = []
    ai_classifications = []
    tasks = []
    
    for row in rows:
        # Complaint
        complaint = {
            "complaint_id": row["complaint_id"],
            "reporter_user_id": None,  # Will be set later
            "state": row.get("state", "Andhra Pradesh"),
            "city": row.get("city", "Unknown"),
            "section_id": row.get("section_id", "S-01"),
            "asset_type": row.get("asset_type", "Unknown"),
            "asset_id": row.get("asset_id"),
            "description": row.get("description", ""),
            "status": row.get("status", "Reported"),
        }
        complaints.append(complaint)
        
        # AI Classification
        ai_class = {
            "complaint_id": row["complaint_id"],
            "department": row.get("target_department", "Track"),
            "fault_category": row.get("target_fault_category", "Unknown"),
            "severity": row.get("target_base_priority", "Medium"),
            "base_priority": row.get("target_base_priority", "Medium"),
            "confidence": float(row.get("target_confidence", 0.5)),
            "requires_human_review": row.get("target_human_review_required", "False").lower() == "true",
            "model_version": "v1.0",
        }
        ai_classifications.append(ai_class)
        
        # Task
        task = {
            "task_id": row["task_id"],
            "complaint_id": row["complaint_id"],
            "asset_id": row.get("asset_id"),
            "section_id": row.get("section_id", "S-01"),
            "department": row.get("target_department", "Track"),
            "priority": row.get("target_final_priority", "Medium"),
            "status": row.get("status", "Reported"),
        }
        tasks.append(task)
    
    return complaints, ai_classifications, tasks


def main():
    print("=" * 60)
    print("RailMadat CSV Data Upload")
    print("=" * 60)
    
    # Check if CSV directory exists
    if not os.path.exists(CSV_DIR):
        print(f"\nERROR: CSV directory not found: {CSV_DIR}")
        print("Please create the directory and place CSV files there.")
        print(f"Expected path: {os.path.abspath(CSV_DIR)}")
        return
    
    # List available CSV files
    csv_files = [f for f in os.listdir(CSV_DIR) if f.endswith(".csv")]
    print(f"\nFound {len(csv_files)} CSV files:")
    for f in csv_files:
        size = os.path.getsize(os.path.join(CSV_DIR, f))
        print(f"  - {f} ({size:,} bytes)")
    
    # Process standard tables
    for csv_file, table_name in TABLE_MAP.items():
        filepath = os.path.join(CSV_DIR, csv_file)
        if not os.path.exists(filepath):
            print(f"\nSKIP: {csv_file} not found")
            continue
        
        print(f"\n--- {csv_file} -> {table_name} ---")
        rows = read_csv(filepath)
        print(f"  Read {len(rows)} rows")
        
        if len(rows) == 0:
            print("  SKIP: No data")
            continue
        
        # Show first row columns
        print(f"  Columns: {list(rows[0].keys())}")
        
        success, errors = upload_to_table(table_name, rows)
        print(f"  Uploaded: {success} success, {errors} errors")
    
    # Process role4 dataset (special handling)
    role4_file = "role4_maintenance_classification_dataset.csv"
    role4_path = os.path.join(CSV_DIR, role4_file)
    if os.path.exists(role4_path):
        print(f"\n--- {role4_file} -> complaints + ai_classifications + maintenance_tasks ---")
        complaints, ai_classes, tasks = process_role4_dataset(role4_path)
        
        print(f"  Complaints: {len(complaints)}")
        s, e = upload_to_table("complaints", complaints)
        print(f"  Uploaded: {s} success, {e} errors")
        
        print(f"  AI Classifications: {len(ai_classes)}")
        s, e = upload_to_table("ai_classifications", ai_classes)
        print(f"  Uploaded: {s} success, {e} errors")
        
        print(f"  Tasks: {len(tasks)}")
        s, e = upload_to_table("maintenance_tasks", tasks)
        print(f"  Uploaded: {s} success, {e} errors")
    
    # Final verification
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    
    tables_to_check = [
        "asset_registry", "maintenance_teams", "equipment",
        "complaints", "ai_classifications", "maintenance_tasks",
        "workflow_status_history", "maintenance_history",
        "maintenance_schedules", "work_completion_reports",
    ]
    
    for t in tables_to_check:
        try:
            r = admin.table(t).select("*", count="exact").execute()
            print(f"  {t}: {r.count} rows")
        except Exception as e:
            print(f"  {t}: ERROR - {str(e)[:80]}")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
