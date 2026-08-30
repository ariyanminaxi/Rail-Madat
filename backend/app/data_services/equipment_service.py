"""Equipment Service — provides equipment availability and lookup data.

Tracks equipment status, assignment, and availability for scheduling.
"""

import json
import os
from typing import Optional


def load_equipment(json_path: Optional[str] = None) -> list:
    """Load equipment data from JSON file.

    Returns a list of dicts with at least:
        equipment_id, equipment_type, status, assigned_team_id, section_id
    """
    if json_path is None:
        json_path = os.path.join("data", "reference", "equipment.json")
    if not os.path.exists(json_path):
        return []
    with open(json_path) as f:
        return json.load(f)


def get_equipment(equipment_id: str, equipment: Optional[list] = None) -> Optional[dict]:
    """Look up a single piece of equipment by equipment_id."""
    if equipment is None:
        equipment = load_equipment()
    for eq in equipment:
        if eq.get("equipment_id") == equipment_id:
            return eq
    return None


def get_available_equipment(equipment: Optional[list] = None) -> list:
    """Return all equipment with status 'available'."""
    if equipment is None:
        equipment = load_equipment()
    return [e for e in equipment if e.get("status") == "available"]


def get_equipment_by_section(section_id: str, equipment: Optional[list] = None) -> list:
    """Return all equipment assigned to a given section."""
    if equipment is None:
        equipment = load_equipment()
    return [e for e in equipment if e.get("section_id") == section_id]
