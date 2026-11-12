# Lead Follow-up Prioritization Intelligence

**Product:** APEX — Lead Intelligence Platform
**Case ID:** AA007
**Architecture Version:** 2.1

## 1. Architecture Overview

APEX follows a deterministic multi-agent workflow architecture orchestrated using LangGraph.

A lead record enters through the FastAPI endpoint. The LangGraph StateGraph executes a linear sequence of workflow nodes, beginning with the Context Builder and followed by the Lead Intake Agent, Recency Agent, Engagement Agent, Fit & SLA Agent, Lead Priority Decision Agent, and Explanation & Audit stage.

The Context Builder creates a run-scoped shared workflow context. The Lead Intake Agent validates the lead information before the analytical agents execute.

For valid leads, all five agents execute in sequence. For invalid leads with missing mandatory information, the analytical agent nodes are skipped while the workflow continues to explanation and audit generation.

LangGraph manages the orchestration and shared workflow state. It does not make business decisions. The existing agents, deterministic scoring rules, recommendation logic, explanations, and audit behaviour remain unchanged.

The workflow also records an execution trace containing the node name and execution status. This makes the orchestration sequence inspectable.

The frontend exposes business inputs, workflow context, agent execution information, decision evidence, final recommendations, explanations, and audit references.

## 2. High-Level Workflow

The FastAPI endpoint invokes the LangGraph workflow. The compiled StateGraph executes the following nodes in a fixed linear sequence:

```text
User / Frontend
       |
       v
FastAPI Endpoint
       |
       v
LangGraph StateGraph
       |
       v
  build_context
       |
       v
   lead_intake
       |
       v
     recency
       |
       v
   engagement
       |
       v
     fit_sla
       |
       v
priority_decision
       |
       v
explanation_audit
       |
       v
      END
       |
       v
  API Response
       |
       v
    Frontend
```

### Workflow Execution Behaviour

- **Valid lead:** All seven workflow nodes execute in sequence, and all five agents produce their outputs.
- **Invalid lead:** The Context Builder and Lead Intake nodes execute. The four downstream analytical agent nodes are marked as skipped. The workflow still proceeds to explanation and audit generation.
- **Execution trace:** Each node records its name and status (`completed`, `skipped`, or `failed`) in the shared workflow context.

The graph uses fixed edges between nodes. Conditional routing and dynamic agent selection are not part of the current Phase 2.1 implementation.

## 3. Agent Responsibilities

### 3.1 Lead Intake Agent

- Validates mandatory lead information.
- Normalizes lead fields.
- Identifies missing or invalid information.
- Produces validated lead data.

### 3.2 Recency Agent

- Evaluates the lead's age and last-contact date.
- Applies the configured recency scoring bands.
- Produces the recency score and supporting evidence.

### 3.3 Engagement Agent

- Evaluates approved business engagement events.
- Applies configured event weights.
- Produces the engagement score and supporting evidence.

### 3.4 Fit & SLA Agent

- Evaluates declared business need.
- Checks pending follow-up commitments.
- Identifies overdue follow-up conditions.
- Produces fit and SLA outputs.

### 3.5 Lead Priority Decision Agent

- Combines the outputs from the preceding agents.
- Applies deterministic decision precedence.
- Produces the final action, priority score, reasons, and triggered rules.

## 4. Workflow Context

Each workflow execution uses its own shared workflow context to carry information between LangGraph nodes and agents.

The context includes:

- Workflow identifier.
- Original lead record and normalized lead snapshot.
- Lead Intake validation outcome and validated lead information, when valid.
- Recency score.
- Engagement score.
- Fit score and SLA flags.
- Individual agent outputs.
- Final recommendation.
- Explanation.
- Audit reference.
- Errors.
- Execution trace containing workflow node names and execution statuses.

The LangGraph StateGraph uses a shared workflow state to pass the lead record, engagement events, and workflow context between nodes.

The execution trace records the sequence in which nodes execute. Each entry contains a node name and a status, such as `completed`, `skipped`, or `failed`.

This structure keeps workflow state organized, supports execution inspection, and makes individual workflow runs easier to validate.

## 5. Decision and Scoring Layer

The decision layer uses configured scoring weights and deterministic rules.

The provisional scoring model allocates:

| Component | Maximum points |
|---|---:|
| Recency | 30 |
| Engagement | 40 |
| Declared need / fit | 30 |
| Total | 100 |

