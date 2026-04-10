import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from engine.api.events import router as events_router
from engine.api.alerts import router as alerts_router
from engine.api.activity import router as activity_router
from engine.api.admin import router as admin_router
from engine.api.dashboard import router as dashboard_router
from engine.config import get_settings
from engine.db import init_db

_settings = get_settings()
logging.basicConfig(
    level=getattr(logging, _settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("engine.api")

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


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    client = request.client.host if request.client else "unknown"
    logger.info(
        "→ %s %s from %s",
        request.method,
        request.url.path,
        client,
        extra={"query": str(request.query_params) or None},
    )
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "← %s %s %d (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


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
