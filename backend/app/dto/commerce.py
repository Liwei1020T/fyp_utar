from __future__ import annotations

from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


PaymentMethod = Literal[
    "card",
    "online_banking",
    "e_wallet",
    "wallet_balance",
]
PaymentStatus = Literal["pending", "paid", "failed", "cancelled"]
PaymentType = Literal["booking_payment", "wallet_top_up"]
WalletTransactionType = Literal["top_up", "booking_payment"]
WalletDirection = Literal["credit", "debit"]


class BookingPaymentPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: PaymentMethod
    expected_amount: float | None = Field(default=None, gt=0, le=100000)


class WalletTopUpPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: float = Field(ge=1, le=5000)
    method: Literal["card", "online_banking", "e_wallet"]


class AdminPaymentStatusPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["paid", "failed", "cancelled"]


class PaymentOut(BaseModel):
    id: str
    booking_id: str | None
    user_id: str
    method: PaymentMethod
    status: PaymentStatus
    amount: float
    type: PaymentType
    reference: str
    note: str | None
    created_at: str


class BookingPaymentQuoteOut(BaseModel):
    booking_id: str
    string_fee: float
    service_fee: float
    total_amount: float
    wallet_balance: float
    active_payment: PaymentOut | None


class WalletTransactionOut(BaseModel):
    id: str
    user_id: str
    type: WalletTransactionType
    direction: WalletDirection
    status: Literal["completed"]
    amount: float
    description: str
    created_at: str
    related_booking_id: str | None
    method_label: str | None


class WalletOut(BaseModel):
    user_id: str
    available_balance: float
    pending_top_up: float
    lifetime_top_ups: float
    transactions: list[WalletTransactionOut]
