from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String as SAString
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.adapters.persistence.sqlalchemy.base import Base


class BookingConversation(Base):
    __tablename__ = "booking_conversations"
    __table_args__ = (
        CheckConstraint(
            "state IN ('waiting_admin', 'admin_joined', 'resolved', 'closed')",
            name="ck_booking_conversations_state",
        ),
    )

    booking_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        primary_key=True,
    )
    state: Mapped[str] = mapped_column(
        SAString(20),
        default="waiting_admin",
        server_default="waiting_admin",
        index=True,
    )
    support_requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    player_last_read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    admin_last_read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
