# APEX — Lead Follow-up Prioritization Intelligence

**Case ID:** AA007  
**Assignment:** Lead Follow-up Prioritization Intelligence  
**Domain:** Sales Operations  
**Product:** APEX — Lead Intelligence Platform  
**Product Version:** 1.0.0  
**Current Phase:** Phase 3.1 — Business Recommendation Experience

## 1. Overview

APEX is a deterministic, multi-agent application that helps sales teams prioritize lead follow-up activities using structured business evidence.

The system evaluates lead recency, engagement, declared business need, and pending follow-up commitments. It produces transparent recommendations, supporting reasons, evidence, and audit references.

Five specialized agents are orchestrated through a LangGraph `StateGraph` with deterministic conditional routing. The graph manages execution order and shared workflow state, while the agents retain responsibility for deterministic validation, scoring, and business decisions.

An optional, controlled Google Gemini service enhances the readability of the deterministic explanation. Gemini receives structured decision evidence, not the lead identifier, and cannot change the recommendation, priority score, or business rules. If the provider is unavailable or its response fails validation, the application retains the original deterministic explanation.

Phase 3.1 improves the frontend recommendation experience by providing clearer explanations and suggested next actions for all four recommendation outcomes.

The application uses seeded sample lead records. It does not connect to a live CRM, contact customers, or make autonomous external business decisions.

## 2. Business Problem

Sales teams need a consistent way to identify which leads require immediate attention, which can be followed up soon, and which should remain in a nurture process.

Manual prioritization can be inconsistent and difficult to audit.

APEX addresses this problem through a structured workflow with five specialized agents and deterministic decision rules. The frontend presents the resulting recommendation with supporting context and a suggested next action.

## 3. Recommendations

The system supports four recommendation types:

| Recommendation | Meaning |
|---|---|
| `FOLLOW_UP_NOW` | Immediate follow-up is recommended. |
| `FOLLOW_UP_SOON` | Follow-up should be scheduled soon. |
| `NURTURE` | Continue the lead nurturing process. |
| `REQUEST_DATA` | Mandatory lead information is missing or invalid. |

Each completed workflow provides a priority score, score breakdown, triggered business rules, explanation, and audit reference.

### Phase 3.1 — Recommendation Experience

Phase 3.1 improves how the application communicates its deterministic recommendations.

The frontend provides:

- A recommendation explanation that gives users additional context about the outcome.
- A suggested next action that helps users understand the appropriate operational response.
- Consistent presentation across all four recommendation types.
- The existing priority score, evidence, agent outputs, and audit information.

The suggested actions are guidance for the sales team. They do not trigger automatic customer communication or external actions.

| Recommendation | Suggested operational response |
|---|---|
| `FOLLOW_UP_NOW` | Contact the lead as soon as practical and agree on the next step. |
| `FOLLOW_UP_SOON` | Schedule a follow-up within the team's normal response window. |
| `NURTURE` | Add the lead to the appropriate nurture queue and plan a future review. |
| `REQUEST_DATA` | Obtain the missing mandatory information before reassessing the lead. |

## 4. Multi-Agent Architecture

The workflow consists of five specialized agents:

1. **Lead Intake Agent** — validates and normalizes lead information.
2. **Recency Agent** — evaluates lead age and last-contact recency.
3. **Engagement Agent** — scores approved business engagement events.
4. **Fit & SLA Agent** — evaluates declared business need and pending follow-up commitments.
5. **Lead Priority Decision Agent** — combines agent outputs and applies deterministic decision rules.

### LangGraph Orchestration

The five specialized agents are orchestrated through a LangGraph `StateGraph` using deterministic conditional routing. The graph uses shared workflow state and selects different execution paths based on mandatory-data validation and the deterministic priority decision.

The workflow includes these core processing nodes:

1. `build_context` — initializes the shared workflow context.
2. `lead_intake` — validates and normalizes mandatory lead information.
3. `recency` — evaluates lead age and last-contact recency.
4. `engagement` — scores approved business engagement events.
5. `fit_sla` — evaluates declared business need and pending follow-up commitments.
6. `priority_decision` — calculates the deterministic recommendation.
7. `explanation_audit` — generates the explanation and audit information for every outcome path.

**Conditional routing after Lead Intake:**

