# APEX — Lead Follow-up Prioritization Intelligence

**Case ID:** AA007  
**Product:** APEX — Lead Intelligence Platform
**Domain:** Sales Operations
**Architecture Version:** 3.2
**Current Phase:** Phase 3 — Final Demo & Portfolio Package

## 1. Architecture Overview

APEX follows a deterministic, multi-agent workflow architecture orchestrated using LangGraph.

The application accepts structured lead information through a FastAPI backend. A compiled LangGraph `StateGraph` coordinates lead validation, analytical agent execution, conditional business routing, explanation generation, and audit recording.

Five specialized agents perform the lead evaluation:

1. Lead Intake Agent
2. Recency Agent
3. Engagement Agent
4. Fit & SLA Agent
5. Lead Priority Decision Agent

The workflow uses structured, run-scoped state to carry information between agents and workflow nodes.

The final recommendation is produced by deterministic business rules and scoring. An optional Google Gemini integration enhances explanation readability but cannot modify the recommendation, priority score, or business rules.

The React and TypeScript frontend presents the business recommendation separately from the technical execution details. The Explainability & Audit section provides access to the workflow context, agent outputs, execution trace, Gemini metadata, and audit record.

The architecture maintains three clear responsibilities:

- **Decision layer:** Deterministic validation, scoring, and recommendation.
- **Orchestration layer:** LangGraph workflow execution and conditional routing.
- **Presentation layer:** Business-facing recommendation and technical explainability.

## 2. High-Level Architecture

```text
                 User
                  |
                  v
          React + TypeScript
             Frontend
                  |
                  v
          Nginx API Proxy
                  |
                  v
             FastAPI
              Backend
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
            Intake Router
                  |
          +-------+--------+
          |       |        |
          v       v        v
       recency  request_  workflow_
          |      data      error
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
     Priority Router
          |
    +-----+------+-------+-------+
    |     |      |       |       |
    v     v      v       v       v
 overdue high  follow_ nurture workflow_
 follow  priority up_soon         error
    |     |      |       |       |
    +-----+------+-------+-------+
                  |
                  v
          build_explanation
                  |
                  v
          gemini_explanation
          (controlled optional
             enhancement)
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
             /       \
            v         v
       Business     Explainability
       Recommendation  & Audit
```

## 3. Agent Responsibilities

### 3.1 Lead Intake Agent

- Validates mandatory lead information.
- Normalizes lead fields.
- Identifies missing or invalid information.
- Produces validated lead data.
- Determines whether the lead can proceed through analytical evaluation.

Missing mandatory information results in the `REQUEST_DATA` path.

### 3.2 Recency Agent

- Evaluates lead age and last-contact date.
- Applies configured recency scoring bands.
- Produces a recency score and supporting evidence.

### 3.3 Engagement Agent

- Evaluates approved business engagement events.
- Applies configured event weights.
- Produces an engagement score and supporting evidence.

### 3.4 Fit & SLA Agent

- Evaluates declared business need.
- Checks pending follow-up commitments.
- Identifies overdue follow-up conditions.
- Produces fit and SLA outputs.

### 3.5 Lead Priority Decision Agent

- Combines the outputs from the analytical agents.
- Applies deterministic decision precedence.
- Produces the final recommendation, priority score, reasons, and triggered business rules.

The five agents retain responsibility for validation, evidence evaluation, scoring, and business decisions. Neither LangGraph nor Gemini independently determines the business recommendation.

## 4. LangGraph Workflow and Conditional Routing

The backend invokes a compiled LangGraph `StateGraph`.

The graph initializes a workflow context, executes lead intake, and uses conditional routers to select the appropriate business path.

### 4.1 Intake Routing

After the Lead Intake Agent executes, the intake router selects one of the following paths:

| Condition | Selected route | Behaviour |
|---|---|---|
| Mandatory information is valid | `recency` | Continue through the analytical agents. |
| Mandatory information is missing | `request_data` | Return a data-completion recommendation. |
| Intake or workflow failure | `workflow_error` | Follow the workflow error path. |

The missing-data path skips the four downstream analytical agents.

