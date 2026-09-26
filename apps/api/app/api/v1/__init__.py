"""API router v1."""

from fastapi import APIRouter
from app.api.v1.search import router as search_router

router_v1 = APIRouter(prefix="/api/v1")
router_v1.include_router(search_router)
