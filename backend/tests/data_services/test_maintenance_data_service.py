"""Tests for maintenance_data_service.py — Maintenance Data Service."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.data_services.maintenance_data_service import (
    get_asset,
    get_asset_context,
    get_maintenance_history,
    get_preventive_schedule,
    get_workflow_history,
    get_resource_context,
    get_maintenance_context,
)


def test_get_asset_returns_dict():
    result = get_asset("SIG-S02-04")
    assert result["asset_id"] == "SIG-S02-04"
    assert "asset_type" in result
    assert "asset_criticality" in result


def test_get_asset_context_matches_get_asset():
    ctx = get_asset_context("TRK-S01-02")
    assert ctx["asset_id"] == "TRK-S01-02"


def test_get_maintenance_history_returns_list():
    result = get_maintenance_history("SIG-S02-04")
    assert isinstance(result, list)


def test_get_preventive_schedule_returns_list():
    result = get_preventive_schedule("SIG-S02-04")
    assert isinstance(result, list)


def test_get_workflow_history_returns_list():
    result = get_workflow_history("SIG-S02-04")
    assert isinstance(result, list)


def test_get_resource_context_returns_dict():
    result = get_resource_context("SIG-S02-04")
    assert isinstance(result, dict)
    assert "assigned_team" in result
    assert "available_equipment" in result


def test_get_maintenance_context_has_all_keys():
    result = get_maintenance_context("SIG-S02-04")
    expected_keys = {"asset", "maintenance_history", "preventive_schedule",
                     "workflow_history", "resource_context"}
    assert expected_keys.issubset(result.keys())


def test_get_maintenance_context_asset_matches():
    ctx = get_maintenance_context("SIG-S02-04")
    assert ctx["asset"]["asset_id"] == "SIG-S02-04"
