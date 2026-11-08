from fastapi import FastAPI

from app.api.routes.leads import router as leads_router


app = FastAPI(
    title="AA007 - Lead Follow-up Prioritization Intelligence",
    description="Deterministic Agentic AI MVP for prioritizing sales lead follow-ups.",
    version="1.0.0",
)


@app.get("/api/assistant/health")
def health_check():
    return {
        "status": "healthy",
        "application": "AA007 Lead Follow-up Prioritization Intelligence",
        "version": "1.0.0",
    }


app.include_router(leads_router)