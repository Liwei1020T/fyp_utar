from __future__ import annotations

from dataclasses import dataclass

from app.domain.booking.entities import BookingRecord
from app.ports.repositories.booking_repository import BookingRepository
from app.shared.pagination import Page


@dataclass
class ListAdminBookingsUseCase:
    booking_repository: BookingRepository

    def execute(
        self,
        *,
        status: str | None,
        search: str | None,
        sort_by: str,
        sort_order: str,
        limit: int | None,
        offset: int,
    ) -> Page[BookingRecord]:
        return self.booking_repository.list_admin(
            status=status,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )
