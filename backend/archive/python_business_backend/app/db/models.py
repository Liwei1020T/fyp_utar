from datetime import date
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Boolean
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import String as SAString
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.core.constants import BookingStatus
from app.core.constants import UserRole
from app.db.base import Base


def _uuid() -> str:
    return str(uuid4())


class AppUser(Base):
    __tablename__ = "app_users"

    id: Mapped[str] = mapped_column(SAString(36), primary_key=True, default=_uuid)
    auth_user_id: Mapped[str] = mapped_column(
        SAString(36),
        unique=True,
        index=True,
        default=_uuid,
    )
    full_name: Mapped[str] = mapped_column(SAString(255))
    phone_number: Mapped[str] = mapped_column(
        SAString(30),
        unique=True,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(SAString(255))
    role: Mapped[str] = mapped_column(
        SAString(20),
        default=UserRole.CUSTOMER.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class CustomerProfile(Base):
    __tablename__ = "customer_profiles"

    id: Mapped[str] = mapped_column(SAString(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("app_users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    skill_level: Mapped[str | None] = mapped_column(SAString(50), nullable=True)
    playing_style: Mapped[str | None] = mapped_column(SAString(50), nullable=True)
    play_frequency: Mapped[str | None] = mapped_column(SAString(50), nullable=True)
    budget_min: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    budget_max: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    preferred_tension: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 1), nullable=True
    )
    durability_priority: Mapped[int | None] = mapped_column(Integer, nullable=True)
    repulsion_priority: Mapped[int | None] = mapped_column(Integer, nullable=True)
    control_priority: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sound_priority: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tension_retention_priority: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    preferred_feel: Mapped[str | None] = mapped_column(SAString(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class String(Base):
    __tablename__ = "strings"

    id: Mapped[str] = mapped_column(SAString(36), primary_key=True, default=_uuid)
    external_id: Mapped[str | None] = mapped_column(
        SAString(50),
        unique=True,
        index=True,
        nullable=True,
    )
    source_item_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    brand: Mapped[str] = mapped_column(SAString(100), index=True)
    brand_en: Mapped[str | None] = mapped_column(SAString(100), nullable=True)
    model_name: Mapped[str] = mapped_column(SAString(100), index=True)
    series: Mapped[str | None] = mapped_column(SAString(50), nullable=True)
    series_en: Mapped[str | None] = mapped_column(SAString(50), nullable=True)
    currency: Mapped[str] = mapped_column(SAString(10), default="RM")
    gauge_raw: Mapped[str | None] = mapped_column(SAString(20), nullable=True)
    gauge_mm: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    material: Mapped[str | None] = mapped_column(SAString(100), nullable=True)
    material_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str | None] = mapped_column(SAString(100), nullable=True)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    rating_5_scale: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    want_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    popularity_signal: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feature_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    feature_text_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    repulsion_score: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )
    durability_score: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )
    control_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    sound_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    tension_retention_score: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )
    value_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    availability_status: Mapped[str] = mapped_column(SAString(20), default="active")
    recommended_tension_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recommended_tension_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class StringTag(Base):
    __tablename__ = "string_tags"

    id: Mapped[str] = mapped_column(SAString(36), primary_key=True, default=_uuid)
    string_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("strings.id", ondelete="CASCADE"),
        index=True,
    )
    tag_name: Mapped[str] = mapped_column(SAString(100))
    tag_name_en: Mapped[str | None] = mapped_column(SAString(100), nullable=True)
    votes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(SAString(36), primary_key=True, default=_uuid)
    customer_user_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("app_users.id", ondelete="CASCADE"),
        index=True,
    )
    string_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("strings.id"),
        index=True,
    )
    racket_brand: Mapped[str | None] = mapped_column(SAString(100), nullable=True)
    racket_model: Mapped[str | None] = mapped_column(SAString(100), nullable=True)
    requested_tension: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 1), nullable=True
    )
    appointment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    appointment_slot: Mapped[str | None] = mapped_column(SAString(30), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        SAString(30),
        default=BookingStatus.PENDING.value,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class BookingStatusHistory(Base):
    __tablename__ = "booking_status_history"

    id: Mapped[str] = mapped_column(SAString(36), primary_key=True, default=_uuid)
    booking_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        index=True,
    )
    old_status: Mapped[str | None] = mapped_column(SAString(30), nullable=True)
    new_status: Mapped[str] = mapped_column(SAString(30))
    changed_by_user_id: Mapped[str | None] = mapped_column(
        SAString(36),
        ForeignKey("app_users.id"),
        nullable=True,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class RecommendationLog(Base):
    __tablename__ = "recommendation_logs"

    id: Mapped[str] = mapped_column(SAString(36), primary_key=True, default=_uuid)
    customer_user_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("app_users.id", ondelete="CASCADE"),
        index=True,
    )
    input_snapshot: Mapped[str] = mapped_column(Text)
    result_snapshot: Mapped[str] = mapped_column(Text)
    algorithm_version: Mapped[str | None] = mapped_column(SAString(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class PasswordResetCode(Base):
    __tablename__ = "password_reset_codes"

    id: Mapped[str] = mapped_column(SAString(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("app_users.id", ondelete="CASCADE"),
        index=True,
    )
    phone_number: Mapped[str] = mapped_column(SAString(30), index=True)
    code_hash: Mapped[str] = mapped_column(SAString(255))
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
