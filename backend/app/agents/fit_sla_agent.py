from datetime import datetime, timezone

from app.models.agent_outputs import FitSLAOutput
from app.models.workflow import WorkflowContext


class FitSLAAgent:

    @staticmethod
    def run(context: WorkflowContext) -> FitSLAOutput:
        lead = context.lead_record

        # Provisional MVP fit-scoring assumption.
        if lead.declared_need and lead.declared_need.strip():
            fit_score = 30
            fit_reason = "A declared business need is available."
        else:
            fit_score = 0
            fit_reason = "No declared business need is available."

        sla_flags = []

        if lead.pending_follow_up:
            if lead.follow_up_due_at is None:
                sla_flags.append("FOLLOW_UP_DUE_DATE_MISSING")
            else:
                due_at = lead.follow_up_due_at

                if due_at.tzinfo is None:
                    due_at = due_at.replace(tzinfo=timezone.utc)

                now = datetime.now(timezone.utc)

                if due_at < now:
                    sla_flags.append("FOLLOW_UP_OVERDUE")

        result = FitSLAOutput(
            fit_score=fit_score,
            sla_flags=sla_flags,
            reason=fit_reason,
        )

        context.fit_score = result.fit_score
        context.sla_flags = result.sla_flags
        context.agent_outputs["fit_sla"] = result.model_dump()

        return result