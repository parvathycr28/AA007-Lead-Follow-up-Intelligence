from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from app.models.lead import EngagementEvent, LeadRecord


class WorkflowContext(BaseModel):
    workflow_id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    lead_record: LeadRecord
    engagement_events: List[EngagementEvent] = Field(
        default_factory=list
    )

    validated_lead: Optional[Dict[str, Any]] = None

    recency_score: Optional[float] = None
    engagement_score: Optional[float] = None
    fit_score: Optional[float] = None

    sla_flags: List[str] = Field(default_factory=list)

    agent_outputs: Dict[str, Any] = Field(
        default_factory=dict
    )

    final_recommendation: Optional[Dict[str, Any]] = None
    explanation: Optional[Dict[str, Any]] = None
    audit_reference: Optional[str] = None

    errors: List[str] = Field(default_factory=list)