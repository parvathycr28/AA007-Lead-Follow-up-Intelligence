# APEX — Lead Follow-up Prioritization Intelligence

**Case ID:** AA007
**Assignment:** Lead Follow-up Prioritization Intelligence
**Domain:** Sales Operations
**Product:** APEX — Lead Intelligence Platform
**Version:** 1.0.0
**Current Phase:** 1.2 — Explain & Visualize Your Agent Workflow

## 1. Overview

APEX is a deterministic, multi-agent MVP that helps sales teams prioritize lead follow-up activities using structured business evidence.

The system evaluates lead recency, engagement, declared business need, and pending follow-up commitments. It produces a transparent recommendation, supporting reasons, evidence, and an audit reference.

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

A run-scoped workflow context carries the lead data, agent outputs, recommendation, explanation, and audit information.

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
- Pytest

**Frontend**
- React
- TypeScript
- Vite
- CSS

## 8. Project Structure

```text
AA007-Lead-Follow-up-Intelligence/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── api/
│   │   ├── data/
│   │   ├── models/
│   │   ├── rules/
│   │   └── services/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── docs/
├── .gitignore
└── README.md
```

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

## 12. Scope and Limitations

- Uses seeded sample data rather than a live CRM integration.
- Uses deterministic business rules; no LLM-based decisions.
- Does not use LangGraph, RAG, vector databases, or external agent orchestration.
- Does not automatically send messages or contact leads.
- Audit records are held in process-local memory and are not persistent across backend restarts.
- Scoring weights and thresholds are provisional MVP assumptions.
- Recommendations support operational prioritization and are not guaranteed sales outcomes.
- Sensitive personal profiling is excluded.

## 13. Project Objective

Demonstrate a transparent, explainable, testable multi-agent workflow for Lead Follow-up Prioritization Intelligence, including run-scoped shared workflow context, structured agent outputs, deterministic decision evidence, explanations, and auditability within the AA007 Phase 1.2 scope.