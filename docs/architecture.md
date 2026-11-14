# Lead Follow-up Prioritization Intelligence

**Product:** APEX — Lead Intelligence Platform  
**Case ID:** AA007  
**Architecture Version:** 3.1  
**Current Phase:** Phase 3.1 — Business Experience Separation & Productization

## 1. Architecture Overview

APEX follows a deterministic multi-agent workflow architecture orchestrated using LangGraph.

A lead record enters through the FastAPI endpoint. The LangGraph StateGraph initializes the workflow context, validates the lead, and uses deterministic conditional routers to select the appropriate business execution path. Valid leads proceed through the Recency, Engagement, Fit & SLA, and Lead Priority Decision stages. Missing mandatory data and workflow failures follow dedicated outcome paths.

The Context Builder creates a run-scoped shared workflow context. The Lead Intake Agent validates the lead information before the analytical agents execute.

For valid leads, all five agents execute. Leads with missing mandatory information follow the `request_data` path and skip the four downstream analytical agents. After priority evaluation, the graph selects an outcome path based on the deterministic triggered business rule. Every outcome path converges on explanation generation, optional controlled Gemini enhancement, and audit recording.

LangGraph manages conditional orchestration and shared workflow state. It does not independently make business decisions. The existing agents, deterministic scoring rules, recommendation logic, and business rules retain decision-making authority.

The workflow records node execution statuses and router selections, including the selected route and triggering condition. The complete execution trace is copied into the audit record, including the final explanation and audit completion entry.

The frontend provides a business-oriented interface for entering or selecting lead scenarios and reviewing the resulting prioritization decisions. The normal business-facing screen focuses on:

- Lead information and engagement context.
- Recommendation outcome and priority score.
- Recommendation explanation and business-readable reasons.
- Supporting evidence and triggered business rules.
- Suggested next action.

Internal technical execution information is separated from the normal business-facing experience.

A collapsed-by-default **Explainability & Audit** section provides access to the detailed technical journey when expanded. It retains the run-scoped workflow context, five-agent execution timeline, structured agent outputs, LangGraph routing and execution trace, Gemini metadata, and audit information, including raw JSON where useful.

The application uses a consistent dark navy and gold visual design. The recommendation experience includes an explanation of why an outcome was selected and a suggested next action to help users understand the appropriate follow-up response.

An optional Google Gemini service enhances the readability of the deterministic explanation. It cannot alter the recommendation, priority score, or business rules. If the provider is unavailable or its response fails validation, the original deterministic explanation is retained.

The Phase 3.1 product experience enhancement does not change the underlying deterministic business workflow, scoring model, agent responsibilities, or API decision authority.

## 2. High-Level Workflow

The FastAPI endpoint invokes the compiled LangGraph StateGraph. The graph uses conditional edges after lead intake and priority decision to select the appropriate execution path.

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
   Intake Router
       |
       +--------------------+--------------------+
       |                    |                    |
   Valid data          Missing data       Intake failure
       |                    |                    |
       v                    v                    v
    recency             request_data       workflow_error
       |                    |                    |
       v                    +---------+----------+
  engagement                        |
       |                             |
       v                             |
    fit_sla                          |
       |                             |
       v                             |
 priority_decision                   |
       |                             |
       v                             |
  Priority Router                    |
       |                             |
       +--> overdue_follow_up        |
       +--> high_priority            |
       +--> follow_up_soon           |
       +--> nurture                  |
       +--> workflow_error           |
       |                             |
       +-------------+---------------+
                     |
                     v
             build_explanation
                     |
                     v
             gemini_explanation
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
                     |
          +----------+----------+
          |                     |
          v                     v
  Business-facing        Explainability
  Recommendation          & Audit
  Presentation            (collapsed by
                           default)
          |                     |
          v                     v
  Lead information       Shared workflow
  Recommendation         context
  Priority and status    Five-agent timeline
  Explanation            Structured outputs
  Evidence               LangGraph trace
  Suggested action       Gemini metadata
                         Audit and raw JSON
