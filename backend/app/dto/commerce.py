from __future__ import annotations

from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict


PaymentMethod = Literal[
    "qr_transfer",
    "cash",
    "wallet_balance",
]
PaymentStatus = Literal["pending", "paid", "failed", "cancelled"]
PaymentType = Literal["booking_payment", "wallet_top_up"]
WalletTransactionType = Literal["top_up", "booking_payment"]
WalletDirection = Literal["credit", "debit"]


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
    proof_url: str | None
    created_at: str


class BookingPaymentQuoteOut(BaseModel):
    booking_id: str
    string_fee: float
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
