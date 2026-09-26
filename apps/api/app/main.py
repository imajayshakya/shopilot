"""Shopilot API — Main application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.api.v1 import router_v1
from app.core.config import settings
from app.core.middleware import RequestIdMiddleware
from app.providers.registry import registry
from app.schemas.common import HealthResponse

logger = structlog.get_logger()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Your AI Shopping Agent API",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# Custom Middlewares
app.add_middleware(RequestIdMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(router_v1)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Basic service health check."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        services={"api": "up"},
    )


@app.get("/ready", response_model=HealthResponse, tags=["Health"])
async def readiness_check() -> HealthResponse:
    """Readiness probe checking database & provider status."""
    providers_health = await registry.health_check_all()
    all_healthy = all(providers_health.values())

    status_str = "healthy" if all_healthy else "degraded"
    return HealthResponse(
        status=status_str,
        version=settings.app_version,
        services={"providers": "up" if all_healthy else "degraded", **providers_health},
    )
