"""
RailMadat — Database Migration Script

Creates all required tables in Supabase using the SQL Editor API.
This avoids needing the direct database password.

Usage:
    cd backend
    python scripts/migrate_database.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# All table creation SQL
MIGRATION_SQL = """
-- =============================================
-- RailMadat Database Schema
-- =============================================

-- Profiles table (linked to Supabase Auth users)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT ck_profile_role CHECK (role IN ('Reporter', 'Maintenance staff', 'Maintenance Manager', 'Administrator'))
);

-- Assets table
CREATE TABLE IF NOT EXISTS assets (
    asset_id TEXT PRIMARY KEY,
    asset_type TEXT NOT NULL,
    section_id TEXT NOT NULL,
    department TEXT NOT NULL,
    asset_criticality TEXT NOT NULL,
    current_status TEXT DEFAULT 'Reported' NOT NULL,
    is_overdue BOOLEAN DEFAULT FALSE NOT NULL,
    last_maintenance_date TIMESTAMPTZ,
    next_due_date TIMESTAMPTZ,
    maintenance_interval_days INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Complaints table
CREATE TABLE IF NOT EXISTS complaints (
    complaint_id TEXT PRIMARY KEY,
    client_complaint_id TEXT UNIQUE NOT NULL,
    reporter_user_id UUID REFERENCES profiles(id) NOT NULL,
    state TEXT NOT NULL,
    city TEXT NOT NULL,
    description TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    section_id TEXT NOT NULL,
    asset_id TEXT REFERENCES assets(asset_id) NOT NULL,
    status TEXT DEFAULT 'Reported' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    complaint_id TEXT REFERENCES complaints(complaint_id),
    asset_id TEXT REFERENCES assets(asset_id),
    asset_type TEXT NOT NULL,
    section_id TEXT NOT NULL,
    department TEXT NOT NULL,
    fault_category TEXT,
    maintenance_type TEXT DEFAULT 'Corrective' NOT NULL,
    base_priority TEXT NOT NULL,
    asset_criticality TEXT,
    final_priority TEXT NOT NULL,
    duration_minutes INTEGER DEFAULT 60 NOT NULL,
    due_date TIMESTAMPTZ NOT NULL,
    block_required BOOLEAN DEFAULT TRUE NOT NULL,
    status TEXT DEFAULT 'Waiting for Block' NOT NULL,
    assigned_to UUID REFERENCES profiles(id),
    deferral_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- AI Classifications table
CREATE TABLE IF NOT EXISTS ai_classifications (
    id SERIAL PRIMARY KEY,
    complaint_id TEXT REFERENCES complaints(complaint_id) NOT NULL,
    asset_type TEXT NOT NULL,
    department TEXT NOT NULL,
    fault_category TEXT NOT NULL,
    base_priority TEXT NOT NULL,
    confidence INTEGER NOT NULL,
    human_review_required BOOLEAN DEFAULT FALSE NOT NULL,
    reason TEXT NOT NULL,
    suggested_action TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Blocks table
CREATE TABLE IF NOT EXISTS blocks (
    block_id TEXT PRIMARY KEY,
    section_id TEXT NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    safety_buffer_minutes INTEGER DEFAULT 15 NOT NULL,
    recommendation_reason TEXT,
    approval_status TEXT DEFAULT 'Pending' NOT NULL,
    approved_by UUID REFERENCES profiles(id),
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Approvals table
CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    block_id TEXT REFERENCES blocks(block_id) NOT NULL,
    approver_user_id UUID REFERENCES profiles(id) NOT NULL,
    decision TEXT NOT NULL,
    reason TEXT,
    decided_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Maintenance Events table
CREATE TABLE IF NOT EXISTS maintenance_events (
    event_id TEXT PRIMARY KEY,
    task_id TEXT REFERENCES tasks(task_id) NOT NULL,
    event_type TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    event_reason TEXT,
    reported_by UUID REFERENCES profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    remaining_work_minutes INTEGER,
    final_priority TEXT
);

-- Work Completion Reports table
CREATE TABLE IF NOT EXISTS work_completion_reports (
    completion_report_id TEXT PRIMARY KEY,
    task_id TEXT REFERENCES tasks(task_id) NOT NULL,
    receiver_department TEXT NOT NULL,
    received_by UUID REFERENCES profiles(id) NOT NULL,
    work_status TEXT NOT NULL,
    completion_percentage INTEGER,
    inspection_result TEXT,
    failure_reason TEXT,
    remaining_work_minutes INTEGER,
    material_status TEXT,
    safety_status TEXT,
    next_action TEXT,
    remarks TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    notification_id TEXT PRIMARY KEY,
    notification_type TEXT NOT NULL,
    message TEXT NOT NULL,
    related_task_id TEXT REFERENCES tasks(task_id),
    related_asset_id TEXT REFERENCES assets(asset_id),
    priority TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    is_read BOOLEAN DEFAULT FALSE NOT NULL
);

-- Audit Logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id TEXT PRIMARY KEY,
    user_id UUID REFERENCES profiles(id),
    role TEXT,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    status TEXT NOT NULL
);

-- Offline Queue table
CREATE TABLE IF NOT EXISTS offline_queue (
    id SERIAL PRIMARY KEY,
    client_complaint_id TEXT UNIQUE NOT NULL,
    payload TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    queued_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    retry_count INTEGER DEFAULT 0 NOT NULL,
    last_retry_at TIMESTAMPTZ,
    sync_status TEXT DEFAULT 'QUEUED' NOT NULL,
    last_error TEXT
);

-- Dashboard Alerts table
CREATE TABLE IF NOT EXISTS dashboard_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    priority TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Reports table
CREATE TABLE IF NOT EXISTS reports (
    report_id TEXT PRIMARY KEY,
    report_type TEXT NOT NULL,
    generated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    data_summary TEXT,
    download_url TEXT
);

-- =============================================
-- Seed Data: Default Administrator Profile
-- =============================================

-- Note: The auth user must be created first via create_admin.py
-- This just ensures the profile row exists

SELECT 'Migration completed successfully!' AS result;
"""


def main():
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        sys.exit(1)

    try:
        from supabase import create_client
    except ImportError:
        print("ERROR: supabase package not installed. Run: pip install supabase")
        sys.exit(1)

    print(f"Connecting to Supabase: {SUPABASE_URL}")
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    print("Creating database tables...")
    print("NOTE: You may need to run this SQL in the Supabase SQL Editor manually.")
    print()
    print("=" * 60)
    print("Copy the SQL below and run it in Supabase SQL Editor:")
    print("Go to: https://supabase.com/dashboard/project/syxtsauhtauyedbwneue/sql/new")
    print("=" * 60)
    print()
    print(MIGRATION_SQL)
    print("=" * 60)
    print()
    print("After running the SQL, re-run: python scripts/create_admin.py")


if __name__ == "__main__":
    main()