- Valid mandatory data → continue to `recency` and the analytical agents.
- Missing mandatory data → `request_data` route, producing `REQUEST_DATA`.
- Intake execution failure → `workflow_error` route.

**Conditional routing after Priority Decision:**

- `OVERDUE_FOLLOW_UP` → `overdue_follow_up` route.
- `HIGH_PRIORITY_SCORE` → `high_priority` route.
- `MODERATE_PRIORITY_SCORE` → `follow_up_soon` route.
- `LOW_PRIORITY_SCORE` → `nurture` route.
- Agent execution failure or an unidentified priority route → `workflow_error` route.

Each router records its selected route and triggering condition in the execution trace. The selected outcome node then leads to the shared `explanation_audit` node, ensuring that explanations and audit information are generated across the different paths.

The audit record preserves a copy of the complete execution trace, including node execution statuses, selected routes, routing conditions, and the final `explanation_audit` completion entry.

LangGraph manages conditional orchestration and shared state. All validation, scoring, recommendation selection, and business rules remain deterministic; routing does not delegate business decisions to an LLM.

### Controlled LLM Enhancement — Post 2.3

The workflow includes an optional Google Gemini enhancement after the deterministic explanation is generated and before the final audit is recorded.

**Processing sequence:**

1. The deterministic agents validate lead information and calculate the recommendation.
2. LangGraph selects the appropriate conditional execution path.
3. The deterministic priority decision establishes the recommendation and score.
4. `build_explanation` generates the original evidence-based explanation.
5. `gemini_explanation` optionally rewrites the explanation into a concise, readable summary.
6. The response is validated before it is accepted.
7. `explanation_audit` records the complete execution trace.

**LLM boundaries and safeguards:**

- Gemini only improves the readability of an existing explanation.
- The deterministic recommendation and priority score remain authoritative.
- Only structured decision evidence is sent to Gemini; the lead identifier is excluded.
- The response must preserve the exact recommendation action and priority score.
- Responses exceeding the configured length limit or containing multiple lines are rejected.
- Provider errors, timeouts, missing configuration, and invalid responses trigger deterministic fallback.
- No autonomous customer contact or LLM-based business decisions are performed.

**Configuration:**

The optional service is configured through environment variables:

| Variable | Purpose |
|---|---|
| `LLM_PROVIDER` | LLM provider (`gemini`). |
| `GEMINI_API_KEY` | Google Gemini API key. |
| `GEMINI_MODEL` | Configured Gemini model. |
| `LLM_TIMEOUT` | Provider request timeout in seconds. |

The API key is stored locally in `backend/.env` and must never be committed. `backend/.env.example` contains placeholder configuration.

**Execution trace and audit:**

The `gemini_explanation` trace entry records the provider, model, execution status, and reason. The audit record preserves this entry along with the rest of the workflow trace.

If Gemini is unavailable or returns an invalid response, the original deterministic explanation is retained.

The LLM does not control validation, scoring, routing, recommendation selection, or business rules.

## 5. Deterministic Decision Logic

The current MVP uses provisional scoring assumptions:

- Recency: up to 30 points.
- Engagement: up to 40 points.
- Declared business need: up to 30 points.
- Total priority score: 100 points.

Current decision precedence:

1. Missing or invalid mandatory information → `REQUEST_DATA`.
2. Overdue committed follow-up → `FOLLOW_UP_NOW`.
3. Score of 70 or above → `FOLLOW_UP_NOW`.
4. Score of 40 or above → `FOLLOW_UP_SOON`.
5. Otherwise → `NURTURE`.

These weights, thresholds, and rules are provisional implementation assumptions for the MVP, not externally validated sales benchmarks.

## 6. Sample Scenarios

The application includes seeded sample scenarios for demonstrating the recommendation workflow.

| Scenario | Expected recommendation | Expected score |
|---|---|---:|
| Hot | `FOLLOW_UP_NOW` | 95 |
| Warm | `FOLLOW_UP_SOON` | 65 |
| Stale | `NURTURE` | 0 |
| Missing contact information | `REQUEST_DATA` | 0 |

These are illustrative sample records, not live customer data.

## 7. Technology Stack

**Backend**

