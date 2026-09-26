"""Provider registry — discovers and manages marketplace providers."""

from __future__ import annotations

import structlog
from app.providers.base import MarketplaceProvider

logger = structlog.get_logger()


class ProviderRegistry:
    """Central registry of configured marketplace providers."""

    def __init__(self) -> None:
        self._providers: dict[str, MarketplaceProvider] = {}

    def register(self, provider: MarketplaceProvider) -> None:
        """Register a marketplace provider."""
        self._providers[provider.slug] = provider
        logger.info("provider_registered", provider=provider.name, slug=provider.slug)

    def get(self, slug: str) -> MarketplaceProvider | None:
        """Get provider by slug."""
        return self._providers.get(slug)

    @property
    def all(self) -> list[MarketplaceProvider]:
        """All registered providers."""
        return list(self._providers.values())

    @property
    def slugs(self) -> list[str]:
        """Slugs of all registered providers."""
        return list(self._providers.keys())

    async def health_check_all(self) -> dict[str, bool]:
        """Run health checks on all providers."""
        results = {}
        for slug, provider in self._providers.items():
            try:
                results[slug] = await provider.health_check()
            except Exception:
                logger.exception("provider_health_check_failed", provider=slug)
                results[slug] = False
        return results


# Singleton registry
registry = ProviderRegistry()
