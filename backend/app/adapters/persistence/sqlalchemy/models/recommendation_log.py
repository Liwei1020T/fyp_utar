from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String as SAString
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.adapters.persistence.sqlalchemy.base import Base
from app.adapters.persistence.sqlalchemy.models.common import generate_uuid

if TYPE_CHECKING:
    from app.adapters.persistence.sqlalchemy.models.user import User


class RecommendationLog(Base):
    __tablename__ = "recommendation_logs"

    id: Mapped[str] = mapped_column(SAString(36), primary_key=True, default=generate_uuid)
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
