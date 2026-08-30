"""
priority.py
RailMaintain — AI/ML Complaint Classification

Purpose
-------
Takes the classifier's output (asset_type, fault_category, base severity,
emergency/exception flags) and produces a final, explainable priority
recommendation plus a numeric priority_score for queue ordering.

This module NEVER makes a final safety decision or authorizes a block.
It only recommends a priority level and explains why — an authorized
manager can always override it (see backend API approval workflow).

Scope note: full escalation logic that depends on live operational data
(overdue_days, deferral_count, asset_criticality from the DB) belongs to
maintenance workflows / scheduling downstream. This module only uses what
the classifier already has: the complaint text and the classifier's own
output, plus an OPTIONAL asset_criticality hint if the backend API
chooses to pass one along.
"""

from typing import Dict, Optional


# ---------------------------------------------------------------------------
# 1. Base priority ranks (must match 03 Keywords & Data Dictionary)
# ---------------------------------------------------------------------------
PRIORITY_LEVELS = ["Low", "Medium", "High", "Critical"]
PRIORITY_RANK = {level: i for i, level in enumerate(PRIORITY_LEVELS)}  # Low=0 .. Critical=3


# ---------------------------------------------------------------------------
# 2. Fault category -> base priority weight
# ---------------------------------------------------------------------------
# Some fault categories are inherently riskier than others even at the
# same reported severity (e.g. a signal malfunction is more train-impacting
# than a station-machinery breakdown). This nudges priority, it does not
# override an emergency flag or a Critical severity.
FAULT_CATEGORY_WEIGHT = {
    "Signal malfunction": 1,
    "Obstruction": 1,
    "Electrical fault": 1,
    "Point machine failure": 1,
    "Track damage": 0,
    "Machinery breakdown": 0,
}

# Optional asset_criticality (if the backend API supplies it) nudges priority too.
ASSET_CRITICALITY_WEIGHT = {
    "Critical": 1,
    "High": 1,
    "Medium": 0,
    "Low": 0,
}


# ---------------------------------------------------------------------------
# 3. Suggested action per final priority
# ---------------------------------------------------------------------------
SUGGESTED_ACTION_BY_PRIORITY = {
    "Critical": "Immediate inspection",
    "High": "Priority inspection within 24 hours",
    "Medium": "Schedule inspection within a few days",
    "Low": "Add to routine maintenance queue",
}

# Numeric score per level, used only for sorting/queue display — not a
# safety judgment.
PRIORITY_SCORE = {"Low": 25, "Medium": 50, "High": 75, "Critical": 100}


def _clamp_rank(rank: int) -> int:
    return max(0, min(rank, len(PRIORITY_LEVELS) - 1))


def calculate_priority(
    classification: Dict,
    asset_criticality: Optional[str] = None,
) -> Dict:
    """
    Refine the classifier's base_priority into a final priority
    recommendation with an explanation and a numeric score.

    Parameters
    ----------
    classification : dict
        The output of classifier.classify_complaint(), must contain at
        least: complaint_id, fault_category, base_priority,
        human_review_required, and (from emergency_rules) whether an
        emergency was flagged — inferred here from human_review_required
        + base_priority == "Critical" since classify_complaint() already
        folds that in.
    asset_criticality : str, optional
        "Low" | "Medium" | "High" | "Critical" — if the calling system
        (backend API) already knows how critical this specific asset is.

    Returns
    -------
    dict, e.g.:
    {
        "complaint_id": "C-201",
        "base_priority": "High",
        "final_priority": "High",
        "priority_score": 75,
        "suggested_action": "Priority inspection within 24 hours",
        "escalated": false,
        "human_review_required": false,
        "reason": "..."
    }
    """
    complaint_id = classification.get("complaint_id", "UNKNOWN")
    fault_category = classification.get("fault_category")
    base_priority = classification.get("base_priority", "Medium")
    human_review_required = classification.get("human_review_required", False)

    if base_priority not in PRIORITY_LEVELS:
        base_priority = "Medium"

    rank = PRIORITY_RANK[base_priority]
    reasons = [f"Base severity from classifier: {base_priority}."]

    # A Critical rating (which already includes emergency-flagged
    # complaints, per classifier.py) is never adjusted further — a
    # critical task can never be silently downgraded, and it's already
    # at the ceiling so it can't be escalated further either.
    if base_priority == "Critical":
        final_rank = rank
        escalated = False
        reasons.append("Critical priority is never automatically adjusted.")
    else:
        adjustment = 0

        if fault_category in FAULT_CATEGORY_WEIGHT and FAULT_CATEGORY_WEIGHT[fault_category] > 0:
            adjustment += FAULT_CATEGORY_WEIGHT[fault_category]
            reasons.append(f"Fault category '{fault_category}' carries additional train-impact risk.")

        if asset_criticality in ASSET_CRITICALITY_WEIGHT and ASSET_CRITICALITY_WEIGHT[asset_criticality] > 0:
            adjustment += ASSET_CRITICALITY_WEIGHT[asset_criticality]
            reasons.append(f"Asset criticality '{asset_criticality}' supports escalation.")

        final_rank = _clamp_rank(rank + (1 if adjustment >= 2 else 0))
        escalated = final_rank > rank
        if not escalated:
            reasons.append("No escalation factors strong enough to raise priority.")

    final_priority = PRIORITY_LEVELS[final_rank]

    # Escalating into Critical territory always requires human review,
    # consistent with the ground rule that AI never finalizes a Critical
    # safety decision on its own.
    if final_priority == "Critical" and not human_review_required:
        human_review_required = True
        reasons.append("Escalated to Critical — human review required.")

    return {
        "complaint_id": complaint_id,
        "base_priority": base_priority,
        "final_priority": final_priority,
        "priority_score": PRIORITY_SCORE[final_priority],
        "suggested_action": SUGGESTED_ACTION_BY_PRIORITY[final_priority],
        "escalated": escalated,
        "human_review_required": human_review_required,
        "reason": " ".join(reasons),
    }


# ---------------------------------------------------------------------------
# Quick manual smoke test (run: python priority.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json
    from classifier import classify_complaint

    samples = [
        {"complaint_id": "C-201", "description": "Signal near S-02 is flickering and trains are slowing down.", "asset_id": "SIG-S02-04", "section_id": "S-02"},
        {"complaint_id": "C-202", "description": "Track joint is damaged near the station.", "asset_id": "TRK-S01-02", "section_id": "S-01"},
        {"complaint_id": "C-205", "description": "There has been a derailment near platform 3, urgent help needed.", "asset_id": "TRK-S04-01", "section_id": "S-04"},
    ]

    # Example: C-201 is on a High-criticality signal asset per (hypothetical) asset register
    criticality_lookup = {"C-201": "High"}

    for sample in samples:
        classification = classify_complaint(sample)
        priority_result = calculate_priority(
            classification,
            asset_criticality=criticality_lookup.get(sample["complaint_id"]),
        )
        print(json.dumps({"classification": classification, "priority": priority_result}, indent=2))
        print("-" * 60)