- Python 3.11
- FastAPI
- Pydantic
- LangGraph (`StateGraph` conditional routing)
- Pytest
- Google Gemini integration (optional explanation enhancement)

**Frontend**

- React
- TypeScript
- Vite
- CSS

**Containerization and Deployment**

- Docker
- Docker Compose
- Nginx (frontend static hosting and API reverse proxy)
- Render (cloud deployment)

## 8. Project Structure

```text
AA007-Lead-Follow-up-Prioritization-Intelligence/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── api/
│   │   ├── data/
│   │   ├── models/
│   │   ├── rules/
│   │   └── services/
│   │       ├── workflow_service.py
│   │       ├── workflow_graph.py
│   │       └── workflow_state.py
│   ├── tests/
│   ├── .dockerignore
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   ├── .dockerignore
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── vite.config.ts
├── docs/
│   └── architecture.md
├── docker-compose.yml
├── .gitignore
└── README.md
```

The backend workflow modules are:

- `workflow_service.py` — invokes the compiled LangGraph workflow.
- `workflow_graph.py` — defines the conditional-routing StateGraph and its outcome paths.
- `workflow_state.py` — defines the shared state passed between graph nodes.

## 9. Run Locally

### Backend

From the repository root:

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8002
```

Backend health endpoint:

`http://127.0.0.1:8002/api/assistant/health`

Interactive API documentation:

`http://127.0.0.1:8002/docs`

### Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev -- --port 5174
```

Open the application:

`http://localhost:5174`

The Vite development server proxies `/api` requests to the backend on port 8002.

### Dockerized Local Run (Phase 1.3)

The application can also run locally as two Docker containers using Docker Compose.

**Container architecture:**

- **Backend:** Python 3.11, FastAPI and Uvicorn, listening on port `8002` inside the container.
- **Frontend:** React production build served by Nginx.
- **API communication:** Nginx forwards frontend `/api/` requests to the backend service at `http://backend:8002`.
- **Frontend access:** `http://localhost:8080`.
- **Health checks:** Docker Compose checks backend and frontend health. The frontend starts after the backend becomes healthy.

Run these commands from the repository root:

```bash
docker compose config
docker compose build
docker compose up -d
docker compose ps
```

Open the containerized application:

`http://localhost:8080`

To rebuild and restart after code changes:

```bash
docker compose up -d --build
```

To stop the AA007 containers:

```bash
docker compose down
```

### Render Cloud Deployment (Phase 1.4)

The APEX application is deployed on Render using two separate Docker-based Web Services.

**Public application URLs:**

- **Frontend:** https://aa007-frontend.onrender.com
- **Backend:** https://aa007-backend.onrender.com
- **Backend health:** https://aa007-backend.onrender.com/api/assistant/health

**Deployment architecture:**

- **Frontend service:** React production build served through Nginx.
- **Backend service:** FastAPI application served by Uvicorn on port `8002`.
- **Cloud platform:** Render Docker Web Services.
- **Region:** Singapore.
- **Instance type:** Free tier for both services.
- **Source repository:** GitHub `main` branch.

**Frontend environment configuration:**

The frontend Render service uses the following environment variable:

| Variable | Value |
|---|---|
| `BACKEND_URL` | `https://aa007-backend.onrender.com` |

Nginx uses this variable to forward browser requests under `/api/` to the backend service. This preserves the frontend's same-origin API request pattern without requiring a separate browser-to-backend CORS configuration.

**Deployment validation:**

The deployed application was checked after the Phase 3.1 changes.

- Public frontend loaded successfully.
- Updated recommendation interface was visible.
- Backend health endpoint was available.
- All four seeded scenarios were exercised through the deployed frontend.
- The four recommendation outcomes were returned as expected.

**Operational limitations:**

- Render free services may spin down after inactivity, resulting in a delay during the first request.
- Audit records, including their complete execution traces, remain in process-local memory. They are not durable and may be lost when the backend restarts.
- No persistent database or external audit storage has been configured.
- The Gemini API key is configured securely as a backend environment secret in Render. It is not committed to GitHub.
- The local `backend/.env` file is excluded from Git, and `backend/.env.example` contains placeholder values only.

## 10. API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/assistant/health` | Backend health check |
| GET | `/api/leads/scenarios` | List seeded scenarios |
| POST | `/api/leads/prioritize` | Prioritize a supplied lead |
| POST | `/api/leads/scenarios/{scenario_name}/run` | Execute a seeded scenario |

