# APEX — Lead Follow-up Prioritization Intelligence

**Case ID:** AA007  
**Product:** APEX — Lead Intelligence Platform  
**Domain:** Sales Operations
**Version:** 1.0.0
**Phase:** 3 — Final Demo & Portfolio Package

## 1. Overview

APEX is a deterministic, multi-agent lead prioritization application designed to help sales teams decide which leads require attention first.

It evaluates lead information, contact recency, engagement activity, declared business needs, and pending follow-up actions. It produces an explainable recommendation supported by scores, rules, and evidence.

The application combines deterministic decision-making with LangGraph conditional workflow orchestration and an optional Gemini-powered explanation layer.

**The deterministic workflow remains the authority for every lead recommendation. Gemini can improve the wording of an explanation, but it cannot change the recommendation or its score.**

## 2. Business Problem

Sales teams may receive leads from multiple sources, with different levels of engagement, contact history, and follow-up urgency.

Without a consistent prioritization process:
- Important follow-ups may be delayed.
- Sales representatives may prioritize leads inconsistently.
- Decisions may be difficult to explain or audit.
- Incomplete lead information may result in unreliable decisions.

APEX addresses this problem through structured lead evaluation and evidence-based prioritization.

## 3. Primary Users

- **Sales coordinators:** Identify leads requiring follow-up.
- **Inside sales representatives:** Understand which leads to contact first and why.
- **Sales operations leads:** Review prioritization decisions and workflow evidence.

## 4. What the Product Does

The application accepts structured lead information, evaluates it through multiple agents, and returns one of four recommendations:

| Recommendation | Meaning |
|---|---|
| `FOLLOW_UP_NOW` | Immediate follow-up is required. |
| `FOLLOW_UP_SOON` | Follow-up should happen soon. |
| `NURTURE` | Keep the lead in a longer-term engagement process. |
| `REQUEST_DATA` | Mandatory information is missing and must be supplied. |

Each result includes a priority score, recommendation, reasons, evidence, and workflow/audit information.

## 5. Architecture

APEX uses a multi-agent workflow orchestrated through LangGraph.

### Agent responsibilities

1. **Lead Intake Agent** — Validates and normalizes lead information.
2. **Recency Agent** — Evaluates lead age and last-contact recency.
3. **Engagement Agent** — Evaluates recognized engagement events.
4. **Fit & SLA Agent** — Evaluates declared business need and pending follow-up obligations.
5. **Lead Priority Decision Agent** — Combines the deterministic scoring results and applies decision rules to produce the recommendation.

### Workflow orchestration

LangGraph coordinates the agents and conditional decision routes.

The workflow includes:
- Structured workflow state.
- Sequential agent execution.
- Conditional routing for different recommendation paths.
- Explanation generation.
- Optional Gemini explanation processing.
- Explanation audit recording.

The workflow ends after the explanation and audit stages.

### Decision authority

The decision engine is deterministic. It uses approved lead evidence, weighted scoring, and explicit business rules.

Important decision conditions include:
- Overdue committed follow-up can trigger `FOLLOW_UP_NOW`.
- High fit combined with recent engagement supports higher priority.
- Low engagement and older leads can be routed to `NURTURE`.
- Missing mandatory information triggers `REQUEST_DATA`.

The same valid input and rules produce the same deterministic decision.

## 6. Key Features

- Multi-agent lead evaluation.
- Deterministic weighted scoring.
- SLA-aware follow-up prioritization.
- LangGraph conditional workflow routing.
- Four recommendation outcomes.
- Evidence-grounded explanations.
- Optional Gemini explanation enhancement.
- Deterministic fallback when Gemini is unavailable or returns an invalid response.
- Workflow trace and audit information.
- Business-facing recommendation view separated from technical explainability details.
- Responsive frontend interface.

## 7. Controlled Gemini Explanation Layer

Gemini is an optional explanation enhancement, not a decision-making agent.

The deterministic workflow first produces the recommendation and evidence. The Gemini layer receives approved decision evidence and attempts to rewrite the explanation concisely.

