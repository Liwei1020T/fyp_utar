from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import JSON
from sqlalchemy import String as SAString
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.adapters.persistence.sqlalchemy.base import Base


class StoreBusinessHours(Base):
    __tablename__ = "store_business_hours"

    id: Mapped[str] = mapped_column(SAString(32), primary_key=True, default="main")
    days_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    special_closed_dates: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
