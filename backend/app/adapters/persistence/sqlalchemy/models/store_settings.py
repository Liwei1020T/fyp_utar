from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import JSON
from sqlalchemy import Numeric
from sqlalchemy import String as SAString
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.adapters.persistence.sqlalchemy.base import Base


class StoreSettings(Base):
    __tablename__ = "store_settings"

    id: Mapped[str] = mapped_column(SAString(32), primary_key=True, default="main")
    store_name: Mapped[str] = mapped_column(SAString(120))
    store_contact: Mapped[str] = mapped_column(SAString(120))
    support_text: Mapped[str] = mapped_column(Text)
    payment_notes: Mapped[str] = mapped_column(Text)
    booking_notes: Mapped[str] = mapped_column(Text)
    store_policy_text: Mapped[str] = mapped_column(Text)
    address: Mapped[str] = mapped_column(Text)
    trending_string_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    default_service_price: Mapped[float] = mapped_column(
        Numeric(10, 2), default=0, server_default="0"
    )
    notification_settings: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
