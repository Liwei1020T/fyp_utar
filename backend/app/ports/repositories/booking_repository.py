from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.domain.booking.entities import BookingRecord
from app.shared.pagination import Page


class BookingRepository(Protocol):
    def create_booking(
        self,
        *,
        user_id: str,
        string_id: str,
        racket_brand: str | None,
        racket_model: str | None,
        requested_tension: float | None,
        drop_off_datetime: datetime | None,
        expected_completion_datetime: datetime | None = None,
        notes: str | None,
        status: str,
        changed_by_user_id: str | None,
    ) -> BookingRecord: ...

    def get_by_id(self, booking_id: str) -> BookingRecord | None: ...

    def get_by_order_code(self, order_code: str) -> BookingRecord | None: ...

    def list_by_user(self, user_id: str) -> Page[BookingRecord]: ...

    def list_admin(
        self,
        *,
        status: str | None,
        search: str | None,
        sort_by: str,
        sort_order: str,
        limit: int | None,
        offset: int,
    ) -> Page[BookingRecord]: ...

    def update_status(
        self,
        *,
        booking_id: str,
        next_status: str,
        changed_by_user_id: str | None,
        note: str | None,
    ) -> BookingRecord: ...

    def add_update(
        self,
        *,
        booking_id: str,
        author_user_id: str,
        author_role: str,
        comment: str | None,
        photo_path: str | None,
        photo_original_name: str | None,
        photo_content_type: str | None,
        photo_type: str | None = None,
    ) -> BookingRecord: ...

    def list_slot_bookings(self) -> list[BookingRecord]: ...

    def list_active_queue(self) -> list[BookingRecord]: ...

    def list_all_for_analytics(self) -> list[BookingRecord]: ...

    def find_active_by_reference(self, reference: str) -> BookingRecord | None: ...
