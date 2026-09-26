"""Common response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Structured error response."""
    code: str
    message: str
    request_id: str | None = None


class ErrorResponse(BaseModel):
    """Wrapper for error responses."""
    error: ErrorDetail


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str
    services: dict[str, str] = Field(default_factory=dict)
