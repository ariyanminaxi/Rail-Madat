"""
RailMadat — Seed 15 sample complaints + clear notifications

Creates complaints A-001 through A-015 using realistic data from the CSV files.
Some complaints have future dates to simulate upcoming issues.
Also clears dashboard_alerts table.
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SERVICE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
admin = create_client(SUPABASE_URL, SERVICE_KEY)

# Reporter user IDs from the users table (UUIDs)
REPORTERS = [
    "82915679-31f4-4ab0-84cc-0a1abe90b115",  # reporter1@railmaintain.in
    "4391f4c8-79f7-4fa8-a35a-1957e2610cf6",  # reporter2@railmaintain.in
]

# 15 complaints based on the CSV asset_master data
COMPLAINTS = [
    # A-001: Signal fault at Krishna Canal Junction (matches SIG-S02-01)
    {
        "complaint_id": "A-001",
        "reporter_user_id": REPORTERS[0],
        "state": "Andhra Pradesh",
        "city": "Krishna Canal Junction",
        "description": "Axle counter showing erratic readings at S-02. Intermittent false occupancy warnings detected during morning peak hours.",
        "asset_type": "Signal",
        "section_id": "S-02",
        "asset_id": "SIG-S02-01",
        "status": "Reported",
        "priority": "Critical",
        "created_at": "2026-08-25T09:15:00+05:30",
    },
    # A-002: Track ballast issue at Vijayawada
    {
        "complaint_id": "A-002",
        "reporter_user_id": REPORTERS[0],
        "state": "Andhra Pradesh",
        "city": "Vijayawada",
        "description": "Ballast section near km 45 showing excessive fouling. Drainage impaired during last monsoon inspection.",
        "asset_type": "Track",
        "section_id": "S-01",
        "asset_id": "TRK-S01-01",
        "status": "Reported",
        "priority": "High",
        "created_at": "2026-08-26T10:30:00+05:30",
    },
    # A-003: OHE section at Tenali
    {
        "complaint_id": "A-003",
        "reporter_user_id": REPORTERS[1],
        "state": "Andhra Pradesh",
        "city": "Tenali",
        "description": "OHE section showing voltage fluctuations. Contact wire sag observed near intermediate pole 23.",
        "asset_type": "Electrical Equipment",
        "section_id": "S-03",
        "asset_id": "ELE-S03-01",
        "status": "Reported",
        "priority": "Medium",
        "created_at": "2026-08-27T11:00:00+05:30",
    },
    # A-004: Point machine at Guntur
    {
        "complaint_id": "A-004",
        "reporter_user_id": REPORTERS[1],
        "state": "Andhra Pradesh",
        "city": "Guntur",
        "description": "Electric point machine PM-S04-01 not completing throw. Motor overheating after 3 consecutive switch operations.",
        "asset_type": "Point Machine",
        "section_id": "S-04",
        "asset_id": "PM-S04-01",
        "status": "Reported",
        "priority": "High",
        "created_at": "2026-08-28T08:45:00+05:30",
    },
    # A-005: Escalator at Vijayawada station
    {
        "complaint_id": "A-005",
        "reporter_user_id": REPORTERS[1],
        "state": "Andhra Pradesh",
        "city": "Vijayawada",
        "description": "Station escalator STN-S01-01 making grinding noise. Speed variation observed between steps.",
        "asset_type": "Station Machinery",
        "section_id": "S-01",
        "asset_id": "STN-S01-01",
        "status": "Reported",
        "priority": "Medium",
        "created_at": "2026-08-29T14:20:00+05:30",
    },
    # A-006: Track circuit at Tenali (future date)
    {
        "complaint_id": "A-006",
        "reporter_user_id": REPORTERS[0],
        "state": "Andhra Pradesh",
        "city": "Tenali",
        "description": "Track circuit SIG-S03-01 showing shunt sensitivity issues. Relay bouncing observed during wet conditions.",
        "asset_type": "Signal",
        "section_id": "S-03",
        "asset_id": "SIG-S03-01",
        "status": "Reported",
        "priority": "High",
        "created_at": "2026-09-01T09:00:00+05:30",
    },
    # A-007: Signal cable at Guntur
    {
        "complaint_id": "A-007",
        "reporter_user_id": REPORTERS[1],
        "state": "Andhra Pradesh",
        "city": "Guntur",
        "description": "Signal cable ELE-S04-01 insulation resistance dropped below 1 MΩ. Moisture ingress suspected near joint box.",
        "asset_type": "Electrical Equipment",
        "section_id": "S-04",
        "asset_id": "ELE-S04-01",
        "status": "Reported",
        "priority": "Low",
        "created_at": "2026-09-02T10:15:00+05:30",
    },
    # A-008: Point machine at Vijayawada
    {
        "complaint_id": "A-008",
        "reporter_user_id": REPORTERS[0],
        "state": "Andhra Pradesh",
        "city": "Vijayawada",
        "description": "PM-S01-01 detection circuit intermittent. Lock bar not fully engaging on reverse position.",
        "asset_type": "Point Machine",
        "section_id": "S-01",
        "asset_id": "PM-S01-01",
        "status": "Reported",
        "priority": "Critical",
        "created_at": "2026-09-03T07:30:00+05:30",
    },
    # A-009: Escalator at Krishna Canal Junction
    {
        "complaint_id": "A-009",
        "reporter_user_id": REPORTERS[0],
        "state": "Andhra Pradesh",
        "city": "Krishna Canal Junction",
        "description": "Station escalator STN-S02-01 emergency stop triggered twice this week. Handrail sensor alignment off.",
        "asset_type": "Station Machinery",
        "section_id": "S-02",
        "asset_id": "STN-S02-01",
        "status": "Reported",
        "priority": "High",
        "created_at": "2026-09-04T16:00:00+05:30",
    },
    # A-010: Rail joint at Guntur (future date)
    {
        "complaint_id": "A-010",
        "reporter_user_id": REPORTERS[1],
        "state": "Andhra Pradesh",
        "city": "Guntur",
        "description": "Rail joint TRK-S04-01 showing fatigue cracks at fishplate bolt holes. Immediate attention required before monsoon.",
        "asset_type": "Track",
        "section_id": "S-04",
        "asset_id": "TRK-S04-01",
        "status": "Reported",
        "priority": "Critical",
        "created_at": "2026-09-05T08:00:00+05:30",
    },
    # A-011: Colour light signal at Guntur
    {
        "complaint_id": "A-011",
        "reporter_user_id": REPORTERS[1],
        "state": "Andhra Pradesh",
        "city": "Guntur",
        "description": "SIG-S04-01 colour light signal showing dim aspect on yellow. LED driver board may need replacement.",
        "asset_type": "Signal",
        "section_id": "S-04",
        "asset_id": "SIG-S04-01",
        "status": "Reported",
        "priority": "Medium",
        "created_at": "2026-09-06T11:30:00+05:30",
    },
    # A-012: OHE at Vijayawada (future)
    {
        "complaint_id": "A-012",
        "reporter_user_id": REPORTERS[0],
        "state": "Andhra Pradesh",
        "city": "Vijayawada",
        "description": "OHE section ELE-S01-01 registration arms showing corrosion. Tension weights need recalibration.",
        "asset_type": "Electrical Equipment",
        "section_id": "S-01",
        "asset_id": "ELE-S01-01",
        "status": "Reported",
        "priority": "Medium",
        "created_at": "2026-09-08T09:45:00+05:30",
    },
    # A-013: Track at Tenali
    {
        "complaint_id": "A-013",
        "reporter_user_id": REPORTERS[1],
        "state": "Andhra Pradesh",
        "city": "Tenali",
        "description": "Ballast section TRK-S03-01 showing geometry defects. Vertical alignment off by 4mm in superelevation.",
        "asset_type": "Track",
        "section_id": "S-03",
        "asset_id": "TRK-S03-01",
        "status": "Reported",
        "priority": "High",
        "created_at": "2026-09-09T13:15:00+05:30",
    },
    # A-014: Escalator at Tenali
    {
        "complaint_id": "A-014",
        "reporter_user_id": REPORTERS[0],
        "state": "Andhra Pradesh",
        "city": "Tenali",
        "description": "Station escalator STN-S03-01 step chain tension uneven. Monthly inspection overdue.",
        "asset_type": "Station Machinery",
        "section_id": "S-03",
        "asset_id": "STN-S03-01",
        "status": "Reported",
        "priority": "Low",
        "created_at": "2026-09-10T15:00:00+05:30",
    },
    # A-015: Signal at Krishna Canal Junction (future)
    {
        "complaint_id": "A-015",
        "reporter_user_id": REPORTERS[0],
        "state": "Andhra Pradesh",
        "city": "Krishna Canal Junction",
        "description": "SIG-S02-02 colour light signal showing wrong aspect during夜间 testing. Approach locking timer seems extended.",
        "asset_type": "Signal",
        "section_id": "S-02",
        "asset_id": "SIG-S02-02",
        "status": "Reported",
        "priority": "Critical",
        "created_at": "2026-09-12T10:00:00+05:30",
    },
]


def clear_notifications():
    print("Clearing dashboard_alerts...")
    try:
        r = admin.table("dashboard_alerts").select("*").execute()
        for row in r.data:
            for pk in ["id", "alert_id"]:
                if pk in row:
                    admin.table("dashboard_alerts").delete().eq(pk, row[pk]).execute()
                    break
        print(f"  Cleared {len(r.data)} alerts")
    except Exception as e:
        print(f"  Error clearing alerts: {str(e)[:80]}")


def seed_complaints():
    print("\nSeeding 15 complaints (A-001 to A-015)...")
    
    # First check what exists
    existing = admin.table("complaints").select("complaint_id").execute()
    existing_ids = {c["complaint_id"] for c in existing.data}
    print(f"  Existing complaints: {existing_ids}")
    
    inserted = 0
    for c in COMPLAINTS:
        if c["complaint_id"] in existing_ids:
            print(f"  Skipping {c['complaint_id']} (already exists)")
            continue
        try:
            admin.table("complaints").insert(c).execute()
            inserted += 1
            print(f"  Inserted {c['complaint_id']}: {c['asset_type']} at {c['city']}")
        except Exception as e:
            print(f"  ERR {c['complaint_id']}: {str(e)[:100]}")
    
    print(f"\n  Total inserted: {inserted}")
    
    # Verify
    result = admin.table("complaints").select("complaint_id,status").order("complaint_id").execute()
    print(f"\n  All complaints in DB:")
    for c in result.data:
        print(f"    {c['complaint_id']} — {c['status']}")


if __name__ == "__main__":
    print("=" * 60)
    print("RailMadat — Seed Complaints + Clear Notifications")
    print("=" * 60)
    
    clear_notifications()
    seed_complaints()
    
    print("\nDone!")
