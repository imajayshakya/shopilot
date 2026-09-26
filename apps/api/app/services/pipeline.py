"""Search Pipeline Orchestrator — coordinates the end-to-end shopping search flow.

Pipeline steps:
1. Parse requirement into ShoppingRequest
2. Generate optimized search queries via SearchPlanner
3. Execute provider searches concurrently (Amazon, Flipkart)
4. Validate & Normalize raw provider results
5. Match & Deduplicate equivalent products
6. Filter & Score candidates using RecommendationEngine
7. Generate transparent evidence & return SearchResponse
"""

from __future__ import annotations

import asyncio
import uuid
import structlog

from app.providers.mock.amazon import MockAmazonProvider
from app.providers.mock.flipkart import MockFlipkartProvider
from app.providers.registry import registry
from app.schemas.shopping import (
    ProductRecommendation,
    ProviderProduct,
    SearchPipelineStats,
    SearchResponse,
)
from app.services.matcher import ProductMatcher
from app.services.normalizer import ProductNormalizer
from app.services.parser import AIRequirementParser, SearchPlanner
from app.services.recommendation import RecommendationEngine

logger = structlog.get_logger()

# Register mock providers by default
if not registry.slugs:
    registry.register(MockAmazonProvider())
    registry.register(MockFlipkartProvider())


class SearchPipeline:
    """End-to-end search pipeline orchestrator."""

    def __init__(self) -> None:
        self.parser = AIRequirementParser()
        self.planner = SearchPlanner()
        self.normalizer = ProductNormalizer()
        self.matcher = ProductMatcher()
        self.recommender = RecommendationEngine()

    async def execute(self, user_query: str) -> SearchResponse:
        """Run the complete vertical slice search pipeline."""
        search_id = f"srch_{uuid.uuid4().hex[:10]}"
        logger.info("pipeline_started", search_id=search_id, query=user_query)

        # 1. Parse requirement
        structured_req = await self.parser.parse(user_query)

        # 2. Plan search queries
        search_queries = self.planner.plan_searches(structured_req)

        # 3. Query providers concurrently
        raw_products: list[ProviderProduct] = []
        providers_searched: list[str] = []
        providers_failed: list[str] = []

        active_providers = registry.all

        for sq in search_queries:
            tasks = [
                self._safe_search(provider, sq.query, sq.category, sq.max_price)
                for provider in active_providers
            ]
            results_list = await asyncio.gather(*tasks)

            for provider, result in zip(active_providers, results_list):
                if provider.name not in providers_searched:
                    providers_searched.append(provider.name)

                if isinstance(result, Exception):
                    if provider.name not in providers_failed:
                        providers_failed.append(provider.name)
                else:
                    raw_products.extend(result)

        # Stats tracking
        total_raw = len(raw_products)

        # 4. Normalize raw products
        normalized_products = self.normalizer.normalize(raw_products)
        valid_count = len(normalized_products)

        # 5. Deduplicate and merge equivalent products
        unique_products = self.matcher.deduplicate(normalized_products)
        unique_count = len(unique_products)

        # 6. Budget hard filtering
        max_budget = structured_req.budget.max_price if structured_req.budget else None
        within_budget = unique_products
        if max_budget:
            within_budget = [
                p for p in unique_products
                if any(o.price <= max_budget for o in p.offers)
            ]
        within_budget_count = len(within_budget)

        # 7. Score & rank recommendations
        recommendations = self.recommender.rank(
            within_budget if within_budget else unique_products,
            structured_req,
            max_results=5,
        )

        stats = SearchPipelineStats(
            total_provider_results=total_raw,
            valid_results=valid_count,
            unique_products=unique_count,
            within_budget=within_budget_count,
            strong_matches=len(recommendations),
            displayed=len(recommendations),
            providers_searched=providers_searched,
            providers_failed=providers_failed,
        )

        logger.info(
            "pipeline_completed",
            search_id=search_id,
            recommendations_count=len(recommendations),
        )

        return SearchResponse(
            search_id=search_id,
            query=user_query,
            structured_request=structured_req,
            recommendations=recommendations,
            pipeline_stats=stats,
            message="Top recommended products matching your request." if recommendations else "No matching products found.",
        )

    async def _safe_search(
        self, provider: Any, query: str, category: str | None, max_price: float | None
    ) -> list[ProviderProduct] | Exception:
        try:
            return await provider.search(query, category=category, max_price=max_price)
        except Exception as e:
            logger.error("provider_search_error", provider=provider.name, error=str(e))
            return e
