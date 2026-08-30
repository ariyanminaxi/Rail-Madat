"""Asset Registry Service — provides asset lookup from the asset registry.

Reads asset data from CSV, database, or memory depending on DATA_MODE.
Returns all fields from the asset registry schema.
"""

import csv
import os
from typing import Optional

from app.config import DATA_MODE, CSV_DATA_PATH


# In-memory store for test mode
_memory_store: dict = {}


def load_asset_registry(csv_path: Optional[str] = None) -> list:
    """Load asset registry from CSV file.

    Returns a list of dicts with all asset registry fields.
    """
    if csv_path is None:
        csv_path = os.path.join(CSV_DATA_PATH, "reference", "asset_registry.csv")
    if not os.path.exists(csv_path):
        return []
    with open(csv_path, newline="") as f:
        return list(csv.DictReader(f))


def _get_asset_full_fields(asset: dict) -> dict:
    """Return a normalized asset dict with all required fields."""
    return {
        "asset_id": asset.get("asset_id"),
        "asset_type": asset.get("asset_type"),
        "asset_subtype": asset.get("asset_subtype"),
        "state": asset.get("state"),
        "city": asset.get("city"),
        "section_id": asset.get("section_id"),
        "department": asset.get("department"),
        "asset_criticality": asset.get("asset_criticality"),
        "operational_status": asset.get("current_status", asset.get("operational_status", "Working")),
        "last_maintenance_date": asset.get("last_maintenance_date"),
        "next_due_date": asset.get("next_due_date"),
        "is_overdue": asset.get("is_overdue", "False"),
        "maintenance_interval_days": asset.get("maintenance_interval_days"),
    }


def get_asset(asset_id: str, assets: Optional[list] = None) -> Optional[dict]:
    """Look up a single asset by asset_id.

    Returns all fields from the asset registry.
    """
    if DATA_MODE == "memory":
        raw = _memory_store.get(asset_id)
        return _get_asset_full_fields(raw) if raw else None

    if assets is None:
        assets = load_asset_registry()

    for asset in assets:
        if asset.get("asset_id") == asset_id:
            return _get_asset_full_fields(asset)
    return None


def get_assets_by_section(section_id: str, assets: Optional[list] = None) -> list:
    """Return all assets in a given section."""
    if DATA_MODE == "memory":
        return [_get_asset_full_fields(a) for a in _memory_store.values() if a.get("section_id") == section_id]

    if assets is None:
        assets = load_asset_registry()
    return [_get_asset_full_fields(a) for a in assets if a.get("section_id") == section_id]


def get_assets_by_department(department: str, assets: Optional[list] = None) -> list:
    """Return all assets belonging to a department."""
    if DATA_MODE == "memory":
        return [_get_asset_full_fields(a) for a in _memory_store.values() if a.get("department") == department]

    if assets is None:
        assets = load_asset_registry()
    return [_get_asset_full_fields(a) for a in assets if a.get("department") == department]


def save_asset(asset_data: dict) -> dict:
    """Save an asset to the in-memory store (test mode only)."""
    asset_id = asset_data.get("asset_id")
    if not asset_id:
        raise ValueError("asset_id is required")
    _memory_store[asset_id] = asset_data
    return _get_asset_full_fields(asset_data)


def reset_memory_store():
    """Clear the in-memory store (test mode only)."""
    _memory_store.clear()
