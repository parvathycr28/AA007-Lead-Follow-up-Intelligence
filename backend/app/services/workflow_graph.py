
from langgraph.graph import END, START, StateGraph

from app.models.workflow import WorkflowContext
from app.services.workflow_state import WorkflowState

from app.services.context_builder import ContextBuilder
from app.services.explanation_service import ExplanationService
from app.services.audit_service import AuditService

from app.agents.lead_intake_agent import LeadIntakeAgent
from app.agents.recency_agent import RecencyAgent
from app.agents.engagement_agent import EngagementAgent
from app.agents.fit_sla_agent import FitSLAAgent
from app.agents.lead_priority_agent import LeadPriorityAgent


def add_trace(
    context: WorkflowContext,
    node: str,
    status: str,
) -> None:
    context.execution_trace.append({
        "node": node,
        "status": status,
    })


def build_context_node(state: WorkflowState) -> dict:
    context = ContextBuilder.build(
        state["lead_record"],
        state.get("engagement_events", []),
    )

    add_trace(context, "build_context", "completed")

    return {"context": context}


def lead_intake_node(state: WorkflowState) -> dict:
    context = state["context"]

    try:
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

            add_trace(context, "lead_intake", "completed")

            return {
                "context": context,
                "intake_valid": False,
                "execution_failed": False,
            }

        add_trace(context, "lead_intake", "completed")

        return {
            "context": context,
            "intake_valid": True,
            "execution_failed": False,
        }

    except Exception as exc:
        context.errors.append(str(exc))
        add_trace(context, "lead_intake", "failed")

        return {
            "context": context,
            "intake_valid": False,
            "execution_failed": True,
        }


def run_agent_node(
    state: WorkflowState,
    node_name: str,
    agent,
) -> dict:
    context = state["context"]

    if not state.get("intake_valid", False):
        add_trace(context, node_name, "skipped")
        return {"context": context}

    if state.get("execution_failed", False):
        add_trace(context, node_name, "skipped")
        return {"context": context}

    try:
        agent.run(context)
        add_trace(context, node_name, "completed")

        return {"context": context}

    except Exception as exc:
        context.errors.append(str(exc))
        add_trace(context, node_name, "failed")

        return {
            "context": context,
            "execution_failed": True,
        }


def recency_node(state: WorkflowState) -> dict:
    return run_agent_node(
        state,
        "recency",
        RecencyAgent,
    )


def engagement_node(state: WorkflowState) -> dict:
    return run_agent_node(
        state,
        "engagement",
        EngagementAgent,
    )


def fit_sla_node(state: WorkflowState) -> dict:
    return run_agent_node(
        state,
        "fit_sla",
        FitSLAAgent,
    )


def priority_decision_node(state: WorkflowState) -> dict:
    return run_agent_node(
        state,
        "priority_decision",
        LeadPriorityAgent,
    )


def explanation_audit_node(state: WorkflowState) -> dict:
    context = state["context"]

    ExplanationService.build(context)
    AuditService.record(context)

    add_trace(context, "explanation_audit", "completed")

    return {"context": context}


def build_workflow_graph():
    graph = StateGraph(WorkflowState)

    graph.add_node("build_context", build_context_node)
    graph.add_node("lead_intake", lead_intake_node)
    graph.add_node("recency", recency_node)
    graph.add_node("engagement", engagement_node)
    graph.add_node("fit_sla", fit_sla_node)
    graph.add_node("priority_decision", priority_decision_node)
    graph.add_node("explanation_audit", explanation_audit_node)

    graph.add_edge(START, "build_context")
    graph.add_edge("build_context", "lead_intake")
    graph.add_edge("lead_intake", "recency")
    graph.add_edge("recency", "engagement")
    graph.add_edge("engagement", "fit_sla")
    graph.add_edge("fit_sla", "priority_decision")
    graph.add_edge("priority_decision", "explanation_audit")
    graph.add_edge("explanation_audit", END)

    return graph.compile()