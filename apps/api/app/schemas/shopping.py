"""Shopping-related schemas — the core AI shopping agent data contracts."""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RequirementType(str, Enum):
    HARD = "hard"
    SOFT = "soft"


class PriceStatus(str, Enum):
    GOOD = "good"
    NORMAL = "normal"
    HIGH = "high"


# ── Budget ─────────────────────────────────────────────────────────

class Budget(BaseModel):
    """Price range constraint."""
    min_price: float | None = Field(None, alias="min")
    max_price: float | None = Field(None, alias="max")
    currency: str = "INR"

    model_config = {"populate_by_name": True}


# ── Requirement ────────────────────────────────────────────────────

class Requirement(BaseModel):
    """A single user requirement — hard or soft."""
    key: str
    value: str | float | int | bool
    type: RequirementType = RequirementType.SOFT
    description: str | None = None


# ── Shopping Request ───────────────────────────────────────────────

class ShoppingRequest(BaseModel):
    """Structured representation of a user's shopping intent.

    Produced by the AI Requirement Parser from natural-language input.
    Consumed by the Search Planner and Recommendation Engine.
    """
    category: str | None = None
    query: str = ""
    budget: Budget | None = None
    requirements: list[Requirement] = Field(default_factory=list)
    use_cases: list[str] = Field(default_factory=list)
    preferred_brands: list[str] = Field(default_factory=list)
    excluded_brands: list[str] = Field(default_factory=list)
    priorities: dict[str, Priority] = Field(default_factory=dict)
    location: str = "India"


# ── Search Queries ─────────────────────────────────────────────────

class SearchQuery(BaseModel):
    """A single search query to send to providers."""
    query: str
    category: str | None = None
    max_price: float | None = None
    min_price: float | None = None


# ── User-facing request ───────────────────────────────────────────

class SearchInput(BaseModel):
    """API input — what the user types."""
    query: str = Field(..., min_length=3, max_length=500, description="Natural-language shopping query")


# ── Provider product (raw, before normalization) ──────────────────

class ProviderProduct(BaseModel):
    """Raw product data returned by a marketplace provider."""
    provider_name: str
    external_id: str
    title: str
    brand: str | None = None
    model: str | None = None
    price: float
    mrp: float | None = None
    currency: str = "INR"
    discount_percentage: float | None = None
    availability: str = "in_stock"
    rating: float | None = None
    review_count: int | None = None
    image_url: str | None = None
    product_url: str
    affiliate_url: str | None = None
    category: str | None = None
    specifications: dict[str, str | float | int | bool] = Field(default_factory=dict)
    description: str | None = None
    delivery_text: str | None = None
    raw_metadata: dict | None = None


# ── Normalized product ────────────────────────────────────────────

class NormalizedProduct(BaseModel):
    """A product after normalization, deduplication and enrichment."""
    canonical_id: str
    title: str
    brand: str | None = None
    model: str | None = None
    category: str | None = None
    image_url: str | None = None
    description: str | None = None
    specifications: dict[str, str | float | int | bool] = Field(default_factory=dict)
    offers: list[ProductOfferOut] = Field(default_factory=list)
    identifiers: dict[str, str] = Field(default_factory=dict)


# ── Offer output ──────────────────────────────────────────────────

class ProductOfferOut(BaseModel):
    """A single merchant offer for a product."""
    merchant: str
    merchant_slug: str
    price: float
    mrp: float | None = None
    currency: str = "INR"
    discount_percentage: float | None = None
    availability: str = "in_stock"
    rating: float | None = None
    review_count: int | None = None
    product_url: str
    affiliate_url: str | None = None
    delivery_text: str | None = None


# Fix forward reference
NormalizedProduct.model_rebuild()


# ── Recommendation ────────────────────────────────────────────────

class RecommendationScore(BaseModel):
    """Detailed scoring breakdown for a recommended product."""
    total: float = Field(..., ge=0, le=100)
    requirement_match: float = 0
    specification_match: float = 0
    price_value: float = 0
    reviews_score: float = 0
    availability_score: float = 0


class ProductRecommendation(BaseModel):
    """A single product recommendation with transparent reasoning."""
    product: NormalizedProduct
    score: RecommendationScore
    rank: int
    match_percentage: int
    matched_requirements: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    why_this_pick: list[str] = Field(default_factory=list)
    best_offer: ProductOfferOut | None = None


# ── Search Response ───────────────────────────────────────────────

class SearchPipelineStats(BaseModel):
    """Transparency stats about the search pipeline."""
    total_provider_results: int = 0
    valid_results: int = 0
    unique_products: int = 0
    within_budget: int = 0
    strong_matches: int = 0
    displayed: int = 0
    providers_searched: list[str] = Field(default_factory=list)
    providers_failed: list[str] = Field(default_factory=list)


class SearchResponse(BaseModel):
    """Complete response to a shopping search query."""
    search_id: str
    query: str
    structured_request: ShoppingRequest
    recommendations: list[ProductRecommendation] = Field(default_factory=list)
    pipeline_stats: SearchPipelineStats = Field(default_factory=SearchPipelineStats)
    message: str | None = None
