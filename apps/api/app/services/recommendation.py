"""Recommendation engine — scores and ranks products against user requirements.

Scoring weights (configurable):
- Requirement match:    35%
- Specification match:  25%
- Price/value:          15%
- Reviews:              10%
- Merchant trust:        5%
- Availability:          5%
- User preferences:      5%

All scores are deterministic. No LLM involved.
"""

from __future__ import annotations

import structlog

from app.schemas.shopping import (
    NormalizedProduct,
    ProductOfferOut,
    ProductRecommendation,
    RecommendationScore,
    Requirement,
    RequirementType,
    ShoppingRequest,
)

logger = structlog.get_logger()


class ScoringWeights:
    """Configurable scoring weights for the recommendation engine."""

    def __init__(
        self,
        requirement_match: float = 0.35,
        specification_match: float = 0.25,
        price_value: float = 0.15,
        reviews: float = 0.10,
        availability: float = 0.10,
        user_preferences: float = 0.05,
    ):
        self.requirement_match = requirement_match
        self.specification_match = specification_match
        self.price_value = price_value
        self.reviews = reviews
        self.availability = availability
        self.user_preferences = user_preferences


DEFAULT_WEIGHTS = ScoringWeights()


class RecommendationEngine:
    """Scores and ranks products against the user's shopping request."""

    def __init__(self, weights: ScoringWeights | None = None):
        self.weights = weights or DEFAULT_WEIGHTS

    def rank(
        self,
        products: list[NormalizedProduct],
        request: ShoppingRequest,
        max_results: int = 5,
    ) -> list[ProductRecommendation]:
        """Score, rank and explain products for the given shopping request."""
        if not products:
            return []

        scored: list[ProductRecommendation] = []

        for product in products:
            recommendation = self._score_product(product, request)
            scored.append(recommendation)

        # Sort by total score descending
        scored.sort(key=lambda r: r.score.total, reverse=True)

        # Assign ranks
        for i, rec in enumerate(scored[:max_results]):
            rec.rank = i + 1

        return scored[:max_results]

    def _score_product(
        self, product: NormalizedProduct, request: ShoppingRequest
    ) -> ProductRecommendation:
        """Score a single product against the shopping request."""
        best_offer = self._get_best_offer(product)
        price = best_offer.price if best_offer else 0

        # Individual scoring components
        req_score, matched, missing = self._score_requirements(product, request)
        spec_score = self._score_specifications(product, request)
        price_score = self._score_price_value(price, request)
        review_score = self._score_reviews(best_offer)
        avail_score = self._score_availability(best_offer)
        pref_score = self._score_preferences(product, request)

        # Weighted total (0–100)
        total = (
            req_score * self.weights.requirement_match
            + spec_score * self.weights.specification_match
            + price_score * self.weights.price_value
            + review_score * self.weights.reviews
            + avail_score * self.weights.availability
            + pref_score * self.weights.user_preferences
        )

        score = RecommendationScore(
            total=round(total, 1),
            requirement_match=round(req_score, 1),
            specification_match=round(spec_score, 1),
            price_value=round(price_score, 1),
            reviews_score=round(review_score, 1),
            availability_score=round(avail_score, 1),
        )

        strengths, weaknesses = self._generate_evidence(product, request, best_offer)
        why = self._generate_why_this_pick(matched, strengths, price, request)

        return ProductRecommendation(
            product=product,
            score=score,
            rank=0,
            match_percentage=round(total),
            matched_requirements=matched,
            missing_requirements=missing,
            strengths=strengths,
            weaknesses=weaknesses,
            why_this_pick=why,
            best_offer=best_offer,
        )

    def _score_requirements(
        self, product: NormalizedProduct, request: ShoppingRequest
    ) -> tuple[float, list[str], list[str]]:
        """Score against hard and soft requirements."""
        if not request.requirements:
            return 70.0, [], []

        matched: list[str] = []
        missing: list[str] = []
        hard_total = 0
        hard_met = 0
        soft_total = 0
        soft_met = 0

        for req in request.requirements:
            is_met = self._check_requirement(product, req)

            if req.type == RequirementType.HARD:
                hard_total += 1
                if is_met:
                    hard_met += 1
                    matched.append(req.description or f"{req.key}: {req.value}")
                else:
                    missing.append(req.description or f"{req.key}: {req.value}")
            else:
                soft_total += 1
                if is_met:
                    soft_met += 1
                    matched.append(req.description or f"{req.key}: {req.value}")
                else:
                    missing.append(req.description or f"{req.key}: {req.value}")

        # Hard requirements dominate
        hard_ratio = (hard_met / hard_total * 100) if hard_total > 0 else 100
        soft_ratio = (soft_met / soft_total * 100) if soft_total > 0 else 100

        # If a hard requirement is missing, cap the score
        if hard_total > 0 and hard_met < hard_total:
            return min(hard_ratio * 0.6, 40), matched, missing

        return hard_ratio * 0.7 + soft_ratio * 0.3, matched, missing

    def _check_requirement(self, product: NormalizedProduct, req: Requirement) -> bool:
        """Check if a product satisfies a single requirement."""
        specs = product.specifications
        key = req.key.lower()

        # Map common requirement keys to specification keys
        key_mapping = {
            "ram_min_gb": "ram_gb",
            "storage_min_gb": "storage_gb",
            "camera_min_mp": "camera_mp",
            "battery_min_mah": "battery_mah",
        }

        spec_key = key_mapping.get(key, key)

        if spec_key not in specs:
            # Can't verify — treat as partially met for soft, miss for hard
            return req.type == RequirementType.SOFT

        spec_val = specs[spec_key]

        # Numeric comparison for "min" requirements
        if "_min_" in key or key.endswith("_min"):
            try:
                return float(spec_val) >= float(req.value)
            except (ValueError, TypeError):
                return False

        # Boolean check
        if isinstance(req.value, bool):
            return spec_val == req.value

        # String match
        return str(spec_val).lower() == str(req.value).lower()

    def _score_specifications(
        self, product: NormalizedProduct, request: ShoppingRequest
    ) -> float:
        """Score how well specs match use cases and priorities."""
        if not product.specifications:
            return 50.0

        score = 50.0  # Base score
        specs = product.specifications

        # Reward based on use cases
        for use_case in request.use_cases:
            uc = use_case.lower()
            if "gaming" in uc:
                if specs.get("gpu") and "rtx" in str(specs.get("gpu", "")).lower():
                    score += 15
                elif specs.get("gpu"):
                    score += 5
                if specs.get("processor") and "snapdragon 8" in str(specs.get("processor", "")).lower():
                    score += 10
            if "development" in uc or "coding" in uc or "programming" in uc:
                ram = specs.get("ram_gb", 0)
                if isinstance(ram, (int, float)) and ram >= 16:
                    score += 15
                elif isinstance(ram, (int, float)) and ram >= 8:
                    score += 5
            if "camera" in uc or "photography" in uc:
                cam = specs.get("camera_mp", 0)
                if isinstance(cam, (int, float)) and cam >= 50:
                    score += 15
                elif isinstance(cam, (int, float)) and cam >= 32:
                    score += 8
            if "travel" in uc or "battery" in uc:
                battery = specs.get("battery_mah", 0)
                if isinstance(battery, (int, float)) and battery >= 5000:
                    score += 10

        # Reward based on priorities
        for priority_key, priority_level in request.priorities.items():
            pk = priority_key.lower()
            if pk == "performance" and priority_level.value == "high":
                ram = specs.get("ram_gb", 0)
                if isinstance(ram, (int, float)) and ram >= 12:
                    score += 10
            if pk == "battery" and priority_level.value == "high":
                battery = specs.get("battery_mah", 0) or specs.get("battery_hours", 0)
                if isinstance(battery, (int, float)) and battery >= 4500:
                    score += 10

        return min(score, 100)

    def _score_price_value(self, price: float, request: ShoppingRequest) -> float:
        """Score price value — within budget = good, under budget = better."""
        if not request.budget or not request.budget.max_price:
            return 70.0

        max_budget = request.budget.max_price

        if price > max_budget:
            # Over budget
            over_pct = (price - max_budget) / max_budget
            return max(0, 50 - over_pct * 100)

        # Under budget — the more under, the better
        under_pct = (max_budget - price) / max_budget
        return min(70 + under_pct * 60, 100)

    def _score_reviews(self, offer: ProductOfferOut | None) -> float:
        """Score based on rating and review count."""
        if not offer:
            return 30.0

        score = 30.0
        if offer.rating:
            score += (offer.rating / 5.0) * 50
        if offer.review_count:
            if offer.review_count >= 10000:
                score += 20
            elif offer.review_count >= 5000:
                score += 15
            elif offer.review_count >= 1000:
                score += 10
            elif offer.review_count >= 100:
                score += 5

        return min(score, 100)

    def _score_availability(self, offer: ProductOfferOut | None) -> float:
        """Score availability."""
        if not offer:
            return 0.0
        if offer.availability == "in_stock":
            return 100.0
        if offer.availability == "limited":
            return 60.0
        return 20.0

    def _score_preferences(
        self, product: NormalizedProduct, request: ShoppingRequest
    ) -> float:
        """Score against user brand preferences."""
        score = 50.0

        if request.preferred_brands and product.brand:
            if product.brand.lower() in [b.lower() for b in request.preferred_brands]:
                score += 40

        if request.excluded_brands and product.brand:
            if product.brand.lower() in [b.lower() for b in request.excluded_brands]:
                score = 0

        return min(score, 100)

    def _get_best_offer(self, product: NormalizedProduct) -> ProductOfferOut | None:
        """Return the cheapest available offer."""
        if not product.offers:
            return None

        available = [o for o in product.offers if o.availability == "in_stock"]
        if not available:
            available = product.offers

        return min(available, key=lambda o: o.price)

    def _generate_evidence(
        self,
        product: NormalizedProduct,
        request: ShoppingRequest,
        offer: ProductOfferOut | None,
    ) -> tuple[list[str], list[str]]:
        """Generate human-readable strengths and weaknesses from product data."""
        strengths: list[str] = []
        weaknesses: list[str] = []
        specs = product.specifications

        # Budget
        if offer and request.budget and request.budget.max_price:
            if offer.price <= request.budget.max_price:
                strengths.append(f"Within your ₹{request.budget.max_price:,.0f} budget")
            else:
                weaknesses.append(f"₹{offer.price - request.budget.max_price:,.0f} over budget")

        # RAM
        ram = specs.get("ram_gb")
        if isinstance(ram, (int, float)):
            if ram >= 16:
                strengths.append(f"{int(ram)}GB RAM — excellent for multitasking")
            elif ram >= 8:
                strengths.append(f"{int(ram)}GB RAM")
            else:
                weaknesses.append(f"Only {int(ram)}GB RAM")

        # Storage
        storage = specs.get("storage_gb")
        if isinstance(storage, (int, float)):
            if storage >= 256:
                strengths.append(f"{int(storage)}GB storage")
            elif storage < 128:
                weaknesses.append(f"Only {int(storage)}GB storage")

        # Camera
        camera = specs.get("camera_mp")
        if isinstance(camera, (int, float)) and camera >= 50:
            strengths.append(f"{int(camera)}MP camera")

        # Battery
        battery = specs.get("battery_mah")
        if isinstance(battery, (int, float)):
            if battery >= 5000:
                strengths.append(f"Large {int(battery)}mAh battery")
            elif battery < 4000:
                weaknesses.append("Below-average battery capacity")

        # GPU
        gpu = specs.get("gpu")
        if gpu and isinstance(gpu, str):
            if "rtx" in gpu.lower():
                strengths.append(f"Dedicated {gpu} GPU")
            elif gpu.lower() != "integrated":
                strengths.append(f"{gpu} GPU")

        # Rating
        if offer and offer.rating and offer.rating >= 4.0:
            strengths.append(f"⭐ {offer.rating} rating ({offer.review_count:,} reviews)")

        # Fast charging
        fast_charge = specs.get("fast_charging")
        if fast_charge:
            strengths.append(f"{fast_charge} fast charging")

        # 5G
        if specs.get("5g") is True:
            strengths.append("5G connectivity")

        # Discount
        if offer and offer.discount_percentage and offer.discount_percentage > 10:
            strengths.append(f"{offer.discount_percentage:.0f}% discount")

        return strengths, weaknesses

    def _generate_why_this_pick(
        self,
        matched: list[str],
        strengths: list[str],
        price: float,
        request: ShoppingRequest,
    ) -> list[str]:
        """Generate concise 'Why this pick' bullet points."""
        why: list[str] = []

        # Budget match
        if request.budget and request.budget.max_price:
            if price <= request.budget.max_price:
                why.append(f"✓ Within your ₹{request.budget.max_price:,.0f} budget")

        # Top matched requirements
        for item in matched[:3]:
            why.append(f"✓ {item}")

        # Top strengths (avoid duplicating budget)
        for s in strengths[:3]:
            entry = f"✓ {s}"
            if entry not in why:
                why.append(entry)

        return why[:6]
