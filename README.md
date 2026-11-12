# APEX — Lead Follow-up Prioritization Intelligence

**Case ID:** AA007
**Assignment:** Lead Follow-up Prioritization Intelligence
**Domain:** Sales Operations
**Product:** APEX — Lead Intelligence Platform
**Version:** 1.0.0
**Current Phase:** 2.1 — LangGraph Linear Orchestration

## 1. Overview

APEX is a deterministic, multi-agent application that helps sales teams prioritize lead follow-up activities using structured business evidence.

The system evaluates lead recency, engagement, declared business need, and pending follow-up commitments. It produces transparent recommendations, supporting reasons, evidence, and audit references.

The existing five specialized agents are orchestrated through a LangGraph linear StateGraph workflow. The graph manages execution order and shared workflow state, while the agents retain responsibility for deterministic validation, scoring, and business decisions.

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

1. **Lead Intake Agent** — validates and normalizes lead information.
2. **Recency Agent** — evaluates lead age and last-contact recency.
3. **Engagement Agent** — scores approved business engagement events.
4. **Fit & SLA Agent** — evaluates declared business need and pending follow-up commitments.
5. **Lead Priority Decision Agent** — combines agent outputs and applies deterministic decision rules.

### LangGraph Orchestration — Phase 2.1

The agents are orchestrated through a LangGraph `StateGraph` using a fixed linear sequence of seven workflow nodes:

1. `build_context`
2. `lead_intake`
3. `recency`
4. `engagement`
5. `fit_sla`
6. `priority_decision`
7. `explanation_audit`

A run-scoped shared workflow context carries lead data, agent outputs, recommendations, explanations, and audit information between nodes.

Each node records its name and execution status in the workflow execution trace.

For valid leads, all seven nodes execute in sequence. For invalid leads, the four downstream analytical agent nodes are skipped, while explanation and audit generation still take place.

LangGraph manages orchestration and shared state. It does not replace the existing deterministic business rules or make independent business decisions.

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
- LangGraph (`StateGraph` linear orchestration)
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
- `workflow_graph.py` — defines the seven-node linear StateGraph.
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
- Audit records remain in process-local memory. They are not durable and may be lost when the backend restarts.
- No persistent database or external audit storage has been configured.
- No application secrets are required for the current deployment.

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

- Backend: 9 tests passed.
- Frontend production build: passed.
- Frontend ESLint: passed.
- Hot, warm, and stale scenarios: manually tested successfully through the frontend.
- Responsive layouts: verified at desktop, tablet, and mobile sizes.

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

**Result:** 9 passed, 1 non-blocking deprecation warning.

**Audit limitation:** Audit records are stored in process memory and are not persistent across backend container restarts.

## 12. Scope and Limitations

### Current Phase 2.1 Capabilities

- Uses seeded sample data rather than a live CRM integration.
- Uses deterministic business rules for lead prioritization.
- Uses LangGraph for fixed linear workflow orchestration.
- Records workflow node execution order and status through execution tracing.
- Preserves the existing five specialized agents and their business logic.
- Does not automatically send messages or contact leads.

### Out of Scope

- Conditional workflow routing and dynamic agent selection.
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

The application combines five specialized deterministic agents, shared workflow context, LangGraph linear orchestration, structured agent outputs, execution tracing, deterministic decision evidence, explanations, and auditability.

Phase 2.1 evolves the existing workflow orchestration without changing established business rules, recommendations, or frontend and API integration.

The project also demonstrates local Docker-based validation and cloud deployment on Render as part of the AA007 development journey.