Overdue follow-up commitments take precedence over ordinary score thresholds.

Missing mandatory information results in `REQUEST_DATA`.

The scoring configuration is an MVP implementation assumption and can be refined using approved business requirements and validated operational data.

## 6. Explanation Service

The Explanation Service generates a structured explanation from the workflow context.

It communicates:

- Which agents executed.
- The final recommendation.
- The supporting reasons.
- Relevant evidence.
- Known limitations.

The explanation is based on deterministic workflow outputs rather than an external language model.

## 7. Audit Service

The Audit Service records information about workflow executions, including:

- Workflow ID.
- Audit reference.
- Execution timestamp.
- Agent execution sequence.
- Agent outputs.
- Triggered business rules.
- Final recommendation.
- Errors, where applicable.

Audit records are stored in process-local memory in the current MVP. Persistent audit storage is outside the current implementation scope.

## 8. API and Frontend Integration

The FastAPI backend exposes endpoints for health checks, lead prioritization, scenario listing, and scenario execution.

The React and TypeScript frontend communicates with the backend through the Vite development proxy during local development.

In the production deployment, the frontend uses Nginx to forward requests under `/api/` to the configured backend service. The browser communicates with the frontend origin, while Nginx handles backend routing.

The dashboard presents scenario selection, recommendations, priority scores, agent execution information, explanations, and audit details.

## 9. Docker Deployment Architecture

The application is containerized using Docker Compose while preserving the existing backend and frontend responsibilities.

### Backend Container

- Built from `backend/Dockerfile`.
- Uses Python 3.11 with FastAPI and Uvicorn.
- Listens on port `8002` inside the container.
- Exposes the existing backend health endpoint at `/api/assistant/health`.

### Frontend Container

- Built from `frontend/Dockerfile` using a multi-stage build.
- Uses Node.js to generate the React production build.
- Uses Nginx to serve the static frontend files.
- Publishes container port `80` on host port `8080`.

### Container Communication

- Docker Compose creates an internal network for the services.
- Nginx forwards `/api/` requests to `http://backend:8002`.
- The backend port is available to the frontend through the internal Docker network.
- The frontend waits for the backend health check before starting.

### Health Checks

- Backend health is checked through `/api/assistant/health`.
- Frontend health is checked through `/health`.
- Docker Compose reports container health status.

### Runtime and Persistence Limitation

The audit service continues to use process-local in-memory storage. Audit records are not persisted across backend container restarts. No database or persistent audit volume is introduced in this phase.

Dockerization changes the local deployment and serving arrangement; it does not change the deterministic business workflow or agent responsibilities.

## 10. Cloud Deployment Architecture — Render (Phase 1.4)

The application is deployed on Render using two independent Docker-based Web Services. This deployment preserves the existing multi-agent workflow and separates frontend presentation from backend execution.

### Frontend Web Service

- **Service:** `aa007-frontend`
- **Public URL:** https://aa007-frontend.onrender.com
- Built using `frontend/Dockerfile`.
- Serves the React production build through Nginx on container port `80`.
- Uses the `BACKEND_URL` environment variable to identify the backend service.

### Backend Web Service

- **Service:** `aa007-backend`
- **Public URL:** https://aa007-backend.onrender.com
- **Health endpoint:** `/api/assistant/health`
- Built using `backend/Dockerfile`.
- Runs FastAPI through Uvicorn on container port `8002`.

### Cloud Request Flow

1. The user opens the public frontend URL.
2. Nginx serves the React application.
3. The frontend makes same-origin requests under `/api/`.
4. Nginx forwards those requests to the backend URL configured through `BACKEND_URL`.
5. FastAPI executes the existing deterministic workflow and returns the response.
6. The frontend displays agent outputs, shared workflow context, recommendation, explanation, and audit reference.

### Environment Configuration

The frontend Render service requires:

| Variable | Configuration |
|---|---|
| `BACKEND_URL` | `https://aa007-backend.onrender.com` |

No application secrets are required for the current deployment.

### Cloud Deployment Constraints

- Both services use the Render Free instance type.
- Free services may spin down after inactivity, causing a delay on the first request.
- Audit records remain in process-local memory and may be lost when the backend restarts or is replaced.
- No persistent database or external audit storage is configured.

The cloud deployment changes the hosting and request-routing arrangement only. It does not change the agents, scoring model, business rules, or deterministic decision workflow.

