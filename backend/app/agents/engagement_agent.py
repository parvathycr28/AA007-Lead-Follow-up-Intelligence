from app.models.agent_outputs import EngagementOutput
from app.models.workflow import WorkflowContext


class EngagementAgent:

    # Provisional MVP weights, not prescribed Product Bible values.
    EVENT_WEIGHTS = {
        "inquiry": 15,
        "email_response": 10,
        "meeting_attended": 20,
        "follow_up_response": 10,
    }

    @classmethod
    def run(cls, context: WorkflowContext) -> EngagementOutput:
        total_score = 0
        recognized_events = []

        for event in context.engagement_events:
            event_type = event.event_type.strip().lower()

            if event_type in cls.EVENT_WEIGHTS:
                total_score += cls.EVENT_WEIGHTS[event_type]
                recognized_events.append(event_type)

        result = EngagementOutput(
            score=min(total_score, 40),
            event_count=len(recognized_events),
            recognized_events=recognized_events,
            reason=(
                f"{len(recognized_events)} recognized engagement "
                f"events contributed to the score."
            ),
        )

        context.engagement_score = result.score
        context.agent_outputs["engagement"] = result.model_dump()

        return result