```

### 2.1 Workflow Execution Behaviour

- **Valid lead:** Intake validation succeeds, followed by the four analytical agents and the priority router.
- **Missing mandatory data:** The intake router selects `request_data`. The four downstream analytical agents are skipped.
- **Overdue follow-up:** The priority router selects `overdue_follow_up` when the `OVERDUE_FOLLOW_UP` rule is triggered.
- **High priority:** The priority router selects `high_priority` when the `HIGH_PRIORITY_SCORE` rule is triggered.
- **Moderate priority:** The priority router selects `follow_up_soon` when the `MODERATE_PRIORITY_SCORE` rule is triggered.
- **Low priority:** The priority router selects `nurture` when the `LOW_PRIORITY_SCORE` rule is triggered.
- **Workflow failure:** The graph selects `workflow_error` when an execution failure occurs or a priority route cannot be identified.
- **Deterministic explanation:** All outcome paths converge on `build_explanation`, which generates the original evidence-based explanation.
- **Gemini enhancement:** `gemini_explanation` optionally rewrites the explanation using structured decision evidence. The lead identifier is excluded, and the recommendation and priority score remain unchanged.
- **Explanation and audit:** `explanation_audit` records the complete execution trace after the Gemini result or deterministic fallback has been applied.
- **Frontend presentation:** The frontend presents the business recommendation separately from the technical workflow and audit information.

### 2.2 Conditional Routing and Execution Trace

The intake router records its selected route and condition, such as `recency` with `INTAKE_VALID` or `request_data` with `MISSING_MANDATORY_DATA`.

The priority router records the selected outcome route and the corresponding triggered rule. Overdue follow-up takes precedence over the high-priority score route.

Each execution-trace entry records a node name and status. Router entries additionally contain `route` and `condition` fields.

The complete execution trace is copied into the audit record after the `explanation_audit` completion entry has been appended. This preserves the selected business paths and their triggering conditions for inspection.

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

The five agents retain their original responsibilities in Phase 3.1. The product experience enhancement does not introduce additional decision-making agents or transfer business decisions to the frontend or Gemini.

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

The execution trace records node names and statuses, along with router selections. Router entries include the selected `route` and triggering `condition`. The audit service copies the complete trace into the audit record so that the workflow path can be inspected alongside the recommendation and agent outputs.

### 4.1 Frontend Access to Workflow Context

The backend continues to return the workflow information required for recommendation presentation and technical inspection.

The frontend separates this information into two presentation areas.

**Business-facing recommendation area:**

- Lead information and engagement context.
- Final recommendation.
- Priority score and available score breakdown.
- Recommendation explanation.
- Supporting evidence and triggered business rules.
- Suggested next action.

**Explainability & Audit area:**

- Run-scoped shared workflow context.
- Agent execution timeline and statuses.
- Structured outputs from the five agents.
- LangGraph execution trace and selected routing conditions.
- Gemini provider, model, execution status, and reason when available.
- Audit reference and complete audit record.
- Relevant raw JSON for technical inspection.

The Explainability & Audit section is collapsed by default. The reviewer can expand it when technical details are required.

The explanatory recommendation context and suggested next action are presentation-layer elements derived from the final recommendation. They do not change the shared workflow state or determine the business outcome.

This structure supports a focused business experience while preserving execution inspection, route validation, and audit traceability.

Audit storage remains process-local in the current MVP.

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

The decision layer remains independent of the frontend presentation layer. Recommendation explanations and suggested next actions do not modify scoring calculations, triggered rules, or recommendation selection.

## 6. Explanation and Controlled LLM Enhancement

### 6.1 Deterministic Explanation

The Explanation Service generates the original structured explanation from the workflow context.

It communicates:

- Which agents executed.
- The final recommendation.
- The supporting reasons.
- Relevant evidence.
- Known limitations.

This deterministic explanation remains the authoritative fallback.

### 6.2 Gemini Explanation Enhancement

The optional `GeminiExplainer` service improves the readability of the deterministic explanation after the business decision has been completed.

The service receives only structured decision evidence, including:

- Recommendation action.
- Priority score.
- Score breakdown.
- Triggered business rules.
- Supporting reasons.
- Executed agents.

The lead identifier is excluded from the external request.

**Validation and safeguards:**

- The response must preserve the exact recommendation action and priority score.
- The response must be non-empty, single-line, and no longer than 500 characters.
- Provider errors, timeouts, missing configuration, and invalid responses result in deterministic fallback.
- The LLM cannot modify validation, scoring, routing, recommendation selection, or business rules.
- The service does not initiate customer communication or autonomous actions.

The provider, model, status, and execution reason are recorded in the `gemini_explanation` execution-trace entry.

### 6.3 Configuration

The service reads its configuration from environment variables:

| Variable | Purpose |
|---|---|
| `LLM_PROVIDER` | Selects the configured provider. |
| `GEMINI_API_KEY` | Authenticates requests to Google Gemini. |
| `GEMINI_MODEL` | Specifies the Gemini model. |
| `LLM_TIMEOUT` | Sets the request timeout in seconds. |

The API key is kept outside source control in `backend/.env`. The example environment file contains placeholders only.

### 6.4 Relationship to the Phase 3.1 Product Experience

Phase 3.1 builds on the existing deterministic explanation and controlled Gemini enhancement.

The frontend presents the recommendation explanation and the suggested next action as separate business-oriented elements.

The recommendation explanation communicates the meaning of the selected outcome. The suggested next action provides guidance on the corresponding follow-up activity.

These elements are based on the final recommendation and use predefined presentation content. They are not generated as new business decisions by Gemini.

If Gemini is unavailable, the deterministic explanation remains available. The recommendation and suggested next action continue to be presented according to the deterministic workflow outcome.

Technical information about the Gemini enhancement remains accessible in the Explainability & Audit section rather than being displayed in the normal business-facing screen.

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
- Complete execution trace, including selected routes, triggering conditions, and node statuses.
- Gemini enhancement metadata, including provider, model, status, and execution reason, when the enhancement node executes.

The audit service copies the complete execution trace into each audit record after the `explanation_audit` completion entry has been appended. The trace includes the Gemini enhancement status and fallback reason when applicable.

The frontend makes the audit information returned by the backend available through the Explainability & Audit section. This allows technical reviewers to inspect the execution evidence associated with a recommendation without exposing the full technical record in the normal business-facing experience.

The recommendation explanation and suggested next action are presentation-layer elements. They do not replace the original execution trace or audit record.

Audit records are stored in process-local memory in the current MVP. The execution trace is preserved in each audit record, but records are not durable across backend restarts. Persistent audit storage is outside the current implementation scope.

## 8. API and Frontend Integration

The FastAPI backend exposes endpoints for health checks, lead prioritization, scenario listing, and scenario execution.

The React and TypeScript frontend communicates with the backend through the Vite development proxy during local development.

In the production deployment, the frontend uses Nginx to forward requests under `/api/` to the configured backend service. The browser communicates with the frontend origin, while Nginx handles backend routing.

### 8.1 Business-Facing Recommendation Presentation

Phase 3.1 improves the business-facing presentation of the existing prioritization results.

The original dark navy and gold visual design is retained. The normal application screen focuses on the information needed to understand and act on the recommendation.

The business-facing screen presents:

- Lead information and engagement context.
- Recommendation outcome and priority score.
- Recommendation explanation and business-readable reasons.
- Supporting evidence and triggered business rules.
- Suggested next action.

The internal agent execution timeline, shared workflow context, raw structured agent outputs, technical execution trace, Gemini metadata, and detailed audit JSON are not displayed in the normal business-facing view.

### 8.2 Recommendation Outcomes

The frontend supports four recommendation outcomes:

| Recommendation | Display label | Business meaning |
|---|---|---|
| `FOLLOW_UP_NOW` | Follow Up Now | The lead needs prompt attention. |
| `FOLLOW_UP_SOON` | Follow Up Soon | The lead should remain in the active follow-up queue. |
| `NURTURE` | Nurture | The lead is better suited to continued engagement. |
| `REQUEST_DATA` | Request Data | Mandatory lead information must be completed before prioritization can continue. |

The frontend provides the following recommendation context:

**FOLLOW_UP_NOW**

This lead needs prompt attention. Review the available evidence and arrange the next follow-up.

**FOLLOW_UP_SOON**

This lead should remain in the active follow-up queue. Schedule the next contact soon.

**NURTURE**

This lead is better suited to continued engagement. Keep it in the nurture process and review it later.

**REQUEST_DATA**

Some mandatory lead information is missing. Complete the required information before prioritization can continue.

### 8.3 Suggested Next Actions

The frontend displays a suggested next action based on the final deterministic recommendation.

| Recommendation | Suggested next action |
|---|---|
| `FOLLOW_UP_NOW` | Contact the lead as soon as practical. Review the declared need and agree on the next step. |
| `FOLLOW_UP_SOON` | Schedule a follow-up within your team's normal response window and keep the lead on the active list. |
| `NURTURE` | Add the lead to the appropriate nurture queue and plan a future engagement review. |
| `REQUEST_DATA` | Ask the responsible team member to provide the missing contact or lead information, then reassess. |

These suggestions are guidance for human users. They do not automatically contact leads, schedule activities, or modify CRM records.

### 8.4 Explainability & Audit — Advanced Technical Details

The Explainability & Audit section separates technical workflow information from the normal business-facing recommendation experience.

It is collapsed by default. A user or technical reviewer can expand the section when deeper execution inspection is needed.

When expanded, the section provides access to:

1. **Run-Scoped Shared Workflow Context**
   - Workflow identifier and execution information.
   - Original and validated lead information.
   - Engagement events and analytical results.
   - Shared workflow state and errors.

2. **Five-Agent Execution Timeline**
   - Agent execution order.
   - Agent statuses.
   - Individual structured outputs.
   - Agent-specific evidence and results.

3. **LangGraph Execution and Routing**
   - Workflow node names and execution statuses.
   - Intake router selection and condition.
   - Priority router selection and triggering condition.
   - Selected business outcome path.
   - Complete execution trace.

4. **Gemini Execution Information**
   - Provider and configured model.
   - Execution status.
   - Execution reason or fallback information.
   - Relevant information returned in the workflow trace.

5. **Audit Information**
   - Audit reference.
   - Recorded recommendation.
   - Agent execution sequence.
   - Triggered rules.
   - Complete audit record.
   - Raw JSON for technical inspection.

The technical information is preserved for internship evaluation, debugging, and verification of the agentic workflow implementation.

The expandable section changes only how the frontend presents the information. It does not change backend execution, API responses, or workflow behavior.

### 8.5 Presentation and Decision Boundaries

The frontend is responsible for displaying the workflow result in a clear and business-oriented format.

The backend remains responsible for:

- Lead validation.
- Agent execution.
- Scoring.
- Business rule evaluation.
- Conditional workflow routing.
- Final recommendation selection.
- Explanation generation.
- Audit recording.

The frontend does not calculate a replacement priority score or override the recommendation returned by the backend.

Phase 3.1 improves the clarity and usability of the existing decision output while keeping the full technical journey accessible through Explainability & Audit.

## 9. Docker Deployment Architecture

The application is containerized using Docker Compose while preserving the existing backend and frontend responsibilities.

### 9.1 Backend Container

- Built from `backend/Dockerfile`.
- Uses Python 3.11 with FastAPI and Uvicorn.
- Listens on port `8002` inside the container.
- Exposes the existing backend health endpoint at `/api/assistant/health`.

### 9.2 Frontend Container

- Built from `frontend/Dockerfile` using a multi-stage build.
- Uses Node.js to generate the React production build.
- Uses Nginx to serve the static frontend files.
- Publishes container port `80` on host port `8080`.

### 9.3 Container Communication

- Docker Compose creates an internal network for the services.
- Nginx forwards `/api/` requests to `http://backend:8002`.
- The backend port is available to the frontend through the internal Docker network.
- The frontend waits for the backend health check before starting.

