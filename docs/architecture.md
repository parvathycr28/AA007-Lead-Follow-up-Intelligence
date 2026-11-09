# Lead Follow-up Prioritization Intelligence

**Product:** APEX — Lead Intelligence Platform
**Case ID:** AA007
**Architecture Version:** 1.0

## 1. Architecture Overview

APEX follows a deterministic multi-agent workflow architecture.

A lead record enters through the API, and the Context Builder creates a run-scoped shared workflow context. The Lead Intake Agent validates the lead information before the Recency, Engagement, and Fit & SLA Agents evaluate their respective business evidence.

The Lead Priority Decision Agent combines the outputs and applies deterministic business rules to generate a recommendation.

The workflow then produces a structured explanation and an audit record. The frontend exposes the business input, run-scoped shared workflow context, agent execution order and outputs, decision evidence, final recommendation, explanation, and audit reference so reviewers can inspect how each recommendation is produced.

## 2. High-Level Workflow

```text
User / Frontend
       |
       v
FastAPI Endpoint
       |
       v
Context Builder
       |
       v
Run-Scoped Shared Workflow Context
       |
       v
Lead Intake Agent
       |
       +--------------------+
       |                    |
       v                    v
   Valid Input          Invalid Input
       |                    |
       v                    v
 Recency Agent          REQUEST_DATA
       |                    |
       v                    |
 Engagement Agent           |
       |                    |
       v                    |
 Fit & SLA Agent             |
       |                    |
       v                    |
 Lead Priority Decision     |
       |                    |
       +--------------------+
                 |
                 v
          Final Recommendation
                 |
          +------+------+
          |             |
          v             v
     Explanation      Audit
       Service       Service
          |             |
          +------+------+
                 |
                 v
            API Response
                 |
                 v
              Frontend
```

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

Each workflow execution uses its own context to carry information between agents.

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

This structure keeps the workflow state organized and makes individual executions easier to inspect.

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

The React and TypeScript frontend communicates with the backend through the Vite development proxy.

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

## 10. Technology and Design Constraints

- Python and FastAPI for backend services.
- Pydantic for structured data validation.
- React and TypeScript for the user interface.
- Deterministic scoring and decision rules.
- Seeded sample data for reproducible demonstrations.
- Pytest for backend testing.

The current MVP intentionally excludes LLM-based decision-making, LangGraph, RAG, vector databases, live CRM integration, and automatic customer communication.

## 11. Architecture Objective

The architecture demonstrates how specialized agents can collaborate through a shared workflow context to produce explainable, auditable, and deterministic sales operations recommendations.