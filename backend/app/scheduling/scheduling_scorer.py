"""
scheduling_scorer.py — Scheduling and Resource Allocation Engine

Ranks candidate free windows so the "best" recommendation is chosen first.
Lower score = better. Prefers earlier + night-time windows, and prioritizes
bundles containing a Critical task or overdue preventive work.
"""

from datetime import datetime, time


def score_window(window_start: datetime, has_critical: bool, has_overdue: bool) -> int:
    score = window_start.hour * 60 + window_start.minute  # earlier is better

    night_start, night_end = time(0, 0), time(5, 0)
    if not (night_start <= window_start.time() < night_end):
        score += 500  # penalty for non-night-time window

    if has_critical:
        score -= 150
    if has_overdue:
        score -= 50

    return score


def rank_windows(windows, has_critical: bool, has_overdue: bool):
    """windows: list of (start_dt, end_dt). Returns sorted list, best first."""
    return sorted(windows, key=lambda w: score_window(w[0], has_critical, has_overdue))
