"""
emergency_rules.py
RailMaintain — AI/ML Complaint Classification

Purpose
-------
Conservative, keyword-based safety net that runs BEFORE / ALONGSIDE the
classifier. This module never authorizes anything — it only flags
complaints that must be routed to a human for review.

Ground rule (per project safety spec):
    The AI must NEVER authorize a railway block, an emergency response,
    or any final safety decision. When in doubt, this module always
    prefers a false positive (unnecessary human review) over a false
    negative (a missed emergency).

This module is intentionally "dumb" — plain keyword matching, no ML —
because a safety gate should be simple, predictable, and easy to audit.
"""

import re
from typing import Dict, List


# ---------------------------------------------------------------------------
# 1. Emergency keywords -> force human review, never auto-confirmed
# ---------------------------------------------------------------------------
# Exact list from the project's Safety & Ground Rules / Keywords & Data
# Dictionary docs. Do not remove or "soften" any of these.
EMERGENCY_KEYWORDS: List[str] = [
    "broken rail",
    "derailment",
    "collision",
    "fire",
    "signal failure",
    "electrical danger",
    "track obstruction",
]

# A few realistic synonyms/phrasings reported by the public/staff.
# These do NOT replace the exact list above — they extend recall while
# staying conservative. Add more here as real complaint text is observed.
EMERGENCY_KEYWORD_SYNONYMS: Dict[str, List[str]] = {
    "broken rail": ["rail crack", "cracked rail", "rail fracture"],
    "derailment": ["derailed", "train off track", "off the rails"],
    "collision": ["train hit", "crash", "collided"],
    "fire": ["smoke", "burning", "sparks and flames"],
    "signal failure": ["signal not working", "signal down", "signal dead"],
    "electrical danger": ["live wire", "exposed wire", "electric shock", "sparking"],
    "track obstruction": ["object on track", "blocked track", "tree on track", "debris on track"],
}


# ---------------------------------------------------------------------------
# 2. Exception-type keywords (Section 11: Exception Handling & Recovery)
# ---------------------------------------------------------------------------
# These are NOT emergencies by themselves, but they identify the    # operational exception category so downstream systems (backend API / scheduling) can
# route the task correctly. Kept separate from EMERGENCY_KEYWORDS.
EXCEPTION_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "WEATHER": ["rain", "flood", "storm", "fog", "weather", "heavy wind", "waterlogged"],
    "TIME_INSUFFICIENT": ["not enough time", "ran out of time", "insufficient time"],
    "MATERIAL_UNAVAILABLE": ["material not available", "no spare parts", "parts unavailable", "out of stock"],
    "RESOURCE_UNAVAILABLE": ["team unavailable", "no team available", "equipment unavailable", "no equipment"],
    "TRACK_BLOCKED": ["track blocked", "track obstruction", "obstruction on track"],
    "COMMUNICATION_FAILURE": ["communication failure", "no signal", "unable to contact", "comms down", "network down"],
    "NEW_TRAIN_CONFLICT": ["train conflict", "unexpected train", "new train schedule", "extra train"],
    "ASSET_UNSAFE": ["unsafe", "dangerous condition", "hazardous", "not safe to operate"],
}


def _normalize(text: str) -> str:
    """Lowercase and collapse whitespace for reliable matching."""
    return " ".join(text.lower().split())


def _contains_phrase(text: str, phrase: str) -> bool:
    """
    Word-boundary match so short words (e.g. 'rain') don't false-positive
    inside unrelated words (e.g. 'trains'). Works for multi-word phrases too.
    """
    pattern = r"\b" + re.escape(phrase) + r"\b"
    return re.search(pattern, text) is not None


