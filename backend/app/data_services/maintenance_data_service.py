"""Maintenance Data Service — provides asset and maintenance context.

This service is the interface between storage (CSV, Supabase, PostgreSQL)
and the Maintenance Intelligence Service. It supplies stable dictionaries
to the inference pipeline and the Scheduling and Resource Allocation Engine.

Responsibilities:
  - Asset registry lookup
  - Maintenance history retrieval
  - Preventive-maintenance schedule retrieval
  - Overdue calculation inputs
  - Repeated failure counts
  - Deferral counts
  - Reopening counts
  - Workflow-history retrieval
  - Maintenance-team data
  - Equipment data
  - Normalization of CSV or database records
"""

from typing import Optional


def get_asset(asset_id: str) -> dict:
    """Retrieve asset details from the asset registry."""
    return {
        "asset_id": asset_id,
        "asset_type": "Unknown",
        "asset_criticality": "Non-Critical",
    }


def get_asset_context(asset_id: str) -> dict:
    """Retrieve asset and maintenance context for a given asset.

    In production this would query Supabase or PostgreSQL.
    For now it returns a default context.
    """
    return get_asset(asset_id)


def get_maintenance_history(asset_id: str) -> list:
    """Retrieve maintenance history records for an asset."""
    return []


def get_preventive_schedule(asset_id: str) -> list:
    """Retrieve preventive maintenance schedules for an asset."""
    return []


def get_workflow_history(asset_id: str) -> list:
    """Retrieve workflow status history for an asset."""
    return []


def get_resource_context(asset_id: str) -> dict:
    """Retrieve team and equipment context for an asset."""
    return {
        "assigned_team": None,
        "available_equipment": [],
    }


def get_maintenance_context(asset_id: str) -> dict:
    """Provide a stable maintenance context for intelligence and scheduling.

    Returns a consolidated dict with asset details, history, schedules,
    workflow history, and resource context.
    """
    return {
        "asset": get_asset(asset_id),
        "maintenance_history": get_maintenance_history(asset_id),
        "preventive_schedule": get_preventive_schedule(asset_id),
        "workflow_history": get_workflow_history(asset_id),
        "resource_context": get_resource_context(asset_id),
    }
