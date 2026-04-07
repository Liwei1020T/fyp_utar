from __future__ import annotations

from dataclasses import dataclass

from app.domain.auth.entities import UserRole
from app.domain.booking.entities import BookingRecord
from app.ports.repositories.booking_repository import BookingRepository
from app.shared.errors import BadRequestError
from app.shared.errors import NotFoundError


@dataclass
class AddBookingUpdateUseCase:
    booking_repository: BookingRepository

    def execute(
        self,
        *,
        booking_id: str,
        author_user_id: str,
        author_role: str,
        comment: str | None,
        photo_path: str | None,
        photo_original_name: str | None,
        photo_content_type: str | None,
    ) -> BookingRecord:
        booking = self.booking_repository.get_by_id(booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")
        if author_role == UserRole.CUSTOMER.value and booking.user_id != author_user_id:
            raise NotFoundError("Booking not found")

        normalized_comment = comment.strip() if comment else None
        if normalized_comment is None and photo_path is None:
            raise BadRequestError("Provide a comment or photo")

        return self.booking_repository.add_update(
            booking_id=booking_id,
            author_user_id=author_user_id,
            author_role=author_role,
            comment=normalized_comment,
            photo_path=photo_path,
            photo_original_name=photo_original_name,
            photo_content_type=photo_content_type,
        )
