import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.data.seed_leads import get_seed_scenarios
from app.services.workflow_service import WorkflowService
from app.services.audit_service import AuditService
from app.models.lead import LeadRecord


client = TestClient(app)


@pytest.mark.parametrize(
    "scenario_name, expected_action, expected_score",
    [
        ("hot", "FOLLOW_UP_NOW", 95),
        ("warm", "FOLLOW_UP_SOON", 65),
        ("stale", "NURTURE", 0),
    ],
)
def test_seed_scenario_workflow(
    scenario_name,
    expected_action,
    expected_score,
):
    scenarios = get_seed_scenarios()
    scenario = scenarios[scenario_name]

    context = WorkflowService.execute(
        scenario["lead"],
        scenario["engagement_events"],
    )

    assert context.final_recommendation["action"] == expected_action
    assert context.final_recommendation["priority_score"] == expected_score

    assert len(context.agent_outputs) == 5
    assert context.explanation is not None
    assert context.audit_reference is not None
    assert AuditService.get(context.audit_reference) is not None
    assert context.errors == []
    expected_nodes = [
        "build_context",
        "lead_intake",
        "recency",
        "engagement",
        "fit_sla",
        "priority_decision",
        "explanation_audit",
    ]

    assert [item["node"] for item in context.execution_trace] == expected_nodes
    assert all(
        item["status"] == "completed"
        for item in context.execution_trace
    )

def test_scenario_listing_api():
    response = client.get("/api/leads/scenarios")

    assert response.status_code == 200

    data = response.json()

    assert set(data.keys()) == {"hot", "warm", "stale"}


@pytest.mark.parametrize(
    "scenario_name, expected_action",
    [
        ("hot", "FOLLOW_UP_NOW"),
        ("warm", "FOLLOW_UP_SOON"),
        ("stale", "NURTURE"),
    ],
)
def test_scenario_execution_api(scenario_name, expected_action):
    response = client.post(
        f"/api/leads/scenarios/{scenario_name}/run"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["recommendation"]["action"] == expected_action
    assert data["explanation"] is not None
    assert data["audit_reference"] is not None
    assert data["errors"] == []


def test_unknown_scenario_returns_404():
    response = client.post(
        "/api/leads/scenarios/unknown/run"
    )

    assert response.status_code == 404


def test_missing_contact_returns_request_data():
    lead = LeadRecord(
        lead_id="LEAD-TEST-INVALID",
        source="Website",
        created_at="2026-11-08T10:00:00Z",
        stage="New",
        contact_available=False,
    )

    context = WorkflowService.execute(lead)

    assert context.final_recommendation["action"] == "REQUEST_DATA"
    assert context.explanation is not None
    assert context.audit_reference is not None
    assert context.errors
    expected_trace = [
        ("build_context", "completed"),
        ("lead_intake", "completed"),
        ("recency", "skipped"),
        ("engagement", "skipped"),
        ("fit_sla", "skipped"),
        ("priority_decision", "skipped"),
        ("explanation_audit", "completed"),
    ]

    actual_trace = [
        (item["node"], item["status"])
        for item in context.execution_trace
    ]

    assert actual_trace == expected_trace
    assert list(context.agent_outputs.keys()) == ["lead_intake"]