### 9.4 Health Checks

- Backend health is checked through `/api/assistant/health`.
- Frontend health is checked through `/health`.
- Docker Compose reports container health status.

### 9.5 Runtime and Persistence Limitation

The audit service continues to use process-local in-memory storage. Audit records are not persisted across backend container restarts. No database or persistent audit volume is introduced in this phase.

Dockerization changes the local deployment and serving arrangement; it does not change the deterministic business workflow or agent responsibilities.

## 10. Cloud Deployment Architecture — Render

The application is deployed on Render using two independent Docker-based Web Services. This deployment preserves the existing multi-agent workflow and separates frontend presentation from backend execution.

### 10.1 Frontend Web Service

- **Service:** `aa007-frontend`
- **Public URL:** https://aa007-frontend.onrender.com
- Built using `frontend/Dockerfile`.
- Serves the React production build through Nginx on container port `80`.
- Uses the `BACKEND_URL` environment variable to identify the backend service.

### 10.2 Backend Web Service

- **Service:** `aa007-backend`
- **Public URL:** https://aa007-backend.onrender.com
- **Health endpoint:** `/api/assistant/health`
- Built using `backend/Dockerfile`.
- Runs FastAPI through Uvicorn on container port `8002`.

### 10.3 Cloud Request Flow

1. The user opens the public frontend URL.
2. Nginx serves the React application.
3. The frontend makes same-origin requests under `/api/`.
4. Nginx forwards those requests to the backend URL configured through `BACKEND_URL`.
5. FastAPI executes the existing deterministic workflow and returns the response.
6. The frontend presents the business recommendation and makes the detailed technical workflow information available through Explainability & Audit.

