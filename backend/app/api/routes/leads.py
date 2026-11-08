from fastapi import APIRouter, HTTPException

from app.models.api import (
    PrioritizationRequest,
    PrioritizationResponse,
)

from app.services.workflow_service import WorkflowService
from app.data.seed_leads import get_seed_scenarios

router = APIRouter(
    prefix="/api/leads",
    tags=["Lead Prioritization"],
)


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
            workflow_id=context.workflow_id,
            lead_id=context.lead_record.lead_id,
            recommendation=context.final_recommendation or {},
            explanation=context.explanation,
            audit_reference=context.audit_reference,
            errors=context.errors,
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

    return {
        "workflow_id": context.workflow_id,
        "scenario": scenario_name,
        "lead_id": context.lead_record.lead_id,
        "recommendation": context.final_recommendation,
        "explanation": context.explanation,
        "audit_reference": context.audit_reference,
        "errors": context.errors,
    }