### 4.2 Priority Routing

Valid leads proceed through Recency, Engagement, and Fit & SLA before reaching the Lead Priority Decision Agent.

The priority router selects the outcome path based on deterministic business rules.

| Route | Triggering condition | Recommendation |
|---|---|---|
| `overdue_follow_up` | `OVERDUE_FOLLOW_UP` | `FOLLOW_UP_NOW` |
| `high_priority` | `HIGH_PRIORITY_SCORE` | `FOLLOW_UP_NOW` |
| `follow_up_soon` | `MODERATE_PRIORITY_SCORE` | `FOLLOW_UP_SOON` |
| `nurture` | `LOW_PRIORITY_SCORE` | `NURTURE` |
| `workflow_error` | Execution failure or unidentified route | Workflow error handling |

Overdue follow-up takes precedence over the ordinary high-priority score route.

### 4.3 Common Explanation and Audit Path

All business outcome paths converge on the following nodes:

1. `build_explanation`
2. `gemini_explanation`
3. `explanation_audit`

The deterministic explanation is created first. The optional Gemini enhancement is then attempted. Finally, the audit stage records the completed workflow information.

This common path ensures that successful decisions, incomplete-data outcomes, and workflow error outcomes follow the same explanation and audit sequence.

## 5. Decision and Scoring Layer

APEX uses deterministic scoring and explicit business rules.

The current MVP uses the following provisional scoring allocation. These weights and scoring rules are implementation assumptions, not prescribed Product Bible values, and may be refined using validated operational data.

| Component | Maximum points |
|---|---:|
| Recency | 30 |
| Engagement | 40 |
| Declared need / fit | 30 |
| **Total** | **100** |

The priority score is calculated by adding the three component scores and capping the result at 100:

`Priority Score = min(Recency + Engagement + Fit, 100)`

The current provisional scoring rules are:

- **Recency:** 30 points for contact within 7 days, 20 points for 8–30 days, 10 points for 31–60 days, and 0 points beyond 60 days or when no contact date is available.
- **Engagement:** Recognized engagement events contribute their configured event weights. The total engagement score is capped at 40.
- **Fit:** A declared business need contributes 30 points; otherwise, the fit score is 0.

### Decision precedence

The Lead Priority Decision Agent applies the following rules in order:

1. Missing or invalid mandatory lead information → `REQUEST_DATA`.
2. Overdue committed follow-up → `FOLLOW_UP_NOW`.
3. Priority score of 70 or higher → `FOLLOW_UP_NOW`.
4. Priority score of 40–69 → `FOLLOW_UP_SOON`.
5. Priority score below 40 → `NURTURE`.

Missing mandatory information and overdue follow-up conditions take precedence over ordinary score-based decisions.

These scoring bands, event weights, and thresholds are provisional MVP implementation assumptions. They are not prescribed Product Bible values.

The decision layer combines the analytical results and applies business-rule precedence.

Important conditions include:

- Overdue committed follow-up can trigger `FOLLOW_UP_NOW`.
- High fit combined with recent engagement supports higher priority.
- Low engagement and older leads can be routed to `NURTURE`.
- Missing mandatory information triggers `REQUEST_DATA`.

The four recommendation outcomes are:

| Recommendation | Business meaning |
|---|---|
| `FOLLOW_UP_NOW` | The lead needs prompt attention. |
| `FOLLOW_UP_SOON` | The lead should remain in the active follow-up queue. |
| `NURTURE` | The lead is better suited to continued engagement. |
| `REQUEST_DATA` | Mandatory lead information must be completed before prioritization can continue. |

The same valid input and configured rules produce the same deterministic result.

The frontend does not calculate a replacement score or override the backend recommendation.

## 6. Workflow State and Context

Each workflow execution maintains its own shared workflow context.

The context carries information between LangGraph nodes and agents, including:

- Workflow identifier.
- Original lead record.
- Normalized lead snapshot.
- Lead Intake validation outcome.
- Validated lead information, when valid.
- Recency score.
- Engagement score.
- Fit score and SLA flags.
- Individual agent outputs.
- Final recommendation.
- Explanation.
- Audit reference.
- Errors.
- Execution trace.

