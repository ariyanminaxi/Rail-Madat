"""Workflow-sensitive Maintenance Prioritization Engine.

Takes the Maintenance Classifier's base_priority and applies deterministic
safety and workflow rules to produce the final_priority.

The engine ensures:
- Extreme safety risk → Emergency (always)
- Safety-Critical assets with Interrupted/Reopened status → Critical
- Escalated status → at least Critical
- Classifier cannot override safety rules
"""

from typing import List, Tuple

from app.maintenance_intelligence.config import CRITICAL_STATUSES, EMERGENCY_STATUSES


def calculate_final_priority(
    prediction: dict,
    context: dict,
) -> dict:
    """Apply workflow and safety rules to determine final priority.

    Args:
        prediction: Must contain "base_priority" key.
        context: Must contain "asset_criticality", "current_status",
                 and "safety_risk_level" keys.

    Returns:
        Dictionary with "final_priority" and "reasons" list.
    """
    priority = prediction.get("base_priority", "Medium")
    reasons = []

    valid_priorities = {"Low", "Medium", "High", "Critical", "Emergency"}
    if priority not in valid_priorities:
        priority = "Medium"
        reasons.append("Invalid base_priority defaulted to Medium")

    asset_criticality = context.get("asset_criticality", "Non-Critical")
    current_status = context.get("current_status", "New")
    safety_risk = context.get("safety_risk_level", "Low")

    # --- HARD SAFETY OVERRIDES ---

    if safety_risk == "Extreme":
        priority = "Emergency"
        reasons.append("Extreme safety risk overrides all priorities")

    elif (
        asset_criticality == "Safety-Critical"
        and current_status in CRITICAL_STATUSES
    ):
        if priority_order(priority) < priority_order("Critical"):
            priority = "Critical"
        reasons.append(f"Asset is safety-critical and status is {current_status}")

    elif current_status in EMERGENCY_STATUSES:
        if priority_order(priority) < priority_order("Critical"):
            priority = "Critical"
        reasons.append(f"Workflow status is {current_status}")

    # --- SOFT ESCALATION RULES ---

    if asset_criticality == "Safety-Critical":
        reasons.append("Asset is safety-critical")

    if current_status == "Interrupted":
        reasons.append("Work is currently interrupted")

    if current_status == "Reopened":
        reasons.append("Task was previously completed and reopened")

    if safety_risk == "High" and priority_order(priority) < priority_order("High"):
        priority = "High"
        reasons.append("High safety risk level")

    return {
        "final_priority": priority,
        "reasons": reasons,
    }


def priority_order(priority: str) -> int:
    """Return the numeric order of a priority level."""
    order = {
        "Low": 0,
        "Medium": 1,
        "High": 2,
        "Critical": 3,
        "Emergency": 4,
    }
    return order.get(priority, 1)


def requires_human_review(
    final_priority: str,
    confidence: float = None,
    confidence_threshold: float = 0.75,
    safety_risk: str = "Low",
) -> Tuple[bool, List[str]]:
    """Determine whether the case requires human verification."""
    reasons = []

    if final_priority in ("Critical", "Emergency"):
        reasons.append(f"Priority is {final_priority} — requires human verification")

    if confidence is not None and confidence < confidence_threshold:
        reasons.append(
            f"Model confidence ({confidence:.2f}) is below threshold ({confidence_threshold})"
        )

    if safety_risk == "Extreme":
        reasons.append("Extreme safety risk — mandatory human review")

    return len(reasons) > 0, reasons


def get_recommended_action(
    final_priority: str,
    fault_category: str,
    safety_risk: str,
) -> str:
    """Generate a recommended action based on the final assessment."""
    if final_priority == "Emergency":
        return "Immediate emergency response required"
    elif final_priority == "Critical":
        return "Immediate inspection required"
    elif final_priority == "High":
        return "Prioritised inspection within 24 hours"
    elif final_priority == "Medium":
        return "Schedule maintenance within standard timeframe"
    else:
        return "Include in routine maintenance schedule"
