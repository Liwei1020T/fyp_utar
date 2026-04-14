from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import String as SAString
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.adapters.persistence.sqlalchemy.base import Base
from app.adapters.persistence.sqlalchemy.models.common import generate_uuid

if TYPE_CHECKING:
    from app.adapters.persistence.sqlalchemy.models.user import User


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(
        SAString(36), primary_key=True, default=generate_uuid
    )
    user_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    skill_level: Mapped[str | None] = mapped_column(SAString(32), nullable=True)
    playing_style: Mapped[str | None] = mapped_column(SAString(32), nullable=True)
    budget_tier: Mapped[str | None] = mapped_column(SAString(32), nullable=True)
    budget_min: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    budget_max: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    preferred_tension: Mapped[float | None] = mapped_column(
        Numeric(4, 1),
        nullable=True,
    )
    game_type: Mapped[str | None] = mapped_column(SAString(16), nullable=True)
    frequency_per_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preferred_feel: Mapped[str | None] = mapped_column(SAString(32), nullable=True)
    recent_goal: Mapped[str | None] = mapped_column(SAString(500), nullable=True)
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
