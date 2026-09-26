"""Search API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
import structlog

from app.schemas.shopping import SearchInput, SearchResponse
from app.services.pipeline import SearchPipeline

logger = structlog.get_logger()
router = APIRouter(prefix="/search", tags=["Shopping Search"])

pipeline = SearchPipeline()


@router.post("", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def search_products(payload: SearchInput) -> SearchResponse:
    """Execute natural language AI shopping search."""
    try:
        response = await pipeline.execute(payload.query)
        return response
    except Exception as exc:
        logger.exception("search_failed", query=payload.query)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "SEARCH_PROCESSING_ERROR",
                "message": "An error occurred while processing your shopping search request.",
            },
        ) from exc
