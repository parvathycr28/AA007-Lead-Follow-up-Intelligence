from datetime import datetime, timezone
from uuid import uuid4

from app.models.audit import AuditRecord
from app.models.workflow import WorkflowContext


class AuditService:

    # In-memory audit storage for the MVP.
    audit_store: dict[str, AuditRecord] = {}

    @classmethod
    def record(cls, context: WorkflowContext) -> AuditRecord:

        recommendation = context.final_recommendation or {}

        triggered_rules = recommendation.get(
            "triggered_rules",
            [],
        )

        audit_reference = f"AUD-{uuid4().hex[:12].upper()}"

        record = AuditRecord(
            audit_reference=audit_reference,
            workflow_id=context.workflow_id,
            timestamp=datetime.now(timezone.utc),
            lead_id=context.lead_record.lead_id,
            agent_sequence=list(context.agent_outputs.keys()),
            agent_outputs=context.agent_outputs.copy(),
            triggered_rules=triggered_rules,
            final_recommendation=recommendation.copy(),
            errors=list(context.errors),
        )

        cls.audit_store[audit_reference] = record

        context.audit_reference = audit_reference

        return record

    @classmethod
    def get(cls, audit_reference: str) -> AuditRecord | None:
        return cls.audit_store.get(audit_reference)