"""Maintenance Team Service — provides maintenance team data.

Reads team data from JSON or database and provides team lookup
by team_id, section, or qualification.
"""

import json
import os
from typing import Optional


def load_teams(json_path: Optional[str] = None) -> list:
    """Load team data from JSON file.

    Returns a list of dicts with at least:
        team_id, section_id, is_reserve, status, qualified_sections
    """
    if json_path is None:
        json_path = os.path.join("data", "reference", "teams.json")
    if not os.path.exists(json_path):
        return []
    with open(json_path) as f:
        return json.load(f)


def get_team(team_id: str, teams: Optional[list] = None) -> Optional[dict]:
    """Look up a single team by team_id."""
    if teams is None:
        teams = load_teams()
    for team in teams:
        if team.get("team_id") == team_id:
            return team
    return None


def get_teams_by_section(section_id: str, teams: Optional[list] = None) -> list:
    """Return all teams assigned to a given section."""
    if teams is None:
        teams = load_teams()
    return [t for t in teams if t.get("section_id") == section_id]


def get_available_teams(teams: Optional[list] = None) -> list:
    """Return all teams with status 'available'."""
    if teams is None:
        teams = load_teams()
    return [t for t in teams if t.get("status") == "available"]
