from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import String as SAString
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.adapters.persistence.sqlalchemy.base import Base
from app.adapters.persistence.sqlalchemy.models.common import generate_uuid


class Racket(Base):
    __tablename__ = "rackets"

    id: Mapped[str] = mapped_column(
        SAString(36), primary_key=True, default=generate_uuid
    )
    user_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    nickname: Mapped[str] = mapped_column(SAString(80))
    brand: Mapped[str] = mapped_column(SAString(100))
    model: Mapped[str] = mapped_column(SAString(100))
    weight_class: Mapped[str | None] = mapped_column(SAString(30), nullable=True)
    balance_point: Mapped[str | None] = mapped_column(SAString(50), nullable=True)
    grip_size: Mapped[str | None] = mapped_column(SAString(30), nullable=True)
    preferred_use: Mapped[str | None] = mapped_column(SAString(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class BookingFeedback(Base):
    __tablename__ = "booking_feedback"
    __table_args__ = (
        CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="ck_booking_feedback_rating",
        ),
    )

    id: Mapped[str] = mapped_column(
        SAString(36), primary_key=True, default=generate_uuid
    )
    booking_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    rating: Mapped[int] = mapped_column(Integer)
    string_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    service_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentiment_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
