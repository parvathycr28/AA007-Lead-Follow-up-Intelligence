
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.data.seed_leads import get_seed_scenarios
from app.services.workflow_service import WorkflowService
from app.services.audit_service import AuditService
from app.models.lead import LeadRecord


client = TestClient(app)


@pytest.mark.parametrize(
    "scenario_name, expected_action, expected_score, expected_route, expected_condition",
    [
        (
            "hot",
            "FOLLOW_UP_NOW",
            95,
            "overdue_follow_up",
            "OVERDUE_FOLLOW_UP",
        ),
        (
            "warm",
            "FOLLOW_UP_SOON",
            65,
            "follow_up_soon",
            "MODERATE_PRIORITY_SCORE",
        ),
        (
            "stale",
            "NURTURE",
            0,
            "nurture",
            "LOW_PRIORITY_SCORE",
        ),
    ],
)
def test_seed_scenario_workflow(
    scenario_name,
    expected_action,
    expected_score,
    expected_route,
    expected_condition,
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
    audit_record = AuditService.get(context.audit_reference)
    assert audit_record is not None
    assert audit_record.execution_trace == context.execution_trace

    assert any(
        item["node"] == "intake_router"
        and item.get("route") == "recency"
        and item.get("condition") == "INTAKE_VALID"
        for item in audit_record.execution_trace
    )

    assert any(
        item["node"] == "priority_router"
        and item.get("route") == expected_route
        and item.get("condition") == expected_condition
        for item in audit_record.execution_trace
    )

    assert audit_record.execution_trace[-1] == {
        "node": "explanation_audit",
        "status": "completed",
    }

    assert context.errors == []

    actual_nodes = [
        item["node"]
        for item in context.execution_trace
    ]

    assert actual_nodes == [
        "build_context",
        "lead_intake",
        "intake_router",
        "recency",
        "engagement",
        "fit_sla",
        "priority_decision",
        "priority_router",
        expected_route,
        "explanation_audit",
    ]

    intake_route = next(
        item
        for item in context.execution_trace
        if item["node"] == "intake_router"
    )

    assert intake_route["route"] == "recency"
    assert intake_route["condition"] == "INTAKE_VALID"

    priority_route = next(
        item
        for item in context.execution_trace
        if item["node"] == "priority_router"
    )

    assert priority_route["route"] == expected_route
    assert priority_route["condition"] == expected_condition

    assert all(
        item["status"] in ("completed", "selected")
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

    actual_trace = context.execution_trace

    assert [
        (item["node"], item["status"])
        for item in actual_trace
    ] == [
        ("build_context", "completed"),
        ("lead_intake", "completed"),
        ("intake_router", "selected"),
        ("request_data", "completed"),
        ("explanation_audit", "completed"),
    ]

    intake_route = next(
        item
        for item in actual_trace
        if item["node"] == "intake_router"
    )

    assert intake_route["route"] == "request_data"
    assert intake_route["condition"] == "MISSING_MANDATORY_DATA"

    assert list(context.agent_outputs.keys()) == ["lead_intake"]

def test_high_priority_score_uses_high_priority_route():
    from datetime import datetime, timezone, timedelta

    from app.models.lead import EngagementEvent

    now = datetime.now(timezone.utc)

    lead = LeadRecord(
        lead_id="LEAD-TEST-HIGH",
        source="Website",
        created_at=now - timedelta(days=2),
        last_contact_at=now - timedelta(days=1),
        declared_need="Enterprise software",
        stage="Qualified",
        contact_available=True,
        pending_follow_up=False,
    )

    events = [
        EngagementEvent(
            event_id=f"HIGH-E{i}",
            event_type=event_type,
            occurred_at=now - timedelta(hours=i),
        )
        for i, event_type in enumerate(
            [
                "inquiry",
                "email_response",
                "meeting_attended",
                "follow_up_response",
            ],
            start=1,
        )
    ]

    context = WorkflowService.execute(lead, events)

    assert context.final_recommendation["action"] == "FOLLOW_UP_NOW"
    assert context.final_recommendation["priority_score"] == 100
    assert context.final_recommendation["triggered_rules"] == [
        "HIGH_PRIORITY_SCORE"
    ]

    priority_route = next(
        item
        for item in context.execution_trace
        if item["node"] == "priority_router"
    )

    assert priority_route["route"] == "high_priority"
    assert priority_route["condition"] == "HIGH_PRIORITY_SCORE"

    assert any(
        item["node"] == "high_priority"
        and item["status"] == "completed"
        for item in context.execution_trace
    )

    assert context.explanation is not None
    assert context.audit_reference is not None
    assert context.errors == []