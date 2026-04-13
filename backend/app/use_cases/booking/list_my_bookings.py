from __future__ import annotations

from dataclasses import dataclass

from app.domain.booking.entities import BookingRecord
from app.ports.repositories.booking_repository import BookingRepository
from app.shared.pagination import Page


@dataclass
class ListMyBookingsUseCase:
    booking_repository: BookingRepository

    def execute(self, user_id: str) -> Page[BookingRecord]:
        return self.booking_repository.list_by_user(user_id)
