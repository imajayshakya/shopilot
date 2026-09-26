"""Models package — re-exports all ORM models."""

from app.models.product import (
    Category,
    Merchant,
    PriceHistory,
    Product,
    ProductIdentifier,
    ProductOffer,
)
from app.models.user import PriceAlert, SearchHistory, User, WishlistItem

__all__ = [
    "Category",
    "Merchant",
    "PriceHistory",
    "Product",
    "ProductIdentifier",
    "ProductOffer",
    "PriceAlert",
    "SearchHistory",
    "User",
    "WishlistItem",
]
