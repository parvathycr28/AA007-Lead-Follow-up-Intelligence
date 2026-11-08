from app.models.agent_outputs import LeadPriorityOutput
from app.models.workflow import WorkflowContext


class LeadPriorityAgent:

    @staticmethod
    def run(context: WorkflowContext) -> LeadPriorityOutput:

        recency = context.recency_score or 0
        engagement = context.engagement_score or 0
        fit = context.fit_score or 0

        priority_score = min(
            recency + engagement + fit,
            100,
        )

        triggered_rules = []
        reasons = []

        # Rule 1: Missing mandatory contact information.
        intake_output = context.agent_outputs.get(
            "lead_intake", {}
        )

        if intake_output.get("status") == "invalid":
            action = "REQUEST_DATA"
            triggered_rules.append("MISSING_MANDATORY_DATA")
            reasons.append(
                "Mandatory lead information is missing or invalid."
            )

        # Rule 2: Overdue committed follow-up.
        elif "FOLLOW_UP_OVERDUE" in context.sla_flags:
            action = "FOLLOW_UP_NOW"
            triggered_rules.append("OVERDUE_FOLLOW_UP")
            reasons.append(
                "A committed follow-up is overdue."
            )

        # Rule 3: High priority score.
        elif priority_score >= 70:
            action = "FOLLOW_UP_NOW"
            triggered_rules.append("HIGH_PRIORITY_SCORE")
            reasons.append(
                "The lead has a high combined priority score."
            )

        # Rule 4: Moderate priority score.
        elif priority_score >= 40:
            action = "FOLLOW_UP_SOON"
            triggered_rules.append("MODERATE_PRIORITY_SCORE")
            reasons.append(
                "The lead has a moderate combined priority score."
            )

        # Rule 5: Low priority score.
        else:
            action = "NURTURE"
            triggered_rules.append("LOW_PRIORITY_SCORE")
            reasons.append(
                "The lead has a low combined priority score."
            )

        result = LeadPriorityOutput(
            priority_score=priority_score,
            action=action,
            triggered_rules=triggered_rules,
            reasons=reasons,
        )

        context.final_recommendation = result.model_dump()
        context.agent_outputs["lead_priority"] = (
            result.model_dump()
        )

        return result