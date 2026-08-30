import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.scheduling.resource_allocator import allocate_team
from app.scheduling.preemption_manager import get_preemption_status


def test_primary_team_assigned_when_available():
    task = {"required_team": "TEAM-A", "section_id": "S-01"}
    teams = [{"team_id": "TEAM-A", "section_id": "S-01", "is_reserve": False, "status": "available", "qualified_sections": ["S-01"]}]
    result = allocate_team(task, teams, {})
    assert result["team_assigned"] == "TEAM-A"
    assert result["escalated"] is False


def test_falls_back_to_reserve_team():
    task = {"required_team": "TEAM-A", "section_id": "S-01"}
    teams = [
        {"team_id": "TEAM-A", "section_id": "S-01", "is_reserve": False, "status": "busy", "qualified_sections": ["S-01"]},
        {"team_id": "TEAM-RESERVE", "section_id": "S-01", "is_reserve": True, "status": "available", "qualified_sections": ["S-01"]},
    ]
    result = allocate_team(task, teams, {})
    assert result["team_assigned"] == "TEAM-RESERVE"
    assert "reserve" in result["resource_status"].lower()


def test_falls_back_to_cross_section_team():
    task = {"required_team": "TEAM-A", "section_id": "S-01"}
    teams = [
        {"team_id": "TEAM-A", "section_id": "S-01", "is_reserve": False, "status": "busy", "qualified_sections": ["S-01"]},
        {"team_id": "TEAM-B", "section_id": "S-02", "is_reserve": False, "status": "available", "qualified_sections": ["S-01", "S-02"]},
    ]
    result = allocate_team(task, teams, {})
    assert result["team_assigned"] == "TEAM-B"
    assert "cross-section" in result["resource_status"].lower()


def test_non_preemptible_work_is_never_interrupted():
    task = {"required_team": "TEAM-A", "section_id": "S-01"}
    teams = [{"team_id": "TEAM-A", "section_id": "S-01", "is_reserve": False, "status": "busy", "qualified_sections": ["S-01"]}]
    active = {"TEAM-A": {"task_id": "T-999", "is_emergency": True}}
    result = allocate_team(task, teams, active)
    assert result["preemption_status"] == "Non-Preemptible"
    assert result["team_assigned"] is None
    assert result["escalated"] is True


def test_preemptible_work_allows_reassignment():
    task = {"required_team": "TEAM-A", "section_id": "S-01"}
    teams = [{"team_id": "TEAM-A", "section_id": "S-01", "is_reserve": False, "status": "busy", "qualified_sections": ["S-01"]}]
    active = {"TEAM-A": {"task_id": "T-998", "is_emergency": False, "fault_category": "Preventive Inspection"}}
    result = allocate_team(task, teams, active)
    assert result["preemption_status"] == "Preemptible"
    assert result["team_assigned"] == "TEAM-A"
    assert result["escalated"] is False
