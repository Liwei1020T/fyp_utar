from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import String as SAString
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.adapters.persistence.sqlalchemy.base import Base
from app.adapters.persistence.sqlalchemy.models.common import generate_uuid

if TYPE_CHECKING:
    from app.adapters.persistence.sqlalchemy.models.booking import Booking


class StringCatalogItem(Base):
    __tablename__ = "string_catalog_items"

    id: Mapped[str] = mapped_column(SAString(36), primary_key=True, default=generate_uuid)
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
    stock_level: Mapped[int] = mapped_column(Integer, default=8)
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
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