### 10.4 Environment Configuration

The frontend Render service requires:

| Variable | Configuration |
|---|---|
| `BACKEND_URL` | Public URL of the backend service. |

The backend Render service uses the following optional Gemini configuration:

| Variable | Purpose |
|---|---|
| `LLM_PROVIDER` | Set to `gemini`. |
| `GEMINI_API_KEY` | Secret Google Gemini API key. |
| `GEMINI_MODEL` | Configured Gemini model. |
| `LLM_TIMEOUT` | Provider request timeout in seconds. |

The Gemini API key must be configured as a secret environment variable in Render. It must not be committed to source control or included in documentation.

If Gemini is not configured or is unavailable, the workflow retains its deterministic explanation through the fallback mechanism.

### 10.5 Cloud Deployment Constraints

- Both services use the Render Free instance type.
- Free services may spin down after inactivity, causing a delay on the first request.
- Audit records remain in process-local memory and may be lost when the backend restarts or is replaced.
- No persistent database or external audit storage is configured.

### 10.6 Earlier Phase 3.1 Production Deployment

The earlier Phase 3.1 recommendation experience changes were merged into the GitHub `main` branch and deployed through the existing Render services.

The deployed frontend and backend were confirmed as Live after that deployment.

The production frontend was refreshed and validated against the recommendation experience.