## 11. Testing and Validation

### Automated and Frontend Validation

The following Phase 3.1 frontend validation was completed:

- TypeScript validation using `npx tsc --noEmit` — passed.
- Frontend production build using `npm run build` — passed.
- Docker frontend image rebuild — completed successfully.
- Local Docker application — frontend and backend running.
- Production Render application — updated interface verified.

The previously documented backend automated test result was 17 passed during Phase 2.3. This historical result should not be interpreted as a newly executed Phase 3.1 backend test run.

### Phase 3.1 Scenario Validation

All four scenarios were tested through the local application and the deployed Render frontend.

| Scenario | Expected recommendation | Score | Result |
|---|---|---:|---|
| HOT | `FOLLOW_UP_NOW` | 95 | Passed |
| WARM | `FOLLOW_UP_SOON` | 65 | Passed |
| STALE | `NURTURE` | 0 | Passed |
| Missing contact | `REQUEST_DATA` | 0 | Passed |

The HOT, WARM, and STALE scenarios completed the normal analytical workflow.

The missing-contact scenario correctly followed the mandatory-data validation path and returned `REQUEST_DATA`. It stopped after the Lead Intake Agent rather than executing the remaining analytical agents. This is the expected incomplete-input behavior.

The application displayed the corresponding recommendation explanations and suggested next actions.

### Docker Validation (Phase 1.3)

The application was built and validated using Docker Compose.

**Container status:**

- `aa007-backend` — running and healthy.
- `aa007-frontend` — running and healthy.
- Frontend published on host port `8080`.

**Health and API checks:**

| Check | Result |
|---|---|
| Frontend health (`/health`) | Passed |
| Backend health (`/api/assistant/health`) through Nginx | Passed |
| Scenario listing API | Passed |
| Frontend-to-backend communication | Passed |

Audit records are stored in process memory and are not persistent across backend container restarts.

## 12. Scope and Limitations

### Current Phase 3.1 Capabilities

- Uses seeded sample data rather than a live CRM integration.
- Uses five specialized deterministic agents for lead validation, analysis, and prioritization.
- Uses LangGraph conditional routing based on mandatory-data validation and deterministic priority rules.
- Preserves deterministic recommendation selection, scoring, and business rules.
- Uses Google Gemini as an optional, controlled explanation-enhancement service.
- Validates LLM output and falls back to the original deterministic explanation on provider errors, timeouts, missing configuration, or invalid responses.
- Records workflow execution, routing decisions, and Gemini provider/model/status/reason in the execution trace and audit record.
- Presents clearer recommendation explanations and suggested next actions for all four recommendation outcomes.
- Supports local Docker-based execution and cloud deployment on Render.
- Does not automatically send messages or contact leads.

### Out of Scope

- Dynamic agent selection beyond the defined deterministic workflow routes.
- LLM-based business decisions.
- Retrieval-Augmented Generation (RAG).
- Vector databases.
- Model Context Protocol (MCP).
- Live CRM integration.
- Automatic customer communication.

### Operational Limitations

- Audit records are held in process-local memory and are not durable across backend restarts or service replacement.
- Scoring weights and thresholds are provisional MVP assumptions.
- Recommendations support operational prioritization and are not guaranteed sales outcomes.
- Sensitive personal profiling is excluded.
- The application uses seeded sample scenarios and is not a production CRM integration.

## 13. Project Objective

The objective is to demonstrate a transparent, explainable, and testable multi-agent workflow for Lead Follow-up Prioritization Intelligence.

The application combines five specialized deterministic agents, shared workflow context, LangGraph conditional routing, structured agent outputs, execution tracing, deterministic decision evidence, explanations, and auditability.

The controlled Gemini enhancement introduced in Post 2.3 improves explanation readability while keeping deterministic business decisions authoritative.

Phase 3.1 builds on this foundation by improving the business recommendation experience. Users receive clearer explanations and suggested next actions for each recommendation outcome, while the underlying deterministic workflow and API behavior remain unchanged.

The project demonstrates the design, implementation, testing, local Docker validation, and Render deployment of a deterministic multi-agent lead prioritization application.