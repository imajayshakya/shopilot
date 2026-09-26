"""Marketplace provider abstraction.

Every external marketplace (Amazon, Flipkart, Croma, etc.) implements
this interface. The rest of the system never touches provider internals.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.shopping import ProviderProduct


class MarketplaceProvider(ABC):
    """Abstract base for all marketplace integrations."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name (e.g. 'Amazon')."""
        ...

    @property
    @abstractmethod
    def slug(self) -> str:
        """URL-safe identifier (e.g. 'amazon')."""
        ...

    @abstractmethod
    async def search(
        self,
        query: str,
        *,
        category: str | None = None,
        max_price: float | None = None,
        min_price: float | None = None,
        max_results: int = 25,
    ) -> list[ProviderProduct]:
        """Search for products matching the query."""
        ...

    @abstractmethod
    async def get_product(self, external_product_id: str) -> ProviderProduct | None:
        """Fetch a single product by its provider-specific ID."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider API is reachable."""
        ...

    async def get_offers(self, external_product_id: str) -> list[ProviderProduct]:
        """Get current offers for a product — defaults to get_product."""
        product = await self.get_product(external_product_id)
        return [product] if product else []