The following four scenarios were successfully checked on the deployed application:

| Scenario | Expected recommendation | Validation |
|---|---|---|
| HOT lead | `FOLLOW_UP_NOW` | Passed |
| WARM lead | `FOLLOW_UP_SOON` | Passed |
| STALE lead | `NURTURE` | Passed |
| Missing contact information | `REQUEST_DATA` | Passed |

The recommendation explanations and suggested next actions were also verified for all four outcomes.

The earlier deployment changed the business-facing recommendation presentation. It did not introduce new backend services or change the existing deterministic workflow.

The subsequent Explainability & Audit separation is a further frontend productization correction. Its local validation is documented in Section 14.5. Production verification of that latest correction must be performed after its corresponding deployment.

## 11. Technology and Design Constraints

- Python 3.11 for backend development.
- FastAPI for backend API services.
- Pydantic for structured data validation.
- LangGraph for deterministic conditional workflow orchestration using StateGraph.
- Google Gen AI SDK for optional, controlled Gemini explanation enhancement.
- python-dotenv for loading local environment configuration.
- React and TypeScript for the user interface.
- Deterministic scoring and decision rules.
- Seeded sample data for reproducible demonstrations.
- Pytest for backend testing.
- Docker and Docker Compose for containerized local validation.
- Nginx for production frontend serving and API proxying.
- Render for cloud deployment.

### 11.1 Current Phase 3.1 Scope

The current implementation combines five specialized deterministic agents, LangGraph conditional routing, one controlled Google Gemini explanation enhancement, and a business-oriented frontend recommendation experience.

The workflow preserves deterministic business authority:

- The intake router selects the appropriate path based on mandatory-data validation.
- The priority router selects an outcome path based on deterministic business rules and triggered priority conditions.
- The deterministic explanation is generated after the business decision.
- The optional Gemini service enhances explanation readability using structured evidence.
- The Gemini response is validated before acceptance; failures and invalid responses retain the deterministic explanation.
- The execution trace records provider, model, status, and reason for the Gemini enhancement.
- The complete execution trace is preserved in the audit record.
- The normal frontend screen focuses on the business recommendation and suggested next action.
- The Explainability & Audit section retains access to technical workflow information.
- The frontend does not override deterministic recommendations or calculate alternative business decisions.

