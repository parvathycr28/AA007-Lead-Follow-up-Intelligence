
from typing import List, TypedDict

from app.models.lead import EngagementEvent, LeadRecord
from app.models.workflow import WorkflowContext


class WorkflowState(TypedDict, total=False):
    """
    Shared state passed between LangGraph workflow nodes.
    """

    lead_record: LeadRecord
    engagement_events: List[EngagementEvent]

    context: WorkflowContext

    intake_valid: bool
    execution_failed: bool