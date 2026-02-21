from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from engine.api.events import router as events_router
from engine.api.alerts import router as alerts_router
from engine.api.activity import router as activity_router
from engine.api.admin import router as admin_router
from engine.api.dashboard import router as dashboard_router
from engine.db import init_db

app = FastAPI(
    title="Threat Detection Engine",
    description="Ingest activity events, run PSI/ML/XAI, store results and serve alerts and activity to the dashboard.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(activity_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "service": "Threat Detection Engine",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1",
    }


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}
