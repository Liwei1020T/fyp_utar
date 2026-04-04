from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import String as SAString
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from stringsense_backend.db.base import Base


def _uuid() -> str:
    return str(uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(SAString(36), primary_key=True, default=_uuid)
    username: Mapped[str] = mapped_column(SAString(64), index=True)
    phone_number: Mapped[str] = mapped_column(SAString(20), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(SAString(255))
    role: Mapped[str] = mapped_column(SAString(20), default="customer")
    auth_provider: Mapped[str] = mapped_column(SAString(40), default="local")
    external_auth_id: Mapped[str | None] = mapped_column(
        SAString(64),
        unique=True,
        nullable=True,
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

    profile: Mapped["Profile | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    bookings: Mapped[list["Booking"]] = relationship(back_populates="user")
    recommendation_logs: Mapped[list["RecommendationLog"]] = relationship(
        back_populates="user"
    )


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(SAString(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    skill_level: Mapped[str | None] = mapped_column(SAString(32), nullable=True)
    playing_style: Mapped[str | None] = mapped_column(SAString(32), nullable=True)
    budget_min: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    budget_max: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    preferred_tension: Mapped[float | None] = mapped_column(
        Numeric(4, 1),
        nullable=True,
    )
    game_type: Mapped[str | None] = mapped_column(SAString(16), nullable=True)
    frequency_per_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pref_attack: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pref_comfort: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pref_control: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pref_durability: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pref_elasticity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pref_sound: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pref_string_movement: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pref_tension_retention: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pref_value_for_money: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship(back_populates="profile")


class StringCatalogItem(Base):
    __tablename__ = "string_catalog_items"

    id: Mapped[str] = mapped_column(SAString(36), primary_key=True, default=_uuid)
    brand: Mapped[str] = mapped_column(SAString(100), index=True)
    model_name: Mapped[str] = mapped_column(SAString(100), index=True)
    normalized_name: Mapped[str] = mapped_column(SAString(255), unique=True, index=True)
    price_rm: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    attack: Mapped[float] = mapped_column(Numeric(4, 2), default=0.5)
    comfort: Mapped[float] = mapped_column(Numeric(4, 2), default=0.5)
    control: Mapped[float] = mapped_column(Numeric(4, 2), default=0.5)
    durability: Mapped[float] = mapped_column(Numeric(4, 2), default=0.5)
    elasticity: Mapped[float] = mapped_column(Numeric(4, 2), default=0.5)
    sound: Mapped[float] = mapped_column(Numeric(4, 2), default=0.5)
    string_movement: Mapped[float] = mapped_column(Numeric(4, 2), default=0.5)
    tension_retention: Mapped[float] = mapped_column(Numeric(4, 2), default=0.5)
    value_for_money: Mapped[float] = mapped_column(Numeric(4, 2), default=0.5)
    beginner_fit_score: Mapped[float] = mapped_column(Numeric(4, 2), default=0.5)
    stability_score: Mapped[float] = mapped_column(Numeric(4, 2), default=0.5)
    all_round_score: Mapped[float] = mapped_column(Numeric(4, 2), default=0.5)
    source_item_id: Mapped[str | None] = mapped_column(SAString(64), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    bookings: Mapped[list["Booking"]] = relationship(back_populates="string_item")


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(SAString(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    string_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("string_catalog_items.id"),
        index=True,
    )
    racket_brand: Mapped[str | None] = mapped_column(SAString(100), nullable=True)
    racket_model: Mapped[str | None] = mapped_column(SAString(100), nullable=True)
    requested_tension: Mapped[float | None] = mapped_column(
        Numeric(4, 1),
        nullable=True,
    )
    drop_off_datetime: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(SAString(30), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship(back_populates="bookings")
    string_item: Mapped["StringCatalogItem"] = relationship(back_populates="bookings")
    status_history: Mapped[list["BookingStatusHistory"]] = relationship(
        back_populates="booking",
        cascade="all, delete-orphan",
        order_by="BookingStatusHistory.changed_at.asc()",
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
        ForeignKey("users.id"),
        nullable=True,
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    booking: Mapped["Booking"] = relationship(back_populates="status_history")
    changed_by: Mapped["User | None"] = relationship()


class RecommendationLog(Base):
    __tablename__ = "recommendation_logs"

    id: Mapped[str] = mapped_column(SAString(36), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(
        SAString(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    request_json: Mapped[str] = mapped_column(Text)
    recommendation_json: Mapped[str] = mapped_column(Text)
    algorithm_version: Mapped[str] = mapped_column(SAString(80), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user: Mapped["User | None"] = relationship(back_populates="recommendation_logs")


class PasswordResetCode(Base):
    __tablename__ = "password_reset_codes"

    id: Mapped[str] = mapped_column(SAString(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    phone_number: Mapped[str] = mapped_column(SAString(20), index=True)
    code_hash: Mapped[str] = mapped_column(SAString(255))
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