The LangGraph state passes the lead record, engagement events, and workflow context between nodes.

The context is run-scoped. It is not a long-term lead memory or persistent customer profile store.

### 6.1 Execution Trace

The workflow records node execution information.

Each trace entry includes:

- `node` — workflow node name.
- `status` — execution status.

Router entries also include:

- `route` — selected conditional route.
- `condition` — triggering condition.

The trace records the selected business path and the execution status of the workflow nodes.

## 7. Explanation and Controlled Gemini Enhancement

### 7.1 Deterministic Explanation

The Explanation Service generates the original explanation from the workflow context.

It uses the final recommendation, supporting reasons, available evidence, and executed-agent information.

This deterministic explanation remains the authoritative fallback.

### 7.2 Gemini Explanation Enhancement

The optional `GeminiExplainer` service enhances the readability of the deterministic explanation after the business decision has been completed.

The structured evidence supplied to Gemini includes:

- Recommendation action.
- Priority score.
- Score breakdown.
- Triggered business rules.
- Supporting reasons.
- Executed agents.

The lead identifier is excluded from the external explanation request.

### 7.3 Validation and Safeguards

The Gemini response is validated before acceptance.

The implementation requires:

- A non-empty response.
- A single-line explanation.
- A maximum length of 500 characters.
- Preservation of the exact recommendation action.
- Preservation of the exact priority score.

The prompt restricts the model to rewriting supplied evidence. It prohibits invented facts, unsupported predictions, promises, and changes to the deterministic decision.

The following conditions trigger deterministic fallback:

- Missing provider configuration.
- Provider errors.
- Request timeouts.
- Invalid or unacceptable responses.

If Gemini is unavailable, the original deterministic explanation is retained.

### 7.4 Configuration

The service reads configuration from environment variables:

| Variable | Purpose |
|---|---|
| `LLM_PROVIDER` | Selects the configured provider. |
| `GEMINI_API_KEY` | Authenticates requests to Google Gemini. |
| `GEMINI_MODEL` | Specifies the Gemini model. |
| `LLM_TIMEOUT` | Sets the request timeout in seconds. |

The API key is maintained outside source control. It must not be committed to GitHub or included in documentation.

Gemini is an optional explanation enhancement. It does not perform validation, scoring, recommendation selection, routing, or autonomous customer actions.

## 8. Audit Service

The Audit Service records information about workflow executions, including:

- Workflow ID.
- Audit reference.
- Execution timestamp.
- Agent execution sequence.
- Agent outputs.
- Triggered business rules.
- Final recommendation.
- Errors, where applicable.
- Complete execution trace.
- Gemini provider, model, status, and execution reason when available.

The audit stage records the complete execution trace after the explanation and Gemini processing stages.

This preserves the selected business paths, execution statuses, and explanation outcome for inspection.

### 8.1 Storage Limitation

Audit records are stored in process-local memory in the current MVP.

They are not guaranteed to survive backend restarts or container replacement.

Persistent database-backed audit storage is outside the current implementation scope.

## 9. Frontend Architecture

The frontend uses React and TypeScript.

It communicates with the FastAPI backend through relative `/api/` request paths.

### 9.1 Business-Facing Recommendation

The normal application screen focuses on:

- Lead information and engagement context.
- Recommendation outcome.
- Priority score and available score breakdown.
- Recommendation explanation.
- Supporting evidence and triggered rules.
- Suggested next action.

The interface retains the product's dark navy and gold visual design.

### 9.2 Explainability & Audit

Internal technical execution information is separated from the normal business-facing screen.

The collapsed-by-default **Explainability & Audit** section provides access to:

- Run-scoped workflow context.
- Five-agent execution timeline.
- Structured agent outputs.
- LangGraph routing and execution trace.
- Gemini provider and model information.
- Gemini execution status and fallback reason.
- Audit reference and complete audit record.
- Relevant raw JSON for technical inspection.

Expanding or collapsing this section changes only frontend presentation. It does not change workflow execution, API responses, or business decisions.