The following capabilities remain outside the current scope:

- LLM-based validation, scoring, or business decision-making.
- Dynamic agent selection beyond the defined deterministic workflow routes.
- Retrieval-Augmented Generation (RAG).
- Vector databases.
- Model Context Protocol (MCP).
- Live CRM integration.
- Automatic customer communication.
- Automatic follow-up scheduling.
- Persistent database-backed audit storage.
- Autonomous external business actions.

LangGraph manages conditional workflow execution and shared state. Business scoring, prioritization, and recommendations remain deterministic and are produced by the existing agents and business rules.

## 12. Architecture Objective

LangGraph provides explicit conditional workflow orchestration through a StateGraph, while the existing agents retain responsibility for validation, evidence evaluation, scoring, and prioritization.

The controlled Gemini enhancement improves explanation readability without changing deterministic business decisions. Output validation and deterministic fallback preserve the reliability of the workflow.

The Phase 3.1 product experience makes the resulting recommendations easier for business users to understand and act upon through explanatory context and suggested next actions.

The Explainability & Audit section preserves technical transparency by making the complete workflow journey accessible when required, without placing internal execution details in the normal business-facing experience.

The overall design maintains a clear separation between deterministic backend decision-making, business-facing frontend presentation, and technical workflow inspection.

## 13. Historical Implementation — Phase 2.1 Linear Orchestration

### 13.1 Implementation

Phase 2.1 evolved the existing deterministic workflow by introducing LangGraph `StateGraph` orchestration.

The implementation added two workflow modules:

- `backend/app/services/workflow_state.py` — defines the shared state passed between workflow nodes.
- `backend/app/services/workflow_graph.py` — defines and compiles the LangGraph workflow.

The `WorkflowService` invokes the compiled graph and returns the resulting workflow context.

The original linear graph contained seven nodes:

| Execution order | LangGraph node | Responsibility |
|---:|---|---|
| 1 | `build_context` | Creates the shared workflow context. |
| 2 | `lead_intake` | Validates mandatory lead information. |
| 3 | `recency` | Evaluates lead recency. |
| 4 | `engagement` | Evaluates engagement evidence. |
| 5 | `fit_sla` | Evaluates fit and follow-up SLA conditions. |
| 6 | `priority_decision` | Applies deterministic prioritization rules. |
| 7 | `explanation_audit` | Generates the explanation and records the audit entry. |

The original graph started at `START`, followed fixed sequential edges, and terminated at `END`.

Subsequent phases introduced conditional routing and the controlled Gemini explanation enhancement.

### 13.2 Execution Tracing

Each node appends an execution-trace entry to the workflow context.

Each entry contains:

- `node` — the workflow node name.
- `status` — the execution status.

Supported statuses include `completed`, `skipped`, and `failed`.

For valid leads, all seven original nodes completed successfully.

For invalid leads, the four downstream analytical agent nodes were skipped after lead intake validation. Explanation and audit generation still took place.

### 13.3 Business Outcome Preservation

The LangGraph migration preserved the existing deterministic business rules and recommendations.

| Scenario | Expected recommendation | Priority score |
|---|---|---:|
| HOT | `FOLLOW_UP_NOW` | 95 |
| WARM | `FOLLOW_UP_SOON` | 65 |
| STALE | `NURTURE` | 0 |
| Missing mandatory contact information | `REQUEST_DATA` | 0 |

The existing API response structure and frontend integration were preserved. Execution-trace information was exposed through the workflow context.

LangGraph was responsible for orchestration, not business decision-making.

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

The historical backend test suite completed successfully with **9 passed tests**.

The local Docker Compose application was also validated, with both backend and frontend containers healthy.

### 13.5 Phase Boundary

Phase 2.1 introduced linear LangGraph orchestration without changing the underlying business logic.

Conditional routing, dynamic workflow paths, LLM-based decisions, RAG, vector databases, and MCP remained outside that phase and were reserved for later development.

