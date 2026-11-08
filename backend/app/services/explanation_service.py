from app.models.workflow import WorkflowContext


class ExplanationService:

    @staticmethod
    def build(context: WorkflowContext) -> dict:

        agent_names = {
            "lead_intake": "Lead Intake Agent",
            "recency": "Recency Agent",
            "engagement": "Engagement Agent",
            "fit_sla": "Fit & SLA Agent",
            "lead_priority": "Lead Priority Decision Agent",
        }

        executed_agents = [
            agent_names[key]
            for key in context.agent_outputs
            if key in agent_names
        ]

        recommendation = context.final_recommendation or {}

        action = recommendation.get(
            "action",
            "NOT_AVAILABLE",
        )

        score = recommendation.get(
            "priority_score",
            0,
        )

        triggered_rules = recommendation.get(
            "triggered_rules",
            [],
        )

        reasons = recommendation.get(
            "reasons",
            [],
        )

        explanation = {
            "summary": (
                f"Lead {context.lead_record.lead_id} "
                f"received the recommendation {action} "
                f"with a priority score of {score}/100."
            ),
            "executed_agents": executed_agents,
            "score_breakdown": {
                "recency": context.recency_score,
                "engagement": context.engagement_score,
                "fit": context.fit_score,
            },
            "triggered_rules": triggered_rules,
            "reasons": reasons,
            "limitations": list(context.errors),
        }

        context.explanation = explanation

        return explanation