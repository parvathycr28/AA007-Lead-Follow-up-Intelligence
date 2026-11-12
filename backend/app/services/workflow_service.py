
from typing import List

from app.models.lead import EngagementEvent, LeadRecord
from app.models.workflow import WorkflowContext
from app.services.workflow_graph import build_workflow_graph


class WorkflowService:

    @staticmethod
    def execute(
        lead_record: LeadRecord,
        engagement_events: List[EngagementEvent] | None = None,
    ) -> WorkflowContext:

        workflow = build_workflow_graph()

        result = workflow.invoke({
            "lead_record": lead_record,
            "engagement_events": engagement_events or [],
        })

        return result["context"]