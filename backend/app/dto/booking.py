from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator

from app.domain.booking.entities import BookingRecord
from app.domain.booking.entities import BookingStatusHistoryEntry
from app.domain.booking.entities import BookingUpdateEntry
from app.domain.booking.enums import BookingStatus
from app.shared.upload_storage import build_signed_media_url
from app.shared.serialization import isoformat_or_none


BookingSortField = Literal["created_at", "updated_at", "status", "drop_off_datetime"]
SortOrder = Literal["asc", "desc"]


class CreateBookingPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    string_id: str
    racket_brand: str | None = None
    racket_model: str | None = None
    requested_tension: float | None = Field(default=None, ge=16, le=35)
    drop_off_datetime: datetime | None = None
    expected_completion_datetime: datetime | None = None
    notes: str | None = None


class UpdateBookingStatusPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(
        pattern="^(awaiting_dropoff|in_progress|ready_for_collection|completed|cancelled|rejected)$"
    )
    expected_completion_datetime: datetime | None = None
    note: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_terminal_note(self) -> "UpdateBookingStatusPayload":
        if self.status in {
            BookingStatus.CANCELLED.value,
            BookingStatus.REJECTED.value,
        } and not (self.note and self.note.strip()):
            raise ValueError("note is required when cancelling or rejecting a booking")
        return self


class BookingStatusHistoryOut(BaseModel):
    old_status: str | None
    new_status: str
    changed_by_user_id: str | None
    changed_by_phone_number: str | None
    note: str | None
    changed_at: str | None


class BookingUpdateOut(BaseModel):
    id: str
    booking_id: str
    author_user_id: str
    author_role: str
    author_phone_number: str | None = None
    comment: str | None = None
    photo_url: str | None = None
    photo_original_name: str | None = None
    photo_content_type: str | None = None
    photo_type: str | None = None
    created_at: str | None = None


class BookingOut(BaseModel):
    id: str
    order_code: str
    user_id: str
    string_id: str
    string_name: str
    customer_phone_number: str | None = None
    customer_username: str | None = None
    racket_brand: str | None = None
    racket_model: str | None = None
    requested_tension: float | None = None
    drop_off_datetime: str | None = None
    expected_completion_datetime: str | None = None
    collection_datetime: str | None = None
    notes: str | None = None
    status: str
    created_at: str | None = None
    updated_at: str | None = None
    latest_admin_note: str | None = None
    status_history: list[BookingStatusHistoryOut] | None = None
    updates: list[BookingUpdateOut] | None = None


def booking_history_to_dto(entry: BookingStatusHistoryEntry) -> BookingStatusHistoryOut:
    return BookingStatusHistoryOut(
        old_status=entry.old_status,
        new_status=entry.new_status,
        changed_by_user_id=entry.changed_by_user_id,
        changed_by_phone_number=entry.changed_by_phone_number,
        note=entry.note,
        changed_at=isoformat_or_none(entry.changed_at),
    )


def booking_update_to_dto(entry: BookingUpdateEntry) -> BookingUpdateOut:
    return BookingUpdateOut(
        id=entry.id,
        booking_id=entry.booking_id,
        author_user_id=entry.author_user_id,
        author_role=entry.author_role,
        author_phone_number=entry.author_phone_number,
        comment=entry.comment,
        photo_url=(
            build_signed_media_url(entry.photo_path) if entry.photo_path else None
        ),
        photo_original_name=entry.photo_original_name,
        photo_content_type=entry.photo_content_type,
        photo_type=entry.photo_type,
        created_at=isoformat_or_none(entry.created_at),
    )


def booking_to_dto(
    booking: BookingRecord,
    *,
    include_user: bool,
    include_history: bool,
) -> BookingOut:
    return BookingOut(
        id=booking.id,
        order_code=booking.order_code,
        user_id=booking.user_id,
        string_id=booking.string_id,
        string_name=booking.string_name,
        customer_phone_number=booking.customer_phone_number if include_user else None,
        customer_username=booking.customer_username if include_user else None,
        racket_brand=booking.racket_brand,
        racket_model=booking.racket_model,
        requested_tension=booking.requested_tension,
        drop_off_datetime=isoformat_or_none(booking.drop_off_datetime),
        expected_completion_datetime=isoformat_or_none(
            booking.expected_completion_datetime
        ),
        collection_datetime=isoformat_or_none(booking.collection_datetime),
        notes=booking.notes,
        status=booking.status,
        created_at=isoformat_or_none(booking.created_at),
        updated_at=isoformat_or_none(booking.updated_at),
        latest_admin_note=booking.latest_admin_note,
        status_history=[
            booking_history_to_dto(entry) for entry in booking.status_history
        ]
        if include_history
        else None,
        updates=[booking_update_to_dto(entry) for entry in booking.updates],
    )


DEFAULT_BOOKING_STATUS = BookingStatus.AWAITING_DROPOFF.value
