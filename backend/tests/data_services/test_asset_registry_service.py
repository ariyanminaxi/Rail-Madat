"""Tests for asset_registry_service.py — Maintenance Data Service."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.data_services.asset_registry_service import (
    get_asset,
    get_assets_by_section,
    get_assets_by_department,
)


def test_get_asset_found():
    assets = [
        {"asset_id": "SIG-S02-04", "asset_type": "Signal", "section_id": "S-02", "department": "Signalling", "criticality": "High"},
        {"asset_id": "TRK-S01-02", "asset_type": "Track", "section_id": "S-01", "department": "Track", "criticality": "Medium"},
    ]
    result = get_asset("SIG-S02-04", assets)
    assert result is not None
    assert result["asset_type"] == "Signal"


def test_get_asset_not_found():
    assets = [{"asset_id": "SIG-S02-04"}]
    result = get_asset("NONEXISTENT", assets)
    assert result is None


def test_get_assets_by_section():
    assets = [
        {"asset_id": "A-1", "section_id": "S-01"},
        {"asset_id": "A-2", "section_id": "S-02"},
        {"asset_id": "A-3", "section_id": "S-01"},
    ]
    result = get_assets_by_section("S-01", assets)
    assert len(result) == 2


def test_get_assets_by_department():
    assets = [
        {"asset_id": "A-1", "department": "Track"},
        {"asset_id": "A-2", "department": "Signalling"},
    ]
    result = get_assets_by_department("Track", assets)
    assert len(result) == 1
    assert result[0]["asset_id"] == "A-1"
