from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import Numeric
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy import String as SAString
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.adapters.persistence.sqlalchemy.base import Base
from app.adapters.persistence.sqlalchemy.models.common import generate_uuid

if TYPE_CHECKING:
    from app.adapters.persistence.sqlalchemy.models.booking import Booking
    from app.adapters.persistence.sqlalchemy.models.user import User


class Brand(Base):
    __tablename__ = "brands"

    brand_code: Mapped[str] = mapped_column(SAString(40), primary_key=True)
    brand_name: Mapped[str] = mapped_column(SAString(120), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    strings: Mapped[list["StringCatalogItem"]] = relationship(
        back_populates="brand_ref"
    )


class StringCatalogItem(Base):
    __tablename__ = "strings"

    catalog_id: Mapped[str] = mapped_column(SAString(120), primary_key=True)
    brand_code: Mapped[str] = mapped_column(
        SAString(40),
        ForeignKey("brands.brand_code"),
        index=True,
    )
    display_name: Mapped[str] = mapped_column(SAString(160), unique=True, index=True)
    model_name: Mapped[str] = mapped_column(SAString(120), index=True)
    series_key: Mapped[str | None] = mapped_column(
        SAString(80), nullable=True, index=True
    )
    series_label: Mapped[str | None] = mapped_column(SAString(120), nullable=True)
    is_hybrid: Mapped[bool] = mapped_column(Boolean, default=False)
    gauge_main_mm: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    gauge_cross_mm: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    gauge_label: Mapped[str | None] = mapped_column(SAString(80), nullable=True)
    category: Mapped[str | None] = mapped_column(
        SAString(40), nullable=True, index=True
    )
    main_trait: Mapped[str | None] = mapped_column(SAString(120), nullable=True)
    tension_min_lbs: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tension_max_lbs: Mapped[int | None] = mapped_column(Integer, nullable=True)
    material_summary_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    color_options_en: Mapped[list[str]] = mapped_column(JSON, default=list)
    short_description: Mapped[str] = mapped_column(Text)
    full_description: Mapped[str] = mapped_column(Text)
    official_performance_status: Mapped[str] = mapped_column(
        SAString(40),
        default="pending_manual_fill",
        index=True,
    )
    source_dataset_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_language: Mapped[str | None] = mapped_column(SAString(32), nullable=True)
    original_name: Mapped[str | None] = mapped_column(SAString(160), nullable=True)
    original_brand_label: Mapped[str | None] = mapped_column(
        SAString(160), nullable=True
    )
    original_series: Mapped[str | None] = mapped_column(SAString(160), nullable=True)
    original_material: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_color: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    brand_ref: Mapped["Brand"] = relationship(back_populates="strings")
    metrics: Mapped["StringCatalogMetric | None"] = relationship(
        back_populates="catalog_item",
        cascade="all, delete-orphan",
        uselist=False,
    )
    tags: Mapped[list["StringCatalogTag"]] = relationship(
        back_populates="catalog_item",
        cascade="all, delete-orphan",
        order_by="StringCatalogTag.tag_label.asc()",
    )
    official_performance: Mapped["StringOfficialPerformance | None"] = relationship(
        back_populates="catalog_item",
        cascade="all, delete-orphan",
        uselist=False,
    )
    inventory_item: Mapped["StringInventoryItem | None"] = relationship(
        back_populates="catalog_item",
        cascade="all, delete-orphan",
        uselist=False,
    )
    recommendation_entries: Mapped[list["StringRecommendationMatrix"]] = relationship(
        back_populates="catalog_item",
        cascade="all, delete-orphan",
    )
    bookings: Mapped[list["Booking"]] = relationship(back_populates="string_item")


class StringCatalogMetric(Base):
    __tablename__ = "string_catalog_metrics"

    catalog_id: Mapped[str] = mapped_column(
        SAString(120),
        ForeignKey("strings.catalog_id", ondelete="CASCADE"),
        primary_key=True,
    )
    feedback_rating: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    want_count: Mapped[int] = mapped_column(Integer, default=0)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    catalog_item: Mapped["StringCatalogItem"] = relationship(back_populates="metrics")


class StringCatalogTag(Base):
    __tablename__ = "string_catalog_tags"

    catalog_id: Mapped[str] = mapped_column(
        SAString(120),
        ForeignKey("strings.catalog_id", ondelete="CASCADE"),
    )
    tag_key: Mapped[str] = mapped_column(SAString(80))
    tag_label: Mapped[str] = mapped_column(SAString(120))
    tag_count: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (PrimaryKeyConstraint("catalog_id", "tag_key"),)

    catalog_item: Mapped["StringCatalogItem"] = relationship(back_populates="tags")


class StringOfficialPerformance(Base):
    __tablename__ = "string_official_performance"

    catalog_id: Mapped[str] = mapped_column(
        SAString(120),
        ForeignKey("strings.catalog_id", ondelete="CASCADE"),
        primary_key=True,
    )
    source_type: Mapped[str | None] = mapped_column(SAString(40), nullable=True)
    source_name: Mapped[str | None] = mapped_column(SAString(160), nullable=True)
    source_region: Mapped[str | None] = mapped_column(SAString(60), nullable=True)
    category: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    feature: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    feel: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    repulsion_power: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    durability: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    hitting_sound: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    shock_absorption: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    control: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        SAString(40),
        default="pending_manual_fill",
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    catalog_item: Mapped["StringCatalogItem"] = relationship(
        back_populates="official_performance"
    )


class StringInventoryItem(Base):
    __tablename__ = "inventory_items"

    inventory_id: Mapped[str] = mapped_column(
        SAString(36),
        primary_key=True,
        default=generate_uuid,
    )
    catalog_id: Mapped[str] = mapped_column(
        SAString(120),
        ForeignKey("strings.catalog_id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    sku: Mapped[str | None] = mapped_column(SAString(120), nullable=True, unique=True)
    current_stock: Mapped[int] = mapped_column(Integer, default=0)
    reserved_stock: Mapped[int] = mapped_column(Integer, default=0)
    available_stock: Mapped[int] = mapped_column(Integer, default=0)
    reorder_level: Mapped[int] = mapped_column(Integer, default=3)
    reorder_quantity: Mapped[int] = mapped_column(Integer, default=8)
    cost_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    selling_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    pricing_mode: Mapped[str] = mapped_column(SAString(32), default="price_pending")
    availability_status: Mapped[str] = mapped_column(
        SAString(32), default="in_stock", index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    catalog_item: Mapped["StringCatalogItem"] = relationship(
        back_populates="inventory_item"
    )
    movements: Mapped[list["InventoryMovement"]] = relationship(
        back_populates="inventory_item",
        cascade="all, delete-orphan",
        order_by="InventoryMovement.created_at.desc()",
    )


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    movement_id: Mapped[str] = mapped_column(
        SAString(36),
        primary_key=True,
        default=generate_uuid,
    )
    inventory_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("inventory_items.inventory_id", ondelete="CASCADE"),
        index=True,
    )
    movement_type: Mapped[str] = mapped_column(SAString(40), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    reference_type: Mapped[str | None] = mapped_column(SAString(60), nullable=True)
    reference_id: Mapped[str | None] = mapped_column(SAString(120), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    inventory_item: Mapped["StringInventoryItem"] = relationship(
        back_populates="movements"
    )


class RecommendationFeatureDefinition(Base):
    __tablename__ = "recommendation_feature_definitions"

    feature_key: Mapped[str] = mapped_column(SAString(80), primary_key=True)
    feature_label: Mapped[str] = mapped_column(SAString(120))
    feature_group: Mapped[str] = mapped_column(SAString(80), index=True)
    data_type: Mapped[str] = mapped_column(SAString(32))
    min_value: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    max_value: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    matrix_entries: Mapped[list["StringRecommendationMatrix"]] = relationship(
        back_populates="feature_definition"
    )
    user_preferences: Mapped[list["UserPreferenceMatrix"]] = relationship(
        back_populates="feature_definition"
    )


class StringRecommendationMatrix(Base):
    __tablename__ = "string_recommendation_matrix"

    catalog_id: Mapped[str] = mapped_column(
        SAString(120),
        ForeignKey("strings.catalog_id", ondelete="CASCADE"),
    )
    feature_key: Mapped[str] = mapped_column(
        SAString(80),
        ForeignKey(
            "recommendation_feature_definitions.feature_key", ondelete="CASCADE"
        ),
    )
    source_layer: Mapped[str] = mapped_column(SAString(40))
    raw_value: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    normalized_score: Mapped[float | None] = mapped_column(
        Numeric(6, 4),
        nullable=True,
        index=True,
    )
    evidence_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        PrimaryKeyConstraint("catalog_id", "feature_key", "source_layer"),
    )

    catalog_item: Mapped["StringCatalogItem"] = relationship(
        back_populates="recommendation_entries"
    )
    feature_definition: Mapped["RecommendationFeatureDefinition"] = relationship(
        back_populates="matrix_entries"
    )


class UserPreferenceMatrix(Base):
    __tablename__ = "user_preference_matrix"

    user_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    feature_key: Mapped[str] = mapped_column(
        SAString(80),
        ForeignKey(
            "recommendation_feature_definitions.feature_key", ondelete="CASCADE"
        ),
    )
    source_layer: Mapped[str] = mapped_column(SAString(40))
    raw_score: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    preference_weight: Mapped[float | None] = mapped_column(
        Numeric(6, 4), nullable=True
    )
    preferred_min: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    preferred_max: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (PrimaryKeyConstraint("user_id", "feature_key", "source_layer"),)

    user: Mapped["User"] = relationship()
    feature_definition: Mapped["RecommendationFeatureDefinition"] = relationship(
        back_populates="user_preferences"
    )


class RecommendationScoreCache(Base):
    __tablename__ = "recommendation_score_cache"

    user_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    catalog_id: Mapped[str] = mapped_column(
        SAString(120),
        ForeignKey("strings.catalog_id", ondelete="CASCADE"),
    )
    algorithm_version: Mapped[str] = mapped_column(SAString(80))
    preference_match_score: Mapped[float | None] = mapped_column(
        Numeric(6, 4),
        nullable=True,
    )
    rule_fit_score: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    value_for_money_score: Mapped[float | None] = mapped_column(
        Numeric(6, 4),
        nullable=True,
    )
    nlp_review_score: Mapped[float | None] = mapped_column(
        Numeric(6, 4),
        nullable=True,
    )
    final_score: Mapped[float] = mapped_column(Numeric(6, 4))
    rank_position: Mapped[int] = mapped_column(Integer)
    rationale: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    __table_args__ = (
        PrimaryKeyConstraint("user_id", "catalog_id", "algorithm_version"),
    )

    user: Mapped["User"] = relationship()
    catalog_item: Mapped["StringCatalogItem"] = relationship()
