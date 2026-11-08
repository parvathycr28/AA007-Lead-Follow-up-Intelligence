from datetime import datetime, timezone
from typing import Optional

from app.models.agent_outputs import RecencyOutput
from app.models.workflow import WorkflowContext


class RecencyAgent:

    @staticmethod
    def run(context: WorkflowContext) -> RecencyOutput:
        last_contact = context.lead_record.last_contact_at

        if last_contact is None:
            result = RecencyOutput(
                score=0,
                days_since_last_contact=None,
                reason="No previous contact date is available.",
            )
        else:
            now = datetime.now(timezone.utc)

            if last_contact.tzinfo is None:
                last_contact = last_contact.replace(
                    tzinfo=timezone.utc
                )

            days = max(
                0,
                (now - last_contact).days,
            )

            # Provisional scoring assumptions for the MVP.
            if days <= 7:
                score = 30
            elif days <= 30:
                score = 20
            elif days <= 60:
                score = 10
            else:
                score = 0

            result = RecencyOutput(
                score=score,
                days_since_last_contact=days,
                reason=f"Last contact was {days} days ago.",
            )

        context.recency_score = result.score
        context.agent_outputs["recency"] = result.model_dump()

        return result