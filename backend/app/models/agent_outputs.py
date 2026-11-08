from typing import List, Optional

from pydantic import BaseModel, Field


class LeadIntakeOutput(BaseModel):
    agent_name: str = "Lead Intake Agent"
    status: str
    validated_lead: Optional[dict] = None
    errors: List[str] = Field(default_factory=list)


class RecencyOutput(BaseModel):
    agent_name: str = "Recency Agent"
    score: float
    days_since_last_contact: Optional[int] = None
    reason: str


class EngagementOutput(BaseModel):
    agent_name: str = "Engagement Agent"
    score: float
    event_count: int
    recognized_events: List[str] = Field(default_factory=list)
    reason: str


class FitSLAOutput(BaseModel):
    agent_name: str = "Fit & SLA Agent"
    fit_score: float
    sla_flags: List[str] = Field(default_factory=list)
    reason: str


class LeadPriorityOutput(BaseModel):
    agent_name: str = "Lead Priority Decision Agent"
    priority_score: float
    action: str
    triggered_rules: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)