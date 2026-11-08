from typing import List

from app.models.lead import EngagementEvent, LeadRecord
from app.models.workflow import WorkflowContext

from app.services.context_builder import ContextBuilder
from app.services.explanation_service import ExplanationService
from app.services.audit_service import AuditService

from app.agents.lead_intake_agent import LeadIntakeAgent
from app.agents.recency_agent import RecencyAgent
from app.agents.engagement_agent import EngagementAgent
from app.agents.fit_sla_agent import FitSLAAgent
from app.agents.lead_priority_agent import LeadPriorityAgent


class WorkflowService:

    @staticmethod
    def execute(
        lead_record: LeadRecord,
        engagement_events: List[EngagementEvent] | None = None,
    ) -> WorkflowContext:

        # Step 1: Build shared workflow context.
        context = ContextBuilder.build(
            lead_record,
            engagement_events,
        )

        try:
            # Step 2: Validate lead input.
            intake_result = LeadIntakeAgent.run(context)

            if intake_result.status == "invalid":
                context.final_recommendation = {
                    "action": "REQUEST_DATA",
                    "priority_score": 0,
                    "triggered_rules": [
                        "MISSING_MANDATORY_DATA"
                    ],
                    "reasons": intake_result.errors,
                }

            else:
                # Step 3: Execute analytical agents.
                RecencyAgent.run(context)
                EngagementAgent.run(context)
                FitSLAAgent.run(context)

                # Step 4: Generate final recommendation.
                LeadPriorityAgent.run(context)

        except Exception as exc:
            context.errors.append(str(exc))

        # Step 5: Generate explanation.
        ExplanationService.build(context)

        # Step 6: Generate audit record.
        AuditService.record(context)

        return context