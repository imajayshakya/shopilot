"""Product normalizer — transforms raw provider data into canonical form.

Handles:
- Title cleanup
- Brand extraction
- Specification standardization
- Unit normalization (e.g. "16 GB" → 16)
"""

from __future__ import annotations

import re
import hashlib

import structlog

from app.schemas.shopping import NormalizedProduct, ProductOfferOut, ProviderProduct

logger = structlog.get_logger()


class ProductNormalizer:
    """Deterministic normalization of provider product data."""

    def normalize(self, products: list[ProviderProduct]) -> list[NormalizedProduct]:
        """Normalize a batch of provider products into canonical form."""
        normalized: list[NormalizedProduct] = []

        for product in products:
            try:
                normalized.append(self._normalize_one(product))
            except Exception:
                logger.exception("normalization_failed", title=product.title)
                continue

        return normalized

    def _normalize_one(self, product: ProviderProduct) -> NormalizedProduct:
        """Normalize a single provider product."""
        brand = self._extract_brand(product)
        model = self._extract_model(product)
        title = self._clean_title(product.title)
        specs = self._normalize_specs(product.specifications)
        canonical_id = self._generate_canonical_id(brand, model, product)

        offer = ProductOfferOut(
            merchant=product.provider_name,
            merchant_slug=product.provider_name.lower(),
            price=product.price,
            mrp=product.mrp,
            currency=product.currency,
            discount_percentage=product.discount_percentage,
            availability=product.availability,
            rating=product.rating,
            review_count=product.review_count,
            product_url=product.product_url,
            affiliate_url=product.affiliate_url,
            delivery_text=product.delivery_text,
        )

        return NormalizedProduct(
            canonical_id=canonical_id,
            title=title,
            brand=brand,
            model=model,
            category=product.category,
            image_url=product.image_url,
            description=product.description,
            specifications=specs,
            offers=[offer],
            identifiers={product.provider_name: product.external_id},
        )

    def _clean_title(self, title: str) -> str:
        """Remove noise from product title."""
        # Remove content in multiple parentheses but keep first meaningful one
        cleaned = re.sub(r"\s+", " ", title).strip()
        return cleaned

    def _extract_brand(self, product: ProviderProduct) -> str | None:
        """Extract brand — prefer structured data over title parsing."""
        if product.brand:
            return product.brand.strip().title()

        # Try to extract from title (first word is often the brand)
        words = product.title.split()
        if words:
            return words[0].strip().title()
        return None

    def _extract_model(self, product: ProviderProduct) -> str | None:
        """Extract model name."""
        if product.model:
            return product.model.strip()
        return None

    def _normalize_specs(
        self, specs: dict[str, str | float | int | bool]
    ) -> dict[str, str | float | int | bool]:
        """Standardize specification keys and values."""
        normalized: dict[str, str | float | int | bool] = {}

        key_mapping = {
            "ram": "ram_gb",
            "ram_size": "ram_gb",
            "storage": "storage_gb",
            "storage_size": "storage_gb",
            "screen_size": "display_size",
            "screen": "display_size",
            "display": "display_size",
            "battery": "battery_mah",
            "camera": "camera_mp",
            "main_camera": "camera_mp",
            "weight": "weight_g",
            "cpu": "processor",
            "chipset": "processor",
        }

        for key, value in specs.items():
            normalized_key = key_mapping.get(key.lower(), key.lower())
            normalized[normalized_key] = self._normalize_value(normalized_key, value)

        return normalized

    def _normalize_value(self, key: str, value: str | float | int | bool) -> str | float | int | bool:
        """Normalize a specification value (e.g. '16 GB' → 16)."""
        if isinstance(value, (int, float, bool)):
            return value

        if isinstance(value, str):
            # Try to extract numeric values for known keys
            if key in ("ram_gb", "storage_gb", "camera_mp", "battery_mah", "weight_g"):
                match = re.search(r"(\d+(?:\.\d+)?)", value)
                if match:
                    num = float(match.group(1))
                    return int(num) if num == int(num) else num

        return value

    def _generate_canonical_id(
        self, brand: str | None, model: str | None, product: ProviderProduct
    ) -> str:
        """Generate a deterministic canonical ID for deduplication."""
        parts = [
            (brand or "").lower().strip(),
            (model or "").lower().strip(),
            (product.category or "").lower().strip(),
        ]
        key = "|".join(parts)

        if brand and model:
            return hashlib.md5(key.encode()).hexdigest()[:12]

        # Fallback to provider + external_id
        fallback = f"{product.provider_name}:{product.external_id}"
        return hashlib.md5(fallback.encode()).hexdigest()[:12]
