"""Product and related models — the canonical product data model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Category(Base):
    """Product category (e.g. Smartphones, Laptops)."""

    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(Base):
    """Canonical product — one product, many merchant offers."""

    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_title: Mapped[str] = mapped_column(String(500), nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    model: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    canonical_attributes: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    category: Mapped[Optional["Category"]] = relationship(back_populates="products")
    identifiers: Mapped[list["ProductIdentifier"]] = relationship(back_populates="product")
    offers: Mapped[list["ProductOffer"]] = relationship(back_populates="product")

    __table_args__ = (
        Index("ix_products_brand_model", "brand", "model"),
    )


class ProductIdentifier(Base):
    """External identifiers for cross-merchant matching (ASIN, EAN, etc.)."""

    __tablename__ = "product_identifiers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    identifier_type: Mapped[str] = mapped_column(String(30), nullable=False)
    identifier_value: Mapped[str] = mapped_column(String(200), nullable=False)

    product: Mapped["Product"] = relationship(back_populates="identifiers")

    __table_args__ = (
        Index("ix_product_identifiers_type_value", "identifier_type", "identifier_value"),
    )


class Merchant(Base):
    """An e-commerce merchant / retailer."""

    __tablename__ = "merchants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    website_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    offers: Mapped[list["ProductOffer"]] = relationship(back_populates="merchant")


class ProductOffer(Base):
    """A specific merchant's listing/offer for a canonical product."""

    __tablename__ = "product_offers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    merchant_product_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    mrp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    discount_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    availability: Mapped[str] = mapped_column(String(30), default="in_stock")
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    review_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    product_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    affiliate_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    shipping_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    delivery_text: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    product: Mapped["Product"] = relationship(back_populates="offers")
    merchant: Mapped["Merchant"] = relationship(back_populates="offers")
    price_history: Mapped[list["PriceHistory"]] = relationship(back_populates="offer")

    __table_args__ = (
        Index("ix_product_offers_product_merchant", "product_id", "merchant_id"),
    )


class PriceHistory(Base):
    """Historical price point for an offer."""

    __tablename__ = "price_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_offers.id", ondelete="CASCADE"), nullable=False
    )
    price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    offer: Mapped["ProductOffer"] = relationship(back_populates="price_history")
