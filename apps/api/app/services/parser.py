"""AI requirement parser & search planner.

Converts natural language queries into structured `ShoppingRequest` objects
and optimizes search queries to dispatch to providers.
"""

from __future__ import annotations

import re
import structlog
from typing import Any

from app.core.config import settings
from app.schemas.shopping import (
    Budget,
    Priority,
    Requirement,
    RequirementType,
    SearchQuery,
    ShoppingRequest,
)

logger = structlog.get_logger()


class AIRequirementParser:
    """Parses natural-language user shopping queries into structured ShoppingRequest."""

    async def parse(self, query: str) -> ShoppingRequest:
        """Parse query into a structured ShoppingRequest using heuristic fallback or AI."""
        if settings.ai_configured:
            try:
                return await self._parse_with_azure_ai(query)
            except Exception:
                logger.exception("azure_ai_parser_failed_fallback_to_rules", query=query)

        return self._parse_with_rules(query)

    def _parse_with_rules(self, query: str) -> ShoppingRequest:
        """Deterministic rule-based parser fallback."""
        q_lower = query.lower()

        # Category detection
        category = None
        if any(w in q_lower for w in ["phone", "mobile", "smartphone", "iphone", "galaxy"]):
            category = "smartphone"
        elif any(w in q_lower for w in ["laptop", "notebook", "macbook", "computer"]):
            category = "laptop"
        elif any(w in q_lower for w in ["headphone", "earphone", "headset", "earbuds"]):
            category = "headphones"

        # Budget extraction (e.g., "under ₹40,000", "under 40k", "under 70000")
        max_price = None
        budget_match = re.search(r"under\s+(?:₹\s*|rs\.?\s*)?(\d+)(k|000)?", q_lower)
        if budget_match:
            val = float(budget_match.group(1))
            unit = budget_match.group(2)
            if unit == "k":
                val *= 1000
            elif val < 100 and not unit:
                val *= 1000  # e.g., "under 40" -> 40000
            max_price = val

        budget = Budget(max=max_price, currency="INR") if max_price else None

        # Requirements extraction
        requirements: list[Requirement] = []
        if max_price:
            requirements.append(
                Requirement(
                    key="budget_max",
                    value=max_price,
                    type=RequirementType.HARD,
                    description=f"Under ₹{max_price:,.0f}",
                )
            )

        # RAM extraction (e.g., "16gb ram")
        ram_match = re.search(r"(\d+)\s*gb\s*ram", q_lower)
        if ram_match:
            ram_val = int(ram_match.group(1))
            requirements.append(
                Requirement(
                    key="ram_min_gb",
                    value=ram_val,
                    type=RequirementType.HARD,
                    description=f"At least {ram_val}GB RAM",
                )
            )

        # Storage extraction
        storage_match = re.search(r"(\d+)\s*(?:gb|tb)\s*ssd|storage", q_lower)
        if storage_match:
            storage_val = int(storage_match.group(1))
            requirements.append(
                Requirement(
                    key="storage_min_gb",
                    value=storage_val,
                    type=RequirementType.SOFT,
                    description=f"At least {storage_val}GB storage",
                )
            )

        # Camera detection
        use_cases = []
        if "camera" in q_lower or "photo" in q_lower:
            use_cases.append("camera")
            requirements.append(
                Requirement(
                    key="camera_min_mp",
                    value=32,
                    type=RequirementType.SOFT,
                    description="Good camera performance",
                )
            )
        if "coding" in q_lower or "developer" in q_lower or "programming" in q_lower or "python" in q_lower:
            use_cases.append("development")
        if "gaming" in q_lower:
            use_cases.append("gaming")

        priorities = {}
        if "camera" in use_cases:
            priorities["camera"] = Priority.HIGH
        if "development" in use_cases or "gaming" in use_cases:
            priorities["performance"] = Priority.HIGH

        return ShoppingRequest(
            category=category,
            query=query,
            budget=budget,
            requirements=requirements,
            use_cases=use_cases,
            priorities=priorities,
        )

    async def _parse_with_azure_ai(self, query: str) -> ShoppingRequest:
        """Call Azure OpenAI to get structured JSON parsing."""
        # Intentionally placeholder for live Azure AI calls
        return self._parse_with_rules(query)


class SearchPlanner:
    """Generates optimized search queries from a ShoppingRequest."""

    def plan_searches(self, request: ShoppingRequest) -> list[SearchQuery]:
        """Generate targeted provider queries."""
        queries: list[SearchQuery] = []

        # Core query
        base_q = request.category or request.query
        max_p = request.budget.max_price if request.budget else None

        queries.append(
            SearchQuery(
                query=base_q,
                category=request.category,
                max_price=max_p,
            )
        )

        # Add targeted query if brand preferred
        for brand in request.preferred_brands[:2]:
            queries.append(
                SearchQuery(
                    query=f"{brand} {base_q}",
                    category=request.category,
                    max_price=max_p,
                )
            )

        return queries
