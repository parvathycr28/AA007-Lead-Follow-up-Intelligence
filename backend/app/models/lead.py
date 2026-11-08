from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EngagementEvent(BaseModel):
    event_id: str
    event_type: str
    occurred_at: datetime


class LeadRecord(BaseModel):
    lead_id: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)

    created_at: datetime
    last_contact_at: Optional[datetime] = None

    declared_need: Optional[str] = None
    stage: str = Field(..., min_length=1)

    contact_available: bool = True

    pending_follow_up: bool = False
    follow_up_due_at: Optional[datetime] = None