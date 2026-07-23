from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String as SAString
from sqlalchemy import UniqueConstraint
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.adapters.persistence.sqlalchemy.base import Base
from app.adapters.persistence.sqlalchemy.models.common import generate_uuid


class NotificationRead(Base):
    __tablename__ = "notification_reads"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "event_id",
            name="uq_notification_reads_user_event",
        ),
    )

    id: Mapped[str] = mapped_column(
        SAString(36), primary_key=True, default=generate_uuid
    )
    user_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    event_id: Mapped[str] = mapped_column(SAString(160))
    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
