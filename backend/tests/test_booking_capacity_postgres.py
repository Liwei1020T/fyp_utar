from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from datetime import timedelta
from threading import Barrier
from typing import Literal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy import delete
from sqlalchemy.orm import sessionmaker

from app.adapters.persistence.sqlalchemy.models import Booking
from app.adapters.persistence.sqlalchemy.models import User
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_booking_repository import (
    SqlAlchemyBookingRepository,
)
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_catalog_repository import (
    SqlAlchemyCatalogRepository,
)
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_store_repository import (
    SqlAlchemyStoreRepository,
)
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from app.adapters.persistence.sqlalchemy.seed import ensure_catalog_seeded
from app.adapters.persistence.sqlalchemy.seed import ensure_store_defaults
from app.adapters.services.system_clock import SystemClock
from app.domain.auth.entities import AuthProvider
from app.domain.auth.entities import UserRole
from app.shared.errors import ConflictError
from app.use_cases.booking.create_booking import CreateBookingUseCase


POSTGRES_TEST_DATABASE_URL = os.environ.get("POSTGRES_TEST_DATABASE_URL")


def next_weekday(weekday: int) -> date:
    today = date.today()
    days_ahead = (weekday - today.weekday()) % 7 or 7
    return today + timedelta(days=days_ahead)


@pytest.mark.skipif(
    not POSTGRES_TEST_DATABASE_URL,
    reason="POSTGRES_TEST_DATABASE_URL is required for row-lock verification",
)
def test_concurrent_booking_creation_never_exceeds_slot_capacity() -> None:
    assert POSTGRES_TEST_DATABASE_URL is not None
    engine = create_engine(POSTGRES_TEST_DATABASE_URL, pool_pre_ping=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    user_id: str | None = None

    try:
        with session_factory() as db:
            ensure_catalog_seeded(db)
            ensure_store_defaults(db)
            db.commit()

            user = SqlAlchemyUserRepository(db).create_user(
                username="postgres-capacity-test",
                phone_number=f"+6018{uuid4().int % 100_000_000:08d}",
                password_hash="not-used",
                role=UserRole.CUSTOMER.value,
                auth_provider=AuthProvider.LOCAL.value,
            )
            user_id = user.id
            string_id = SqlAlchemyCatalogRepository(db).list_active_catalog()[0].id
            hours = SqlAlchemyStoreRepository(db).get_business_hours()
            assert hours is not None

        slot_date = next_weekday(0)
        monday = next(day for day in hours.days if day.day == "Monday")
        capacity = monday.max_bookings_per_slot
        slot_id = f"slot-{slot_date.isoformat()}-{monday.open_time}"
        worker_count = capacity + 4
        start_barrier = Barrier(worker_count)

        def create_booking() -> tuple[Literal["created", "conflict"], str | None]:
            with session_factory() as db:
                use_case = CreateBookingUseCase(
                    booking_repository=SqlAlchemyBookingRepository(db),
                    catalog_repository=SqlAlchemyCatalogRepository(db),
                    store_repository=SqlAlchemyStoreRepository(db),
                    clock=SystemClock(),
                    store_timezone="Asia/Kuala_Lumpur",
                )
                start_barrier.wait()
                try:
                    booking = use_case.execute(
                        user_id=user_id,
                        string_id=string_id,
                        racket_brand="Yonex",
                        racket_model="Astrox 88D",
                        requested_tension=25,
                        slot_id=slot_id,
                        drop_off_datetime=None,
                        notes="PostgreSQL concurrency verification",
                    )
                except ConflictError:
                    return ("conflict", None)
                return ("created", booking.id)

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            results = list(
                executor.map(lambda _: create_booking(), range(worker_count))
            )

        assert sum(result == "created" for result, _ in results) == capacity
        assert sum(result == "conflict" for result, _ in results) == 4
    finally:
        if user_id is not None:
            with session_factory() as db:
                db.execute(delete(Booking).where(Booking.user_id == user_id))
                db.execute(delete(User).where(User.id == user_id))
                db.commit()
        engine.dispose()
