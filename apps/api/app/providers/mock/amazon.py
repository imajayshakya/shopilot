"""Mock Amazon provider for local development."""

from __future__ import annotations

import asyncio

from app.providers.base import MarketplaceProvider
from app.providers.mock.fixtures import AMAZON_FIXTURES, ALL_AMAZON
from app.schemas.shopping import ProviderProduct


class MockAmazonProvider(MarketplaceProvider):
    """Simulates the Amazon Product Advertising API with fixture data."""

    @property
    def name(self) -> str:
        return "Amazon"

    @property
    def slug(self) -> str:
        return "amazon"

    async def search(
        self,
        query: str,
        *,
        category: str | None = None,
        max_price: float | None = None,
        min_price: float | None = None,
        max_results: int = 25,
    ) -> list[ProviderProduct]:
        # Simulate network latency
        await asyncio.sleep(0.1)

        # Select fixture set by category
        fixtures = self._get_fixtures(query, category)

        # Apply price filters
        results = []
        for item in fixtures:
            if max_price and item["price"] > max_price:
                continue
            if min_price and item["price"] < min_price:
                continue
            results.append(self._to_provider_product(item))

        return results[:max_results]

    async def get_product(self, external_product_id: str) -> ProviderProduct | None:
        await asyncio.sleep(0.05)
        for items in [ALL_AMAZON]:
            for item in items:
                if item["external_id"] == external_product_id:
                    return self._to_provider_product(item)
        return None

    async def health_check(self) -> bool:
        return True

    def _get_fixtures(self, query: str, category: str | None) -> list[dict]:
        """Match fixtures by category or by keywords in the query."""
        query_lower = query.lower()

        if category:
            cat = category.lower()
            if cat in AMAZON_FIXTURES:
                return AMAZON_FIXTURES[cat]

        # Infer category from query
        for keyword, fixtures in AMAZON_FIXTURES.items():
            if keyword in query_lower:
                return fixtures

        # Fallback: return all
        return ALL_AMAZON

    def _to_provider_product(self, item: dict) -> ProviderProduct:
        discount = None
        if item.get("mrp") and item["mrp"] > item["price"]:
            discount = round((1 - item["price"] / item["mrp"]) * 100, 1)

        return ProviderProduct(
            provider_name=self.name,
            external_id=item["external_id"],
            title=item["title"],
            brand=item.get("brand"),
            model=item.get("model"),
            price=item["price"],
            mrp=item.get("mrp"),
            currency="INR",
            discount_percentage=discount,
            availability="in_stock",
            rating=item.get("rating"),
            review_count=item.get("review_count"),
            image_url=item.get("image_url"),
            product_url=item["product_url"],
            category=item.get("category"),
            specifications=item.get("specifications", {}),
            description=item.get("description"),
            delivery_text=item.get("delivery_text"),
        )
