# APEX â€” Lead Follow-up Prioritization Intelligence

**Case ID:** AA007
**Assignment:** Lead Follow-up Prioritization Intelligence
**Domain:** Sales Operations
**Product:** APEX â€” Lead Intelligence Platform
**Version:** 1.0.0
**Current Phase:** Post 2.3 â€” Controlled LLM Enhancement

## 1. Overview

APEX is a deterministic, multi-agent application that helps sales teams prioritize lead follow-up activities using structured business evidence.

The system evaluates lead recency, engagement, declared business need, and pending follow-up commitments. It produces transparent recommendations, supporting reasons, evidence, and audit references.

The existing five specialized agents are orchestrated through a LangGraph StateGraph with deterministic conditional routing. The graph manages execution order and shared workflow state, while the agents retain responsibility for deterministic validation, scoring, and business decisions.

An optional, controlled Google Gemini service enhances the readability of the deterministic explanation. Gemini receives structured decision evidence, not the lead identifier, and cannot change the recommendation, priority score, or business rules. If the provider is unavailable or its response fails validation, the application retains the original deterministic explanation.

The application uses seeded sample lead records. It does not connect to a live CRM, contact customers, or make autonomous external business decisions.

## 2. Business Problem

Sales teams need a consistent way to identify which leads require immediate attention, which can be followed up soon, and which should remain in a nurture process.

Manual prioritization can be inconsistent and difficult to audit.

APEX addresses this problem through a structured workflow with five specialized agents and deterministic decision rules.

## 3. Recommendations

The system supports four recommendation types:

| Recommendation | Meaning |
|---|---|
| `FOLLOW_UP_NOW` | Immediate follow-up is recommended. |
| `FOLLOW_UP_SOON` | Follow-up should be scheduled soon. |
| `NURTURE` | Continue the lead nurturing process. |
| `REQUEST_DATA` | Mandatory lead information is missing or invalid. |

Each completed workflow provides a priority score, score breakdown, triggered business rules, explanation, and audit reference.

## 4. Multi-Agent Architecture

The workflow consists of five specialized agents:

1. **Lead Intake Agent** â€” validates and normalizes lead information.
2. **Recency Agent** â€” evaluates lead age and last-contact recency.
3. **Engagement Agent** â€” scores approved business engagement events.
4. **Fit & SLA Agent** â€” evaluates declared business need and pending follow-up commitments.
5. **Lead Priority Decision Agent** â€” combines agent outputs and applies deterministic decision rules.

### LangGraph Orchestration â€” Phase 2.2

The five specialized agents are orchestrated through a LangGraph `StateGraph` using deterministic conditional routing. The graph uses shared workflow state and selects different execution paths based on mandatory-data validation and the deterministic priority decision.

The workflow includes these core processing nodes:

1. `build_context` â€” initializes the shared workflow context.
2. `lead_intake` â€” validates and normalizes mandatory lead information.
3. `recency` â€” evaluates lead age and last-contact recency.
4. `engagement` â€” scores approved business engagement events.
5. `fit_sla` â€” evaluates declared business need and pending follow-up commitments.
6. `priority_decision` â€” calculates the deterministic recommendation.
7. `explanation_audit` â€” generates the explanation and audit information for every outcome path.

**Conditional routing after Lead Intake:**

- Valid mandatory data â†’ continue to `recency` and the analytical agents.
- Missing mandatory data â†’ `request_data` route, producing `REQUEST_DATA`.
- Intake execution failure â†’ `workflow_error` route.

**Conditional routing after Priority Decision:**

- `OVERDUE_FOLLOW_UP` â†’ `overdue_follow_up` route.
- `HIGH_PRIORITY_SCORE` â†’ `high_priority` route.
- `MODERATE_PRIORITY_SCORE` â†’ `follow_up_soon` route.
- `LOW_PRIORITY_SCORE` â†’ `nurture` route.
- Agent execution failure or an unidentified priority route â†’ `workflow_error` route.

Each router records its selected route and triggering condition in the execution trace. The selected outcome node then leads to the shared `explanation_audit` node, ensuring that explanations and audit information are generated across the different paths.

The audit record preserves a copy of the complete execution trace, including node execution statuses, selected routes, routing conditions, and the final `explanation_audit` completion entry.

LangGraph manages conditional orchestration and shared state. All validation, scoring, recommendation selection, and business rules remain deterministic; routing does not delegate business decisions to an LLM.

### Controlled LLM Enhancement â€” Post 2.3

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

1. Missing or invalid mandatory information â†’ `REQUEST_DATA`.
2. Overdue committed follow-up â†’ `FOLLOW_UP_NOW`.
3. Score of 70 or above â†’ `FOLLOW_UP_NOW`.
4. Score of 40 or above â†’ `FOLLOW_UP_SOON`.
5. Otherwise â†’ `NURTURE`.

These weights, thresholds, and rules are provisional implementation assumptions for the MVP, not externally validated sales benchmarks.

## 6. Sample Scenarios

| Scenario | Expected recommendation | Expected score |
|---|---|---:|
| Hot | `FOLLOW_UP_NOW` | 95 |
| Warm | `FOLLOW_UP_SOON` | 65 |
| Stale | `NURTURE` | 0 |

These are illustrative sample records, not live customer data.

## 7. Technology Stack