Subsequent phases introduced conditional routing and controlled LLM explanation enhancement, as described in the current architecture sections.

## 14. Phase 3.1 — Productize the Business Experience

### 14.1 Objective

Phase 3.1 improves the business-facing experience of APEX by making deterministic lead prioritization results easier to understand and use.

The objective is to move beyond displaying a recommendation and score alone. The interface provides business-oriented explanatory context and a suggested next action for each recommendation outcome.

The enhancement preserves the original Phase 2 visual identity, including its dark navy and gold design.

### 14.2 Recommendation Experience

The business-facing recommendation presentation includes:

- Final recommendation label.
- Priority score and available score breakdown.
- Recommendation explanation.
- Suggested next action.
- Supporting business evidence and triggered rules.

The recommendation explanation communicates why the outcome matters to the sales team.

The suggested next action provides a practical follow-up direction based on the selected outcome.

### 14.3 Outcome Coverage

The Phase 3.1 experience covers all four recommendation outcomes:

| Outcome | Explanation purpose | Suggested action purpose |
|---|---|---|
| `FOLLOW_UP_NOW` | Communicates the need for prompt attention. | Encourages timely contact and agreement on the next step. |
| `FOLLOW_UP_SOON` | Communicates the need to keep the lead in the active queue. | Encourages scheduling a follow-up soon. |
| `NURTURE` | Communicates that continued engagement is more appropriate. | Encourages adding the lead to the nurture process. |
| `REQUEST_DATA` | Identifies missing mandatory lead information. | Encourages completion of the required information before reassessment. |

### 14.4 Technical Boundaries

Phase 3.1 is a frontend product-experience enhancement.

It does not:

- Introduce a new prioritization algorithm.
- Change agent scoring weights.
- Change deterministic recommendation precedence.
- Modify LangGraph conditional routing.
- Give Gemini authority over business decisions.
- Introduce automatic CRM updates or customer communication.
- Introduce persistent audit storage.

The existing API, agent responsibilities, and deterministic workflow remain the source of truth.

### 14.5 Business Experience Separation and Validation

The subsequent Phase 3.1 frontend correction separates the normal business-facing recommendation experience from the technical execution and audit information.

**Business-facing screen:**

- Lead information and engagement context remain visible.
- Recommendation outcome and priority remain visible.
- Recommendation explanation and business evidence remain accessible.
- Suggested next action remains visible.
- Internal agent execution details and raw JSON are not exposed in the normal view.

**Explainability & Audit:**

- The section is collapsed by default.
- Expanding it reveals run-scoped shared workflow context.
- The five-agent execution timeline and structured outputs remain available.
- LangGraph routing and execution trace remain available.
- Gemini metadata and fallback information remain available when returned by the workflow.
- Audit information and relevant raw JSON remain accessible.

**Functional validation:**

All four seeded scenarios were tested through the local application:

| Scenario | Expected recommendation | Score | Result |
|---|---|---:|---|
| HOT | `FOLLOW_UP_NOW` | 95 | Passed |
| WARM | `FOLLOW_UP_SOON` | 65 | Passed |
| STALE | `NURTURE` | 0 | Passed |
| Missing contact | `REQUEST_DATA` | 0 | Passed |

The missing-contact scenario correctly followed the mandatory-data validation path and returned `REQUEST_DATA`. It stopped after the Lead Intake Agent rather than executing the remaining analytical agents. This is the expected incomplete-input behaviour.

**Frontend validation:**

- TypeScript validation using `npx tsc --noEmit` — passed.
- Frontend production build using `npm run build` — passed.
- Docker frontend image rebuild — completed successfully.
- Local Docker Compose application — frontend and backend running and healthy.
- Normal business-facing screen separation — verified.
- Explainability & Audit expansion — verified.
- Four recommendation scenarios — verified.
- Responsive layout checks at 1440px, 768px, 390px, and 320px — completed.

The latest Explainability & Audit separation has been validated locally. Its production deployment and production verification are a separate subsequent step.

The frontend correction does not change the deterministic scoring model, recommendation rules, LangGraph routing, Gemini safeguards, backend architecture, or API decision authority.

**Phase 3.1 result:** The application presents a focused business-facing recommendation experience while retaining the complete technical workflow and audit journey for reviewers through Explainability & Audit.