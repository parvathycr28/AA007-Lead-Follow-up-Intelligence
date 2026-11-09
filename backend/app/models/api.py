from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.lead import LeadRecord, EngagementEvent


class PrioritizationRequest(BaseModel):
    lead: LeadRecord
    engagement_events: List[EngagementEvent] = Field(
        default_factory=list
    )


class PrioritizationResponse(BaseModel):
    workflow_id: str
    lead_id: str

    recommendation: Dict[str, Any]

    explanation: Optional[Dict[str, Any]] = None

    audit_reference: Optional[str] = None

    workflow_context: Dict[str, Any] = Field(
        default_factory=dict
    )

    audit_record: Optional[Dict[str, Any]] = None

    errors: List[str] = Field(
        default_factory=list
    )
