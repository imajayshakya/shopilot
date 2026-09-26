"""Product matcher — detects equivalent products across merchants.

Priority:
1. Exact product identifiers (ASIN, EAN, etc.)
2. Brand + model number
3. Normalized title similarity
4. Specification similarity
"""

from __future__ import annotations

import structlog

from app.schemas.shopping import NormalizedProduct

logger = structlog.get_logger()


class MatchResult:
    """Result of comparing two products."""

    def __init__(
        self,
        same_product: bool,
        confidence: float,
        evidence: list[str],
    ):
        self.same_product = same_product
        self.confidence = confidence
        self.evidence = evidence


class ProductMatcher:
    """Deterministic product matching across providers."""

    def __init__(self, similarity_threshold: float = 0.75):
        self.similarity_threshold = similarity_threshold

    def deduplicate(self, products: list[NormalizedProduct]) -> list[NormalizedProduct]:
        """Merge duplicate products, combining their offers."""
        if not products:
            return []

        merged: dict[str, NormalizedProduct] = {}

        for product in products:
            matched_key = self._find_match(product, merged)

            if matched_key:
                # Merge offers into existing product
                existing = merged[matched_key]
                for offer in product.offers:
                    # Avoid duplicate offers from the same merchant
                    if not any(o.merchant == offer.merchant for o in existing.offers):
                        existing.offers.append(offer)

                # Merge identifiers
                existing.identifiers.update(product.identifiers)

                logger.debug(
                    "products_merged",
                    existing=existing.title,
                    merged=product.title,
                )
            else:
                merged[product.canonical_id] = product

        return list(merged.values())

    def compare(self, a: NormalizedProduct, b: NormalizedProduct) -> MatchResult:
        """Compare two products and determine if they are the same."""
        evidence: list[str] = []
        score = 0.0

        # 1. Same canonical_id (brand + model match)
        if a.canonical_id == b.canonical_id:
            score += 0.5
            evidence.append("Same canonical ID")

        # 2. Brand + model match
        if a.brand and b.brand and a.model and b.model:
            if a.brand.lower() == b.brand.lower() and a.model.lower() == b.model.lower():
                score += 0.35
                evidence.append(f"Same brand ({a.brand}) and model ({a.model})")

        # 3. Title similarity
        title_sim = self._title_similarity(a.title, b.title)
        if title_sim > 0.8:
            score += 0.15
            evidence.append(f"Title similarity: {title_sim:.0%}")

        # 4. Key spec match
        spec_match = self._spec_similarity(a.specifications, b.specifications)
        if spec_match > 0.7:
            score += 0.1
            evidence.append(f"Specification match: {spec_match:.0%}")

        confidence = min(score, 1.0)
        same = confidence >= self.similarity_threshold

        return MatchResult(same_product=same, confidence=confidence, evidence=evidence)

    def _find_match(
        self, product: NormalizedProduct, existing: dict[str, NormalizedProduct]
    ) -> str | None:
        """Find matching product in existing set."""
        # Fast path: exact canonical_id match
        if product.canonical_id in existing:
            return product.canonical_id

        # Slower path: compare against all
        for key, candidate in existing.items():
            result = self.compare(product, candidate)
            if result.same_product:
                return key

        return None

    def _title_similarity(self, a: str, b: str) -> float:
        """Simple word-overlap similarity between titles."""
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())

        if not words_a or not words_b:
            return 0.0

        intersection = words_a & words_b
        union = words_a | words_b

        return len(intersection) / len(union)

    def _spec_similarity(
        self,
        a: dict[str, str | float | int | bool],
        b: dict[str, str | float | int | bool],
    ) -> float:
        """Compare overlapping specifications."""
        common_keys = set(a.keys()) & set(b.keys())
        if not common_keys:
            return 0.0

        matches = sum(1 for k in common_keys if str(a[k]).lower() == str(b[k]).lower())
        return matches / len(common_keys)