**Backend**
- Python 3.11
- FastAPI
- Pydantic
- LangGraph (`StateGraph` conditional routing)
- Pytest

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
â”œâ”€â”€ backend/
â”‚   â”œâ”€â”€ app/
â”‚   â”‚   â”œâ”€â”€ agents/
â”‚   â”‚   â”œâ”€â”€ api/
â”‚   â”‚   â”œâ”€â”€ data/
â”‚   â”‚   â”œâ”€â”€ models/
â”‚   â”‚   â”œâ”€â”€ rules/
â”‚   â”‚   â””â”€â”€ services/
â”‚   â”‚       â”œâ”€â”€ workflow_service.py
â”‚   â”‚       â”œâ”€â”€ workflow_graph.py
â”‚   â”‚       â””â”€â”€ workflow_state.py
â”‚   â”œâ”€â”€ tests/
â”‚   â”œâ”€â”€ .dockerignore
â”‚   â”œâ”€â”€ Dockerfile
â”‚   â””â”€â”€ requirements.txt
â”œâ”€â”€ frontend/
â”‚   â”œâ”€â”€ public/
â”‚   â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ .dockerignore
â”‚   â”œâ”€â”€ Dockerfile
â”‚   â”œâ”€â”€ nginx.conf
â”‚   â”œâ”€â”€ package.json
â”‚   â””â”€â”€ vite.config.ts
â”œâ”€â”€ docs/
â”‚   â””â”€â”€ architecture.md
â”œâ”€â”€ docker-compose.yml
â”œâ”€â”€ .gitignore
â””â”€â”€ README.md
```

The backend workflow modules are:

- `workflow_service.py` â€” invokes the compiled LangGraph workflow.
- `workflow_graph.py` â€” defines the conditional-routing StateGraph and its outcome paths.
- `workflow_state.py` â€” defines the shared state passed between graph nodes.

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

| Check | Result |
|---|---|
| Public frontend URL | Passed |
| Frontend static assets | Passed |
| Direct backend health endpoint | Passed |
| Backend health through frontend proxy | Passed |
| Scenario listing and frontend loading | Passed |
| Render deployment status | Live |

The public backend health endpoint returned:

`{"status":"healthy","application":"AA007 Lead Follow-up Prioritization Intelligence","version":"1.0.0"}`

**Operational limitations:**

- Render free services may spin down after inactivity, resulting in a delay during the first request.
- Audit records, including their complete execution traces, remain in process-local memory. They are not durable and may be lost when the backend restarts.
- No persistent database or external audit storage has been configured.
- The Gemini API key is configured securely as a backend environment secret in Render. It is not committed to GitHub. The local `backend/.env` file is excluded from Git, and `backend/.env.example` contains placeholder values only.

## 10. API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/assistant/health` | Backend health check |
| GET | `/api/leads/scenarios` | List seeded scenarios |
| POST | `/api/leads/prioritize` | Prioritize a supplied lead |
| POST | `/api/leads/scenarios/{scenario_name}/run` | Execute a seeded scenario |

## 11. Testing

Backend tests:

```bash
cd backend
python -m pytest -v
```

Frontend production build:

```bash
cd frontend
npm run build
```

Frontend lint:

```bash
cd frontend
npm run lint
```

Current validation results:

- Backend: 17 tests passed (Phase 2.3).
- Frontend production build: passed.
- Frontend ESLint: passed.
- Hot, warm, and stale scenarios: manually tested successfully through the frontend.
- Responsive layouts: verified at desktop, tablet, and mobile sizes.

### Docker Validation (Phase 1.3)

The application was built and validated using Docker Compose.

**Container status:**
- `aa007-backend` â€” running and healthy.
- `aa007-frontend` â€” running and healthy.
- Frontend published on host port `8080`.

**Health and API checks:**

| Check | Result |
|---|---|
| Frontend health (`/health`) | Passed |
| Backend health (`/api/assistant/health`) through Nginx | Passed |
| Scenario listing API | Passed |
| Frontend-to-backend communication | Passed |

**End-to-end scenario results:**

| Scenario | Expected recommendation | Score | Result |
|---|---|---:|---|
| HOT | FOLLOW_UP_NOW | 95 | Passed |
| WARM | FOLLOW_UP_SOON | 65 | Passed |
| STALE | NURTURE | 0 | Passed |
| Missing contact | REQUEST_DATA | 0 | Passed |

The scenario responses included workflow context, agent execution outputs, explanations, and audit records. The seeded scenarios executed all five agents. The missing-contact scenario correctly stopped after Lead Intake Agent and skipped the remaining four agents.

Backend automated tests were also run locally:

`python -m pytest -q`

**Result:** 17 passed (current Phase 2.3 backend test suite).

**Audit limitation:** Audit records are stored in process memory and are not persistent across backend container restarts.

## 12. Scope and Limitations

### Current Post 2.3 Capabilities

- Uses seeded sample data rather than a live CRM integration.
- Uses five specialized deterministic agents for lead validation, analysis, and prioritization.
- Uses LangGraph conditional routing based on mandatory-data validation and deterministic priority rules.
- Preserves deterministic recommendation selection, scoring, and business rules.
- Uses Google Gemini as an optional, controlled explanation-enhancement service.
- Validates LLM output and falls back to the original deterministic explanation on provider errors, timeouts, missing configuration, or invalid responses.
- Records workflow execution, routing decisions, and Gemini provider/model/status/reason in the execution trace and audit record.
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

## 13. Project Objective

The objective is to demonstrate a transparent, explainable, and testable multi-agent workflow for Lead Follow-up Prioritization Intelligence.

The application combines five specialized deterministic agents, shared workflow context, LangGraph conditional routing, structured agent outputs, execution tracing, deterministic decision evidence, explanations, and auditability.

Post 2.3 builds on the deterministic multi-agent and LangGraph conditional-routing workflow by introducing a controlled, fallback-safe Gemini explanation enhancement. Deterministic business decisions remain authoritative, while the existing frontend and API integration are preserved.

The project also demonstrates local Docker-based validation and cloud deployment on Render as part of the AA007 development journey.
