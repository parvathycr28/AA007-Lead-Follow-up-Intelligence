from app.models.agent_outputs import LeadIntakeOutput
from app.models.workflow import WorkflowContext


class LeadIntakeAgent:

    @staticmethod
    def run(context: WorkflowContext) -> LeadIntakeOutput:
        lead = context.lead_record
        errors = []

        if not lead.lead_id.strip():
            errors.append("Lead ID is missing.")

        if not lead.source.strip():
            errors.append("Lead source is missing.")

        if not lead.stage.strip():
            errors.append("Lead stage is missing.")

        if not lead.contact_available:
            errors.append("Mandatory contact information is unavailable.")

        if errors:
            result = LeadIntakeOutput(
                status="invalid",
                validated_lead=None,
                errors=errors,
            )
        else:
            validated_lead = lead.model_dump(mode="json")

            result = LeadIntakeOutput(
                status="valid",
                validated_lead=validated_lead,
                errors=[],
            )

            context.validated_lead = validated_lead

        context.agent_outputs["lead_intake"] = result.model_dump()

        if errors:
            context.errors.extend(errors)

        return result