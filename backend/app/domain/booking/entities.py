from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BookingStatusHistoryEntry:
    old_status: str | None
    new_status: str
    changed_by_user_id: str | None
    changed_by_phone_number: str | None
    note: str | None
    changed_at: datetime | None


@dataclass(frozen=True)
class BookingRecord:
    id: str
    user_id: str
    string_id: str
    string_name: str
    customer_phone_number: str | None
    customer_username: str | None
    racket_brand: str | None
    racket_model: str | None
    requested_tension: float | None
    drop_off_datetime: datetime | None
    notes: str | None
    status: str
    created_at: datetime | None
    updated_at: datetime | None
    latest_admin_note: str | None
    status_history: list[BookingStatusHistoryEntry]

