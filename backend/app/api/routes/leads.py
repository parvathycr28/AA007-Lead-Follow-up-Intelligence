from fastapi import APIRouter, HTTPException

from app.models.api import (
    PrioritizationRequest,
    PrioritizationResponse,
)

from app.services.workflow_service import WorkflowService
from app.services.audit_service import AuditService
from app.data.seed_leads import get_seed_scenarios

router = APIRouter(
    prefix="/api/leads",
    tags=["Lead Prioritization"],
)


def build_workflow_response(context, scenario=None):
    audit_record = None

    if context.audit_reference:
        record = AuditService.get(context.audit_reference)

        if record:
            audit_record = record.model_dump(mode="json")

    response = {
        "workflow_id": context.workflow_id,
        "lead_id": context.lead_record.lead_id,
        "recommendation": context.final_recommendation or {},
        "explanation": context.explanation,
        "audit_reference": context.audit_reference,
        "workflow_context": context.model_dump(mode="json"),
        "audit_record": audit_record,
        "errors": context.errors,
    }

    if scenario is not None:
        response["scenario"] = scenario

    return response


@router.post(
    "/prioritize",
    response_model=PrioritizationResponse,
)
def prioritize_lead(
    request: PrioritizationRequest,
):
    try:
        context = WorkflowService.execute(
            lead_record=request.lead,
            engagement_events=request.engagement_events,
        )

        return PrioritizationResponse(
            **build_workflow_response(context)
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Lead prioritization failed: {str(exc)}",
        )


@router.get("/scenarios")
def list_scenarios():
    scenarios = get_seed_scenarios()

    return {
        name: {
            "description": data["description"],
            "lead_id": data["lead"].lead_id,
        }
        for name, data in scenarios.items()
    }


@router.post("/scenarios/{scenario_name}/run")
def run_scenario(scenario_name: str):
    scenarios = get_seed_scenarios()

    if scenario_name not in scenarios:
        raise HTTPException(
            status_code=404,
            detail="Scenario not found.",
        )

    scenario = scenarios[scenario_name]

    context = WorkflowService.execute(
        lead_record=scenario["lead"],
        engagement_events=scenario["engagement_events"],
    )

    return build_workflow_response(
        context,
        scenario=scenario_name,
    )