def check_emergency_keywords(complaint_text: str) -> Dict:
    """
    Scan complaint text for emergency keywords (exact list + synonyms).

    Returns
    -------
    dict with:
        is_emergency (bool)
        matched_keywords (list[str])  -- which canonical keyword(s) fired
        matched_terms (list[str])     -- the literal term(s) found in text
    """
    text = _normalize(complaint_text)
    matched_keywords: List[str] = []
    matched_terms: List[str] = []

    for keyword in EMERGENCY_KEYWORDS:
        if _contains_phrase(text, keyword):
            matched_keywords.append(keyword)
            matched_terms.append(keyword)
            continue
        # check synonyms for this keyword
        for synonym in EMERGENCY_KEYWORD_SYNONYMS.get(keyword, []):
            if _contains_phrase(text, synonym):
                matched_keywords.append(keyword)
                matched_terms.append(synonym)
                break

    return {
        "is_emergency": len(matched_keywords) > 0,
        "matched_keywords": matched_keywords,
        "matched_terms": matched_terms,
    }


def check_exception_types(complaint_text: str) -> Dict:
    """
    Scan complaint text for exception_type indicators.

    Returns
    -------
    dict with:
        exception_types (list[str])   -- e.g. ["WEATHER", "ASSET_UNSAFE"]
        matched_terms (dict)          -- exception_type -> list of matched terms
    """
    text = _normalize(complaint_text)
    exception_types: List[str] = []
    matched_terms: Dict[str, List[str]] = {}

    for exception_type, keywords in EXCEPTION_TYPE_KEYWORDS.items():
        hits = [kw for kw in keywords if _contains_phrase(text, kw)]
        if hits:
            exception_types.append(exception_type)
            matched_terms[exception_type] = hits

    return {
        "exception_types": exception_types,
        "matched_terms": matched_terms,
    }


def evaluate_emergency(complaint_id: str, complaint_text: str) -> Dict:
    """
    Main entry point for the backend API / classifier.py.

    Combines emergency-keyword detection and exception-type detection
    into a single conservative safety verdict. This function NEVER
    returns an "authorized" or "confirmed emergency" state — it only
    ever recommends routing to a human.

    Parameters
    ----------
    complaint_id : str   e.g. "C-201"
    complaint_text : str  raw complaint description

    Returns
    -------
    dict, e.g.:
    {
        "complaint_id": "C-201",
        "human_review_required": true,
        "is_emergency_flagged": true,
        "matched_keywords": ["signal failure"],
        "exception_types": [],
        "reason": "Urgent human verification required. Emergency keyword(s) detected: signal failure."
    }
    """
    emergency_result = check_emergency_keywords(complaint_text)
    exception_result = check_exception_types(complaint_text)

    is_emergency = emergency_result["is_emergency"]
    human_review_required = is_emergency  # exception types alone don't force review here;
                                           # classifier.py applies its own confidence threshold too

    if is_emergency:
        keyword_list = ", ".join(emergency_result["matched_keywords"])
        reason = (
            f"Urgent human verification required. "
            f"Emergency keyword(s) detected: {keyword_list}."
        )
    elif exception_result["exception_types"]:
        exc_list = ", ".join(exception_result["exception_types"])
        reason = f"Possible exception condition(s) detected: {exc_list}. Review recommended."
    else:
        reason = "No emergency or exception keywords detected."

    return {
        "complaint_id": complaint_id,
        "human_review_required": human_review_required,
        "is_emergency_flagged": is_emergency,
        "matched_keywords": emergency_result["matched_keywords"],
        "exception_types": exception_result["exception_types"],
        "reason": reason,
    }


# ---------------------------------------------------------------------------
# Quick manual smoke test (run: python emergency_rules.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    samples = [
        ("C-201", "Signal near S-02 is flickering and trains are slowing down."),
        ("C-202", "There has been a derailment near platform 3, urgent help needed."),
        ("C-203", "Track joint is damaged near the station."),
        ("C-204", "Electrical equipment is producing sparks and smoke."),
        ("C-205", "Heavy rain has flooded the track near S-04, work delayed."),
        ("C-206", "Point machine is not operating, no team available to fix it."),
    ]

    for cid, text in samples:
        result = evaluate_emergency(cid, text)
        print(result)
