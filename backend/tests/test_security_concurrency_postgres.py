from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from datetime import timezone
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import delete
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.adapters.persistence.sqlalchemy.models import Booking
from app.adapters.persistence.sqlalchemy.models import CheckInToken
from app.adapters.persistence.sqlalchemy.models import PasswordResetCode
from app.adapters.persistence.sqlalchemy.models import User
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_booking_repository import (
    SqlAlchemyBookingRepository,
)
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_catalog_repository import (
    SqlAlchemyCatalogRepository,
)
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_password_reset_repository import (
    SqlAlchemyPasswordResetRepository,
)
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from app.adapters.persistence.sqlalchemy.seed import ensure_catalog_seeded
from app.domain.auth.entities import AuthProvider
from app.domain.auth.entities import UserRole
from app.domain.store.policies import hash_check_in_token
from app.entrypoints.api.dependencies import CurrentUser
from app.entrypoints.api.routes.booking_routes import create_check_in_token
from app.use_cases.auth.request_password_reset import RequestPasswordResetUseCase


POSTGRES_TEST_DATABASE_URL = os.environ.get("POSTGRES_TEST_DATABASE_URL")


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 7, 31, 4, 0, tzinfo=timezone.utc)


class FastPasswordHasher:
    def normalize_phone_number(self, value: str) -> str:
        return value

    def validate_local_password(self, value: str) -> str:
        return value

    def hash_password(self, value: str) -> str:
        return f"hash:{value}"

    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        return password_hash == self.hash_password(plain_password)


@pytest.mark.skipif(
    not POSTGRES_TEST_DATABASE_URL,
    reason="POSTGRES_TEST_DATABASE_URL is required for row-lock verification",
)
def test_concurrent_reset_and_check_in_requests_keep_one_active_token() -> None:
    assert POSTGRES_TEST_DATABASE_URL is not None
    engine = create_engine(POSTGRES_TEST_DATABASE_URL, pool_pre_ping=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    user_id: str | None = None
    booking_id: str | None = None
    phone_number = f"+6017{uuid4().int % 100_000_000:08d}"

    try:
        with session_factory() as db:
            ensure_catalog_seeded(db)
            db.commit()
            user = SqlAlchemyUserRepository(db).create_user(
                username="postgres-security-test",
                phone_number=phone_number,
                password_hash="not-used",
                role=UserRole.CUSTOMER.value,
                auth_provider=AuthProvider.LOCAL.value,
            )
            user_id = user.id
            string_id = SqlAlchemyCatalogRepository(db).list_active_catalog()[0].id
            booking = Booking(
                user_id=user.id,
                string_id=string_id,
                status="awaiting_dropoff",
            )
            db.add(booking)
            db.commit()
            db.refresh(booking)
            booking_id = booking.id

        reset_barrier = Barrier(2)

        def request_reset_code() -> None:
            with session_factory() as db:
                reset_barrier.wait()
                RequestPasswordResetUseCase(
                    user_repository=SqlAlchemyUserRepository(db),
                    password_reset_repository=SqlAlchemyPasswordResetRepository(db),
                    password_hasher=FastPasswordHasher(),
                    clock=FixedClock(),
                    expire_minutes=10,
                    dev_preview_enabled=False,
                    is_dev_like=False,
                ).execute(phone_number=phone_number)

        with ThreadPoolExecutor(max_workers=2) as executor:
            list(executor.map(lambda _: request_reset_code(), range(2)))

        qr_barrier = Barrier(2)
        current_user = CurrentUser(
            sub=user_id,
            user_id=user_id,
            phone_number=phone_number,
            role=UserRole.CUSTOMER.value,
        )

        def request_check_in_token() -> str:
            with session_factory() as db:
                qr_barrier.wait()
                return create_check_in_token(
                    booking_id=booking_id,
                    current_user=current_user,
                    booking_repository=SqlAlchemyBookingRepository(db),
                    clock=FixedClock(),
                    db=db,
                ).token

        with ThreadPoolExecutor(max_workers=2) as executor:
            raw_tokens = list(
                executor.map(lambda _: request_check_in_token(), range(2))
            )

        with session_factory() as db:
            assert (
                db.scalar(
                    select(func.count())
                    .select_from(PasswordResetCode)
                    .where(
                        PasswordResetCode.phone_number == phone_number,
                        PasswordResetCode.used_at.is_(None),
                    )
                )
                == 1
            )
            active_qr_hashes = set(
                db.scalars(
                    select(CheckInToken.token_hash).where(
                        CheckInToken.booking_id == booking_id,
                        CheckInToken.used_at.is_(None),
                        CheckInToken.revoked_at.is_(None),
                    )
                )
            )
            assert len(active_qr_hashes) == 1
            assert (
                sum(
                    hash_check_in_token(token) in active_qr_hashes
                    for token in raw_tokens
                )
                == 1
            )
    finally:
        if user_id is not None:
            with session_factory() as db:
                db.execute(
                    delete(PasswordResetCode).where(
                        PasswordResetCode.user_id == user_id
                    )
                )
                if booking_id is not None:
                    db.execute(
                        delete(CheckInToken).where(
                            CheckInToken.booking_id == booking_id
                        )
                    )
                    db.execute(delete(Booking).where(Booking.id == booking_id))
                db.execute(delete(User).where(User.id == user_id))
                db.commit()
        engine.dispose()
