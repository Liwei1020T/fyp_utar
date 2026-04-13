from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlalchemy import String as SAString
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.adapters.persistence.sqlalchemy.base import Base
from app.adapters.persistence.sqlalchemy.models.common import generate_uuid

if TYPE_CHECKING:
    from app.adapters.persistence.sqlalchemy.models.booking import Booking
    from app.adapters.persistence.sqlalchemy.models.profile import Profile
    from app.adapters.persistence.sqlalchemy.models.recommendation_log import (
        RecommendationLog,
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        SAString(36), primary_key=True, default=generate_uuid
    )
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
