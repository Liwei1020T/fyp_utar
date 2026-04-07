from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String as SAString
from sqlalchemy import Text
from sqlalchemy import Numeric
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.adapters.persistence.sqlalchemy.base import Base
from app.adapters.persistence.sqlalchemy.models.common import generate_uuid

if TYPE_CHECKING:
    from app.adapters.persistence.sqlalchemy.models.string_catalog_item import (
        StringCatalogItem,
    )
    from app.adapters.persistence.sqlalchemy.models.user import User


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(
        SAString(36), primary_key=True, default=generate_uuid
    )
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
    status: Mapped[str] = mapped_column(
        SAString(30),
        default="awaiting_dropoff",
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

    user: Mapped["User"] = relationship(back_populates="bookings")
    string_item: Mapped["StringCatalogItem"] = relationship(back_populates="bookings")
    status_history: Mapped[list["BookingStatusHistory"]] = relationship(
        back_populates="booking",
        cascade="all, delete-orphan",
        order_by="BookingStatusHistory.changed_at.asc()",
    )
    updates: Mapped[list["BookingUpdate"]] = relationship(
        back_populates="booking",
        cascade="all, delete-orphan",
        order_by="BookingUpdate.created_at.asc()",
    )


class BookingStatusHistory(Base):
    __tablename__ = "booking_status_history"

    id: Mapped[str] = mapped_column(
        SAString(36), primary_key=True, default=generate_uuid
    )
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
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    booking: Mapped["Booking"] = relationship(back_populates="status_history")
    changed_by: Mapped["User | None"] = relationship()


class BookingUpdate(Base):
    __tablename__ = "booking_updates"

    id: Mapped[str] = mapped_column(
        SAString(36), primary_key=True, default=generate_uuid
    )
    booking_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        index=True,
    )
    author_user_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("users.id"),
        index=True,
    )
    author_role: Mapped[str] = mapped_column(SAString(20))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_original_name: Mapped[str | None] = mapped_column(
        SAString(255), nullable=True
    )
    photo_content_type: Mapped[str | None] = mapped_column(SAString(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    booking: Mapped["Booking"] = relationship(back_populates="updates")
    author: Mapped["User"] = relationship()
