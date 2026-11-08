from typing import List

from app.models.lead import EngagementEvent, LeadRecord
from app.models.workflow import WorkflowContext


class ContextBuilder:

    @staticmethod
    def build(
        lead_record: LeadRecord,
        engagement_events: List[EngagementEvent] | None = None,
    ) -> WorkflowContext:

        normalized_lead = lead_record.model_copy(
            update={
                "source": lead_record.source.strip(),
                "stage": lead_record.stage.strip(),
            }
        )

        context = WorkflowContext(
            lead_record=normalized_lead,
            engagement_events=engagement_events or [],
        )

        context.validated_lead = normalized_lead.model_dump(
            mode="json"
        )

        return context