"""Valid workflow statuses in the maintenance lifecycle."""

VALID_STATUSES = [
    "New",
    "Assigned",
    "In Progress",
    "Interrupted",
    "Reopened",
    "Escalated",
    "Completed",
    "Cancelled",
]

VALID_SEVERITIES = ["Low", "Medium", "High", "Critical"]

VALID_PRIORITIES = [
    "Low",
    "Medium",
    "High",
    "Critical",
    "Emergency",
]

VALID_SAFETY_RISK_LEVELS = ["Low", "Medium", "High", "Extreme"]
VALID_SERVICE_IMPACT_LEVELS = ["Negligible", "Minor", "Major", "Severe"]
VALID_ASSET_CRITICALITY_LEVELS = [
    "Non-Critical",
    "Operational",
    "Important",
    "Safety-Critical",
]
