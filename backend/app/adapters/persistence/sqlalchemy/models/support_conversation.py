from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String as SAString
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.adapters.persistence.sqlalchemy.base import Base
from app.adapters.persistence.sqlalchemy.models.common import generate_uuid


class SupportConversation(Base):
    """One reusable general-support thread per player.

    Booking support remains in ``booking_conversations`` so existing booking
    history and routes stay stable. This table is intentionally booking-free.
    """

    __tablename__ = "support_conversations"
    __table_args__ = (
        CheckConstraint(
            "state IN ('waiting_admin', 'admin_joined', 'resolved', 'closed')",
            name="ck_support_conversations_state",
        ),
        UniqueConstraint("player_id", name="uq_support_conversations_player"),
    )

    id: Mapped[str] = mapped_column(
        SAString(36), primary_key=True, default=generate_uuid
    )
    player_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    state: Mapped[str] = mapped_column(
        SAString(20),
        default="waiting_admin",
        server_default="waiting_admin",
        index=True,
    )
    support_requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    player_last_read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    admin_last_read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SupportConversationMessage(Base):
    __tablename__ = "support_conversation_messages"

    id: Mapped[str] = mapped_column(
        SAString(36), primary_key=True, default=generate_uuid
    )
    conversation_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("support_conversations.id", ondelete="CASCADE"),
        index=True,
    )
    author_user_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("users.id"),
        index=True,
    )
    author_role: Mapped[str] = mapped_column(SAString(20))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
