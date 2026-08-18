from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import String as SAString
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.adapters.persistence.sqlalchemy.base import Base
from app.adapters.persistence.sqlalchemy.models.common import generate_uuid


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint(
            "method <> 'qr_transfer' OR proof_path IS NOT NULL",
            name="ck_payments_qr_transfer_proof",
        ),
    )

    id: Mapped[str] = mapped_column(
        SAString(36), primary_key=True, default=generate_uuid
    )
    booking_id: Mapped[str | None] = mapped_column(
        SAString(36),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    method: Mapped[str] = mapped_column(SAString(32))
    status: Mapped[str] = mapped_column(
        SAString(20),
        default="pending",
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    payment_type: Mapped[str] = mapped_column(SAString(32), index=True)
    reference: Mapped[str] = mapped_column(SAString(80), unique=True, index=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    proof_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id: Mapped[str] = mapped_column(
        SAString(36), primary_key=True, default=generate_uuid
    )
    user_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    payment_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("payments.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    transaction_type: Mapped[str] = mapped_column(SAString(32))
    direction: Mapped[str] = mapped_column(SAString(12))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    description: Mapped[str] = mapped_column(Text)
    method_label: Mapped[str | None] = mapped_column(SAString(80), nullable=True)
    related_booking_id: Mapped[str | None] = mapped_column(
        SAString(36),
        ForeignKey("bookings.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