## 11. Technology and Design Constraints

- Python 3.11 for backend development.
- FastAPI for backend API services.
- Pydantic for structured data validation.
- LangGraph for deterministic linear workflow orchestration using `StateGraph`.
- React and TypeScript for the user interface.
- Deterministic scoring and decision rules.
- Seeded sample data for reproducible demonstrations.
- Pytest for backend testing.
- Docker and Docker Compose for containerized local validation.
- Render for cloud deployment.

### Current Phase 2.1 Scope

The current implementation uses LangGraph to orchestrate the existing five-agent workflow through a fixed sequence of nodes.

The following capabilities remain outside the current scope:

- Conditional workflow routing.
- LLM-based decision-making.
- Retrieval-Augmented Generation (RAG).
- Vector databases.
- Model Context Protocol (MCP).
- Live CRM integration.
- Automatic customer communication.

LangGraph manages workflow execution and shared state. Business scoring, prioritization, and recommendations remain deterministic and are produced by the existing agents and business rules.

## 12. Architecture Objective

The architecture demonstrates how specialized deterministic agents collaborate through a shared workflow context to produce explainable, auditable, and reproducible sales operations recommendations.

LangGraph provides explicit workflow orchestration through a linear StateGraph, while the existing agents retain responsibility for validation, evidence evaluation, scoring, and prioritization.

The architecture preserves the established business outcomes while making workflow execution order and node status observable through execution tracing.

## 13. Phase 2.1 — LangGraph Linear Orchestration

### 13.1 Implementation

Phase 2.1 evolves the existing deterministic workflow by introducing LangGraph `StateGraph` orchestration.

The implementation adds two workflow modules:

- `backend/app/services/workflow_state.py` — defines the shared state passed between workflow nodes.
- `backend/app/services/workflow_graph.py` — defines and compiles the LangGraph workflow.

The `WorkflowService` invokes the compiled graph and returns the resulting workflow context.

The graph contains seven nodes:

| Execution order | LangGraph node | Responsibility |
|---:|---|---|
| 1 | `build_context` | Creates the shared workflow context. |
| 2 | `lead_intake` | Validates mandatory lead information. |
| 3 | `recency` | Evaluates lead recency. |
| 4 | `engagement` | Evaluates engagement evidence. |
| 5 | `fit_sla` | Evaluates fit and follow-up SLA conditions. |
| 6 | `priority_decision` | Applies deterministic prioritization rules. |
| 7 | `explanation_audit` | Generates the explanation and records the audit entry. |

The graph starts at `START`, follows fixed sequential edges, and terminates at `END`.

### 13.2 Execution Tracing

Each node appends an execution-trace entry to the workflow context.

Each entry contains:

- `node` — the workflow node name.
- `status` — the execution status.

Supported statuses include `completed`, `skipped`, and `failed`.

For valid leads, all seven nodes complete successfully.

For invalid leads, the four downstream analytical agent nodes are skipped after lead intake validation. Explanation and audit generation still take place.

### 13.3 Business Outcome Preservation

The LangGraph migration preserves the existing deterministic business rules and recommendations.

| Scenario | Expected recommendation | Priority score |
|---|---|---:|
| HOT | `FOLLOW_UP_NOW` | 95 |
| WARM | `FOLLOW_UP_SOON` | 65 |
| STALE | `NURTURE` | 0 |
| Missing mandatory contact information | `REQUEST_DATA` | 0 |

The existing API response structure and frontend integration are preserved. Execution-trace information is exposed through the workflow context.

LangGraph is responsible for orchestration, not business decision-making.

### 13.4 Validation Results

Phase 2.1 validation covered:

- Successful StateGraph compilation.
- Verification of the seven-node linear execution order.
- HOT, WARM, and STALE scenario execution.
- Missing mandatory contact information handling.
- Execution-trace status verification.
- Preservation of deterministic recommendations and explanations.
- API execution through FastAPI.
- Local Docker Compose build and container health checks.
- Frontend scenario execution through the local containerized application.
- Backend automated tests.

The backend test suite completed successfully with **9 passed tests**.

The local Docker Compose application was also validated, with both backend and frontend containers healthy.

### 13.5 Phase Boundary

Phase 2.1 introduces linear LangGraph orchestration without changing the underlying business logic.

Conditional routing, dynamic workflow paths, LLM-based decisions, RAG, vector databases, and MCP remain outside this phase and are reserved for later development.