"""Generate the maintenance cases training dataset."""

import csv
import random
from pathlib import Path

random.seed(42)

DEPARTMENTS = ["Track", "Signalling", "Electrical", "Civil", "Telecom", "Mechanical"]
FAULT_CATEGORIES = [
    "Signal malfunction", "Track defect", "Electrical fault",
    "Structural damage", "Mechanical failure", "Communication failure",
    "Ballast issue", "Switch failure",
]
SEVERITIES = ["Low", "Medium", "High", "Critical"]
PRIORITIES = ["Low", "Medium", "High", "Critical", "Emergency"]
ASSET_TYPES = ["Signal", "Track", "Electrical", "Civil", "Telecom", "Mechanical"]
CRITICALITY = ["Non-Critical", "Operational", "Important", "Safety-Critical"]
STATUSES = ["New", "Assigned", "In Progress", "Interrupted", "Reopened", "Escalated", "Completed", "Cancelled"]
SAFETY_RISKS = ["Low", "Medium", "High", "Extreme"]
SERVICE_IMPACTS = ["Negligible", "Minor", "Major", "Severe"]

TEMPLATES = {
    "Signalling": [
        "Signal near {loc} is flickering intermittently",
        "Signal aspect showing wrong colour at {loc}",
        "Defective axle counter at station {loc}",
        "Signal control panel unresponsive at {loc}",
        "Switch blades not sealing properly at {loc}",
    ],
    "Track": [
        "Broken rail detected near {loc}",
        "Rail head shelling in section {loc}",
        "Track geometry irregularity at {loc}",
        "Sleeper deterioration near {loc}",
        "Ballast pumping under sleepers at {loc}",
    ],
    "Electrical": [
        "Overhead line conductor sagging near {loc}",
        "Transformer oil leak at substation {loc}",
        "Insulator flashover on OHE mast {loc}",
        "Catenary dropper broken near {loc}",
        "Conductor rail support bracket corroded at {loc}",
    ],
    "Civil": [
        "Tunnel lining showing water seepage at {loc}",
        "Bridge deck spalling concrete near {loc}",
        "Level crossing barrier not operating at {loc}",
        "Platform edge damaged near {loc}",
        "Foundation settlement at {loc}",
    ],
    "Telecom": [
        "Telecom cable cut near {loc}",
        "Communication failure at station {loc}",
        "Fibre optic cable damaged near {loc}",
        "Signal cable insulation breakdown at {loc}",
        "Telecom repeater station malfunction at {loc}",
    ],
    "Mechanical": [
        "Point machine jammed at {loc}",
        "Brake cylinder pressure loss at {loc}",
        "Coupler knuckle fracture near {loc}",
        "Bearing failure on wagon at {loc}",
        "Gearbox oil leak at {loc}",
    ],
}

LOCATIONS = [f"S-{i:02d}" for i in range(1, 31)] + [f"KM-{i}" for i in range(10, 200, 10)]


def generate_case(case_id):
    dept = random.choice(DEPARTMENTS)
    asset_type = dept if dept in ASSET_TYPES else random.choice(ASSET_TYPES)
    criticality = random.choices(CRITICALITY, weights=[15, 25, 30, 30])[0]
    status = random.choices(STATUSES, weights=[20, 15, 15, 10, 8, 7, 20, 5])[0]
    safety = random.choices(SAFETY_RISKS, weights=[30, 25, 25, 20])[0]
    service = random.choices(SERVICE_IMPACTS, weights=[15, 35, 30, 20])[0]
    days = random.choices([0, 1, 2, 3, 5, 7, 14, 30], weights=[30, 15, 15, 10, 10, 10, 5, 5])[0]
    failures = random.choices([0, 1, 2, 3, 4], weights=[40, 25, 15, 10, 10])[0]

    # Fault category matches department
    dept_to_cat = {
        "Signalling": ["Signal malfunction", "Switch failure"],
        "Track": ["Track defect", "Ballast issue"],
        "Electrical": ["Electrical fault"],
        "Civil": ["Structural damage"],
        "Telecom": ["Communication failure"],
        "Mechanical": ["Mechanical failure"],
    }
    fault_cat = random.choice(dept_to_cat.get(dept, FAULT_CATEGORIES))

    # Severity and priority based on safety and criticality
    if safety == "Extreme":
        severity = random.choice(["Critical", "High"])
        priority = random.choice(["Critical", "Emergency"])
    elif safety == "High" and criticality == "Safety-Critical":
        severity = random.choice(["High", "Critical"])
        priority = random.choice(["High", "Critical"])
    elif safety == "High":
        severity = random.choice(["Medium", "High"])
        priority = random.choice(["Medium", "High"])
    else:
        severity = random.choice(["Low", "Medium"])
        priority = random.choice(["Low", "Medium"])

    template = random.choice(TEMPLATES.get(dept, TEMPLATES["Track"]))
    loc = random.choice(LOCATIONS)
    text = template.format(loc=loc)

    return [case_id, text, asset_type, criticality, status, days, failures,
            0, 0, safety, service, dept, fault_cat, severity, priority, 1]


def main():
    out_dir = Path(__file__).parent.parent / "datasets"
    csv_path = out_dir / "maintenance_cases.csv"

    header = ["case_id", "complaint_text", "asset_type", "asset_criticality",
              "current_status", "days_overdue", "failure_count_30_days",
              "deferral_count", "reopen_count", "safety_risk_level",
              "service_impact_level", "department", "fault_category",
              "severity", "base_priority", "verified_by_human"]

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for i in range(1, 201):
            writer.writerow(generate_case(f"TC-{i:03d}"))

    print(f"Generated {csv_path}")

    # Also generate workflow_history.csv
    hist_path = out_dir / "workflow_history.csv"
    with open(hist_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "previous_status", "new_status", "changed_by", "change_timestamp"])
        for i in range(1, 201):
            writer.writerow([f"TC-{i:03d}", "New", "Assigned", "system", "2025-01-01 08:00:00"])

    print(f"Generated {hist_path}")


if __name__ == "__main__":
    main()