The integration includes safeguards:
- The recommendation and score must remain unchanged.
- The explanation must be based on supplied evidence.
- Lead identifiers are excluded from the Gemini evidence payload.
- Unsupported predictions, promises, and claims are prohibited.
- Invalid responses, provider errors, timeouts, or missing configuration trigger deterministic fallback.

If Gemini is unavailable, the application retains the original deterministic explanation.

## 8. Demo Scenarios

The following scenarios demonstrate the application's decision paths.

| Scenario | Input condition | Expected recommendation |
|---|---|---|
| A — Hot lead | Recent inquiry, strong fit, overdue follow-up | `FOLLOW_UP_NOW` |
| B — Warm lead | Moderate engagement and valid declared need | `FOLLOW_UP_SOON` |
| C — Stale lead | Older lead with no recognized engagement | `NURTURE` |
| D — Incomplete lead | Missing mandatory contact information | `REQUEST_DATA` |

Scenarios A, B, and C are provided through the seeded scenario API. Scenario D demonstrates the missing-data route using an incomplete lead record.

The actual score and explanation are generated by the workflow at execution time.

## 9. Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI |
| Workflow orchestration | LangGraph |
| LLM explanation | Google Gemini API, `google-genai` SDK |
| Frontend | React, TypeScript, Vite |
| Web server / reverse proxy | Nginx |
| Testing | Pytest |
| Containerization | Docker, Docker Compose |
| Cloud deployment | Render |

## 10. Running Locally

### Prerequisites

- Python 3.11
- Node.js and npm
- Docker and Docker Compose (for containerized execution)

### Backend

From the repository root:

```bash
cd backend
```

Create and activate a virtual environment if one does not already exist.

Install the backend dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8002
```

### Frontend

Open another terminal from the repository root:

```bash
cd frontend
npm install
npm run dev
```

The Vite development server uses the frontend development configuration to proxy API requests to the local backend.

### Docker Compose

From the repository root:

```bash
docker compose up --build
```

The containerized frontend is served on port `8080`. The backend is exposed on port `8002`.

Use the application URL:

```text
http://localhost:8080
```

## 11. Cloud Deployment

The application is deployed using Render.

**Frontend:**
https://aa007-frontend.onrender.com

**Backend:**
https://aa007-backend.onrender.com

The frontend uses Nginx to forward `/api/` requests to the backend through the `BACKEND_URL` environment variable.

The deployed configuration was verified:
- Backend scenario API responds successfully.
- Frontend proxy forwards requests successfully.
- The deployed dashboard loads and works.
- All four application scenarios were verified.

## 12. Testing and Validation

Backend automated tests were executed using the project's Python 3.11.9 virtual environment.

**Latest verified result:**

```text
17 passed in 1.53s
```

Test coverage includes:
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

The deployed frontend, backend API, and frontend-to-backend proxy were also manually verified.

## 13. Product Evolution

The project evolved through three main implementation stages:

1. **Deterministic foundation:** Structured lead inputs, agent responsibilities, weighted scoring, business rules, and explainable recommendations.
2. **LangGraph orchestration:** Multi-agent workflow execution, shared workflow state, and conditional routing for different decision paths.
3. **Controlled LLM enhancement:** Optional Gemini-generated explanation wording, validation safeguards, and deterministic fallback.

Across these stages, the deterministic decision engine remains the source of truth.

## 14. Limitations and Non-Goals

APEX is an internship MVP and demonstration application.

It is not intended to:
- Autonomously contact customers.
- Negotiate pricing or contracts.
- Make decisions using sensitive demographic characteristics.
- Replace human sales judgment.
- Guarantee AI explanation accuracy.
- Claim production readiness or enterprise integration.

The application uses structured sample scenarios for demonstration. Real-world deployment would require appropriate data governance, security controls, operational monitoring, and integration validation.

## 15. Future Improvements

Potential future improvements include:
- Integration with approved CRM systems.
- Persistent audit storage.
- Expanded lead datasets and evaluation.
- User authentication and role-based access.
- Operational monitoring and workflow performance metrics.
- Additional configurable sales prioritization rules.

## 16. Repository

GitHub:
https://github.com/parvathycr28/AA007-Lead-Follow-up-Intelligence

---

**AA007 — APEX Lead Intelligence Platform**

An explainable, deterministic-first, multi-agent approach to lead follow-up prioritization.