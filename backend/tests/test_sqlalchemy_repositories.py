from __future__ import annotations

from datetime import datetime
from datetime import UTC

from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_booking_repository import (
    SqlAlchemyBookingRepository,
)
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_catalog_repository import (
    SqlAlchemyCatalogRepository,
)
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from app.adapters.persistence.sqlalchemy.session import SessionLocal
from app.domain.auth.entities import AuthProvider
from app.domain.auth.entities import UserRole
from app.domain.booking.enums import BookingStatus


def test_sqlalchemy_booking_repository_creates_history_entries() -> None:
    with SessionLocal() as db:
        user_repository = SqlAlchemyUserRepository(db)
        catalog_repository = SqlAlchemyCatalogRepository(db)
        booking_repository = SqlAlchemyBookingRepository(db)

        user = user_repository.create_user(
            username="repo-user",
            phone_number="+60135550000",
            password_hash="hashed-password",
            role=UserRole.CUSTOMER.value,
            auth_provider=AuthProvider.LOCAL.value,
        )
        string_item = catalog_repository.list_active_catalog()[0]

        booking = booking_repository.create_booking(
            user_id=user.id,
            string_id=string_item.id,
            racket_brand="Yonex",
            racket_model="Astrox",
            requested_tension=25,
            drop_off_datetime=None,
            expected_completion_datetime=None,
            notes="Repository test booking",
            status=BookingStatus.AWAITING_DROPOFF.value,
            changed_by_user_id=user.id,
        )

        assert booking.status == BookingStatus.AWAITING_DROPOFF.value
        assert booking.order_code.startswith("ORD-")
        assert len(booking.status_history) == 1
        assert (
            booking.status_history[0].new_status == BookingStatus.AWAITING_DROPOFF.value
        )
        by_order_code = booking_repository.get_by_order_code(booking.order_code)
        assert by_order_code is not None
        assert by_order_code.id == booking.id

        updated = booking_repository.update_status(
            booking_id=booking.id,
            next_status=BookingStatus.IN_PROGRESS.value,
            expected_completion_datetime=datetime(2026, 4, 23, 18, 30, tzinfo=UTC),
            update_expected_completion_datetime=True,
            changed_by_user_id=user.id,
            note="Checked in for stringing.",
        )

        assert updated.status == BookingStatus.IN_PROGRESS.value
        assert updated.expected_completion_datetime is not None
        assert len(updated.status_history) == 2
        assert updated.status_history[-1].note == "Checked in for stringing."

        eta_only = booking_repository.update_status(
            booking_id=booking.id,
            next_status=BookingStatus.IN_PROGRESS.value,
            expected_completion_datetime=None,
            update_expected_completion_datetime=True,
            changed_by_user_id=user.id,
            note=None,
        )
        assert eta_only.status == BookingStatus.IN_PROGRESS.value
        assert eta_only.expected_completion_datetime is None
        assert len(eta_only.status_history) == 2