### 9.3 Suggested Next Actions

The frontend presents predefined guidance based on the final deterministic recommendation.

These suggestions are intended for human sales users.

They do not automatically contact leads, schedule activities, update CRM records, or perform external business actions.

## 10. API and Service Integration

The FastAPI backend exposes endpoints for lead prioritization, seeded scenarios, and health checks.

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/leads/prioritize` | POST | Prioritizes a supplied lead record. |
| `/api/leads/scenarios` | GET | Lists available seeded scenarios. |
| `/api/leads/scenarios/{scenario_name}/run` | POST | Executes a seeded scenario. |
| `/api/assistant/health` | GET | Backend health check. |

The seeded scenarios are:

- `hot` — recent inquiry, high fit, overdue follow-up.
- `warm` — moderate engagement and valid declared need.
- `stale` — older lead with no recognized engagement.

The incomplete-contact scenario is submitted as an incomplete lead record to demonstrate the `REQUEST_DATA` route.

The API response includes the workflow identifier, lead identifier, recommendation, explanation, audit reference, workflow context, audit record, and errors where applicable.

## 11. Docker Deployment Architecture

The application is containerized using Docker and Docker Compose.

### 11.1 Backend Container

- Built from `backend/Dockerfile`.
- Uses Python 3.11.
- Runs FastAPI through Uvicorn.
- Listens on port `8002` inside the container.
- Provides the backend health endpoint at `/api/assistant/health`.

### 11.2 Frontend Container

- Built from `frontend/Dockerfile`.
- Uses Node.js to generate the React production build.
- Uses Nginx to serve static frontend files.
- Listens on container port `80`.
- Publishes the application on host port `8080`.

### 11.3 Container Communication

Docker Compose creates an internal network for the services.

Nginx forwards `/api/` requests to:

```text
http://backend:8002
```

The frontend uses the backend service through the internal Docker network.

### 11.4 Health Checks

- Backend health is checked through `/api/assistant/health`.
- Frontend health is checked through `/health`.
- Docker Compose reports the container health status.

The containerized deployment preserves the existing deterministic business workflow and agent responsibilities.

## 12. Cloud Deployment — Render

The application is deployed on Render using two independent Docker-based Web Services.

### 12.1 Frontend

- **Service:** `aa007-frontend`
- **Public URL:** https://aa007-frontend.onrender.com
- Built using `frontend/Dockerfile`.
- Serves the React production build through Nginx.
- Uses `BACKEND_URL` to identify the backend service.

### 12.2 Backend

- **Service:** `aa007-backend`
- **Public URL:** https://aa007-backend.onrender.com
- **Health endpoint:** `/api/assistant/health`
- Built using `backend/Dockerfile`.
- Runs FastAPI through Uvicorn on port `8002`.

### 12.3 Cloud Request Flow

1. The user opens the public frontend URL.
2. Nginx serves the React application.
3. The frontend sends same-origin requests under `/api/`.
4. Nginx forwards the requests to the backend configured through `BACKEND_URL`.
5. FastAPI executes the deterministic workflow.
6. The backend returns the recommendation and workflow information.
7. The frontend presents the business recommendation and technical details.

The frontend environment variable is configured as:

```text
BACKEND_URL=https://aa007-backend.onrender.com
```

The backend's optional Gemini configuration is maintained separately through backend environment variables.

### 12.4 Cloud Deployment Constraints

- Both services use the Render Free instance type.
- Free services may spin down after inactivity, causing a delay on the first request.
- Audit records are stored in process-local memory.
- Records may be lost when the backend restarts or is replaced.
- No persistent database or external audit storage is configured.

## 13. Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI |
| Data validation | Pydantic |
| Workflow orchestration | LangGraph StateGraph |
| LLM explanation | Google Gemini, `google-genai` SDK |
| Frontend | React, TypeScript |
| Frontend tooling | Vite |
| Web server and proxy | Nginx |
| Testing | Pytest |
| Containerization | Docker, Docker Compose |
| Cloud deployment | Render |

## 14. Testing and Validation

### 14.1 Backend Automated Tests

The backend test suite was executed using the project's Python 3.11.9 virtual environment.

**Latest verified result:**

```text
17 passed in 1.53s
```

The test suite includes:

- Seed scenario workflow execution.
- Scenario listing and execution APIs.
- Unknown scenario handling.
- Missing mandatory contact information.
- High-priority conditional routing.
- Gemini successful explanation.
- Gemini provider-error fallback.
- Gemini timeout fallback.
- Invalid-response fallback.
- Missing-configuration fallback.
- Exclusion of lead identifiers from the Gemini prompt.
- Preservation of the `REQUEST_DATA` recommendation.

These tests verify the Gemini integration's success and fallback behavior through the automated test setup. They do not establish that a live Gemini request succeeds in every deployment.

### 14.2 Application Scenario Validation

The following four scenarios were manually verified:

| Scenario | Expected recommendation | Validation |
|---|---|---|
| HOT lead | `FOLLOW_UP_NOW` | Passed |
| WARM lead | `FOLLOW_UP_SOON` | Passed |
| STALE lead | `NURTURE` | Passed |
| Missing contact information | `REQUEST_DATA` | Passed |

The missing-contact scenario correctly follows the mandatory-data validation route and skips the downstream analytical agents.

### 14.3 Frontend Validation

The frontend was validated through:

- TypeScript compilation.
- Production build.
- Docker frontend image build.
- Local Docker Compose startup.
- Business-facing recommendation presentation.
- Explainability & Audit expansion.
- Responsive layout checks at 1440px, 768px, 390px, and 320px.

### 14.4 Render Validation

The deployed application was verified through:

- Backend scenario API response.
- Frontend Nginx proxy response.
- Correct `BACKEND_URL` configuration.
- Dashboard loading.
- Execution of all four application scenarios.

The deployed frontend and backend are available at the Render URLs documented in Section 12.

## 15. Product Evolution

The architecture evolved through three implementation stages.

### Stage 1 — Deterministic Foundation

The initial implementation established:

- Structured lead inputs.
- Five specialized agent responsibilities.
- Deterministic scoring and business rules.
- Four recommendation outcomes.
- Evidence-based explanations and audit information.

### Stage 2 — LangGraph Conditional Orchestration

LangGraph introduced:

- Shared workflow state.
- Explicit workflow nodes.
- Conditional intake routing.
- Conditional priority routing.
- Execution trace and selected route information.

The business decision authority remained with the deterministic agents and rules.

### Stage 3 — Controlled LLM Explanation and Productization

The subsequent implementation introduced:

- Optional Gemini explanation enhancement.
- Response validation and deterministic fallback.
- Explanation audit metadata.
- A business-facing recommendation experience.
- A separate Explainability & Audit section.

Gemini remains restricted to explanation readability. The deterministic decision engine remains the source of truth.

## 16. Limitations and Non-Goals

APEX is an internship MVP and demonstration application.

It is not intended to:

- Autonomously contact customers.
- Negotiate pricing or contracts.
- Use sensitive demographic characteristics for prioritization.
- Replace human sales judgment.
- Guarantee AI explanation accuracy.
- Claim production readiness or enterprise integration.

The current implementation does not include:

- Live CRM integration.
- Automatic CRM updates.
- Automatic follow-up scheduling.
- Persistent database-backed audit storage.
- Retrieval-Augmented Generation.
- Vector databases.
- Model Context Protocol integrations.
- Autonomous external business actions.

Future production use would require appropriate data governance, access controls, persistent storage, operational monitoring, and integration validation.

## 17. Architecture Objective

APEX combines deterministic multi-agent decision-making, LangGraph conditional orchestration, controlled LLM explanation enhancement, and a business-oriented frontend.

The architecture preserves a clear separation between:

- Deterministic business decisions.
- Workflow orchestration and shared state.
- Optional explanation enhancement.
- Audit recording.
- Business-facing presentation.
- Technical workflow inspection.

This design provides explainable lead follow-up prioritization while keeping business authority deterministic and the complete execution journey available for review.