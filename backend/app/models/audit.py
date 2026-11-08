from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class AuditRecord(BaseModel):
    audit_reference: str
    workflow_id: str
    timestamp: datetime
    lead_id: str

    agent_sequence: List[str] = Field(
        default_factory=list
    )

    agent_outputs: Dict[str, Any] = Field(
        default_factory=dict
    )

    triggered_rules: List[str] = Field(
        default_factory=list
    )

    final_recommendation: Dict[str, Any] = Field(
        default_factory=dict
    )

    errors: List[str] = Field(
        default_factory=list
    )