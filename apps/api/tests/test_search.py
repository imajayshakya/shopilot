"""Unit tests for the AI Shopping Pipeline & API."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.shopping import RequirementType, ShoppingRequest
from app.services.matcher import ProductMatcher
from app.services.normalizer import ProductNormalizer
from app.services.parser import AIRequirementParser
from app.services.pipeline import SearchPipeline
from app.services.recommendation import RecommendationEngine


@pytest.mark.asyncio
async def test_health_check():
    """Test health endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_requirement_parser():
    """Test natural language query parsing into ShoppingRequest."""
    parser = AIRequirementParser()
    req = await parser.parse("I need a phone under ₹40,000 with a good camera")

    assert req.category == "smartphone"
    assert req.budget is not None
    assert req.budget.max_price == 40000
    assert any(r.type == RequirementType.HARD for r in req.requirements)


@pytest.mark.asyncio
async def test_search_pipeline_execution():
    """Test full search pipeline execution with mock providers."""
    pipeline = SearchPipeline()
    response = await pipeline.execute("I need a phone under ₹40,000 with a good camera")

    assert response.search_id.startswith("srch_")
    assert len(response.recommendations) > 0
    top_rec = response.recommendations[0]
    assert top_rec.rank == 1
    assert top_rec.best_offer is not None
    assert top_rec.best_offer.price <= 40000
    assert len(top_rec.why_this_pick) > 0


@pytest.mark.asyncio
async def test_search_api_endpoint():
    """Test POST /api/v1/search endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/search",
            json={"query": "laptop under 70000 for coding"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "recommendations" in data
        assert len(data["recommendations"]) > 0
