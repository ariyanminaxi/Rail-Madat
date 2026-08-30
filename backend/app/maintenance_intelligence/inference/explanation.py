"""Generate plain-language explanations for Maintenance Intelligence predictions."""

from typing import List


def generate_explanation(
    prediction: dict,
    context: dict,
    priority_reasons: List[str],
    confidence_info: dict,
) -> List[str]:
    """Generate a complete explanation for the prediction."""
    explanations = []

    for reason in priority_reasons:
        explanations.append(reason)

    asset_criticality = context.get("asset_criticality", "")
    if asset_criticality and "Asset is safety-critical" not in " ".join(explanations):
        if asset_criticality in ("Safety-Critical", "Important"):
            explanations.append(f"Asset criticality: {asset_criticality}")

    service_impact = context.get("service_impact_level", "")
    if service_impact and service_impact in ("Major", "Severe"):
        explanations.append(f"Service impact is {service_impact.lower()}")

    days_overdue = context.get("days_overdue", 0)
    if days_overdue and days_overdue > 0:
        explanations.append(f"Task is {days_overdue} day(s) overdue")

    failure_count = context.get("failure_count_30_days", 0)
    if failure_count and failure_count > 0:
        explanations.append(
            f"Fault has occurred {failure_count} time(s) in the previous 30 days"
        )

    if confidence_info.get("human_review_required", False):
        confidence = confidence_info.get("confidence")
        if confidence is not None:
            explanations.append(
                f"Model confidence ({confidence:.2f}) is below threshold "
                f"— human review recommended"
            )
        else:
            explanations.append("Confidence score unavailable — human review required")

    if not explanations:
        explanations.append("Standard classification applied — no special escalation factors")

    return explanations


def format_explanation_for_display(explanations: List[str]) -> str:
    """Format explanation list as a readable string."""
    if not explanations:
        return "No explanation available."

    lines = ["Reasons:"]
    for i, reason in enumerate(explanations, 1):
        lines.append(f"  {i}. {reason}")
    return "\n".join(lines)
