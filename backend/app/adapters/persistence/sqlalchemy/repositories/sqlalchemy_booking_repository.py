from __future__ import annotations

import re

from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.adapters.persistence.sqlalchemy.models import Booking
from app.adapters.persistence.sqlalchemy.models import BookingStatusHistory
from app.adapters.persistence.sqlalchemy.models import BookingUpdate
from app.adapters.persistence.sqlalchemy.models import StoreBusinessHours
from app.adapters.persistence.sqlalchemy.models import StringCatalogItem
from app.adapters.persistence.sqlalchemy.models import User
from app.adapters.persistence.sqlalchemy.models.racket_feedback import Racket
from app.adapters.persistence.sqlalchemy.repositories.mappers import to_booking_record
from app.domain.booking.entities import BookingRecord
from app.domain.booking.enums import BookingStatus
from app.domain.booking.policies import booking_order_code
from app.domain.store.entities import BookedSlot
from app.domain.store.policies import ACTIVE_QUEUE_STATUSES
from app.shared.constants import STORE_ID
from app.shared.pagination import Page


ORDER_CODE_PATTERN = re.compile(r"ORD-[A-F0-9]{5}")
CHECK_IN_REFERENCE_PATTERN = re.compile(r"CHK-[A-F0-9]{8}")
LIVE_REFERENCE_PATTERN = re.compile(r"LIVE-[A-F0-9]{8}")
UUID_PATTERN = re.compile(
    r"[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}"
)


BOOKING_SORT_COLUMNS = {
    "created_at": Booking.created_at,
    "updated_at": Booking.updated_at,
    "status": Booking.status,
    "drop_off_datetime": Booking.drop_off_datetime,
}


class SqlAlchemyBookingRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _detail_query(self):
        return select(Booking).options(
            joinedload(Booking.string_item),
            joinedload(Booking.user),
            joinedload(Booking.status_history).joinedload(
                BookingStatusHistory.changed_by
            ),
            joinedload(Booking.updates).joinedload(BookingUpdate.author),
        )

    def lock_slot_capacity(self) -> None:
        self.db.execute(
            select(StoreBusinessHours.id)
            .where(StoreBusinessHours.id == STORE_ID)
            .with_for_update()
        ).scalar_one()

    def create_booking(
        self,
        *,
        user_id: str,
        string_id: str,
        racket_id: str | None = None,
        racket_brand: str | None,
        racket_model: str | None,
        requested_tension: float | None,
        drop_off_datetime,
        expected_completion_datetime,
        notes: str | None,
        status: str,
        changed_by_user_id: str | None,
        service_method: str = "counter_dropoff",
    ) -> BookingRecord:
        booking = Booking(
            user_id=user_id,
            string_id=string_id,
            racket_id=racket_id,
            racket_brand=racket_brand,
            racket_model=racket_model,
            requested_tension=requested_tension,
            drop_off_datetime=drop_off_datetime,
            expected_completion_datetime=expected_completion_datetime,
            notes=notes,
            service_method=service_method,
            status=status,
        )
        self.db.add(booking)
        self.db.flush()
        self.db.add(
            BookingStatusHistory(
                booking_id=booking.id,
                new_status=status,
                changed_by_user_id=changed_by_user_id,
            )
        )
        self.db.flush()
        self.db.expire_all()
        refreshed = self.get_by_id(booking.id)
        assert refreshed is not None
        return refreshed

    def get_owned_racket_identity(
        self,
        *,
        racket_id: str,
        user_id: str,
    ) -> tuple[str, str] | None:
        row = self.db.execute(
            select(Racket.brand, Racket.model).where(
                Racket.id == racket_id,
                Racket.user_id == user_id,
            )
        ).one_or_none()
        return (row.brand, row.model) if row is not None else None

    def get_by_id(self, booking_id: str) -> BookingRecord | None:
        booking = (
            self.db.execute(self._detail_query().where(Booking.id == booking_id))
            .unique()
            .scalar_one_or_none()
        )
        return to_booking_record(booking) if booking else None

    def get_by_id_for_update(self, booking_id: str) -> BookingRecord | None:
        locked_id = self.db.execute(
            select(Booking.id).where(Booking.id == booking_id).with_for_update()
        ).scalar_one_or_none()
        return self.get_by_id(locked_id) if locked_id else None

    def list_by_user(self, user_id: str) -> Page[BookingRecord]:
        items = (
            self.db.execute(
                self._detail_query()
                .where(Booking.user_id == user_id)
                .order_by(Booking.created_at.desc())
            )
            .unique()
            .scalars()
            .all()
        )
        records = [to_booking_record(item) for item in items]
        return Page(items=records, total=len(records), limit=None, offset=0)

    def list_admin(
        self,
        *,
        status: str | None,
        search: str | None,
        sort_by: str,
        sort_order: str,
        limit: int | None,
        offset: int,
    ) -> Page[BookingRecord]:
        query = self._detail_query()
        count_query = select(func.count()).select_from(Booking)

        if status:
            status_filter = Booking.status == status
            query = query.where(status_filter)
            count_query = count_query.where(status_filter)

        if search:
            search_term = search.strip()
            term = f"%{search_term}%"
            query = query.join(Booking.string_item).join(Booking.user)
            count_query = count_query.join(Booking.string_item).join(Booking.user)
            booking_id_term = term
            normalized_code = search_term.upper()
            if normalized_code.startswith("ORD-") and len(normalized_code) > 4:
                booking_id_term = f"{normalized_code[4:]}%"
            search_filter = or_(
                Booking.id.ilike(booking_id_term),
                Booking.racket_brand.ilike(term),
                Booking.racket_model.ilike(term),
                StringCatalogItem.display_name.ilike(term),
                StringCatalogItem.original_brand_label.ilike(term),
                StringCatalogItem.model_name.ilike(term),
                User.phone_number.ilike(term),
                User.username.ilike(term),
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        total = self.db.execute(count_query).scalar_one()
        sort_column = BOOKING_SORT_COLUMNS[sort_by]
        if sort_order == "desc":
            query = query.order_by(sort_column.desc(), Booking.created_at.desc())
        else:
            query = query.order_by(sort_column.asc(), Booking.created_at.desc())
        if limit is not None:
            query = query.limit(limit).offset(offset)

        items = self.db.execute(query).unique().scalars().all()
        return Page(
            items=[to_booking_record(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    def update_status(
        self,
        *,
        booking_id: str,
        next_status: str,
        expected_completion_datetime,
        update_expected_completion_datetime: bool,
        changed_by_user_id: str | None,
        note: str | None,
    ) -> BookingRecord:
        booking = self.db.get(Booking, booking_id)
        assert booking is not None
        previous_status = booking.status
        status_changed = previous_status != next_status
        booking.status = next_status
        if update_expected_completion_datetime:
            booking.expected_completion_datetime = expected_completion_datetime
        if status_changed:
            self.db.add(
                BookingStatusHistory(
                    booking_id=booking.id,
                    new_status=next_status,
                    changed_by_user_id=changed_by_user_id,
                    note=note,
                )
            )
        self.db.flush()
        self.db.expire_all()
        refreshed = self.get_by_id(booking_id)
        assert refreshed is not None
        return refreshed

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
    ) -> BookingRecord:
        self.db.add(
            BookingUpdate(
                booking_id=booking_id,
                author_user_id=author_user_id,
                author_role=author_role,
                comment=comment,
                photo_path=photo_path,
                photo_original_name=photo_original_name,
                photo_content_type=photo_content_type,
                photo_type=photo_type,
            )
        )
        self.db.flush()
        self.db.expire_all()
        refreshed = self.get_by_id(booking_id)
        assert refreshed is not None
        return refreshed

    def list_slot_bookings(self) -> list[BookedSlot]:
        rows = self.db.execute(
            select(Booking.drop_off_datetime, Booking.status).where(
                Booking.drop_off_datetime.is_not(None),
                Booking.status.not_in(
                    [BookingStatus.CANCELLED.value, BookingStatus.REJECTED.value]
                ),
            )
        ).all()
        return [
            BookedSlot(
                drop_off_datetime=row.drop_off_datetime,
                status=row.status,
            )
            for row in rows
            if row.drop_off_datetime is not None
        ]

    def get_by_order_code(self, order_code: str) -> BookingRecord | None:
        items = self.db.execute(self._detail_query()).unique().scalars().all()
        normalized = order_code.strip().upper()
        for booking in items:
            if booking_order_code(booking.id) == normalized:
                return to_booking_record(booking)
        return None

    def list_active_queue(self) -> list[BookingRecord]:
        items = (
            self.db.execute(
                self._detail_query()
                .where(Booking.status.in_(ACTIVE_QUEUE_STATUSES))
                .order_by(Booking.drop_off_datetime.asc(), Booking.created_at.asc())
            )
            .unique()
            .scalars()
            .all()
        )
        return [to_booking_record(item) for item in items]

    def list_all_for_analytics(self) -> list[BookingRecord]:
        items = self.db.execute(self._detail_query()).unique().scalars().all()
        return [to_booking_record(item) for item in items]

    def find_active_by_reference(self, reference: str) -> BookingRecord | None:
        normalized = reference.strip().upper()
        if not normalized:
            return None

        query = self._detail_query().where(
            Booking.status.not_in(
                [
                    BookingStatus.CANCELLED.value,
                    BookingStatus.REJECTED.value,
                    BookingStatus.COMPLETED.value,
                ]
            )
        )

        if ORDER_CODE_PATTERN.fullmatch(normalized):
            query = query.where(func.upper(Booking.id).like(f"{normalized[4:]}%"))
        elif CHECK_IN_REFERENCE_PATTERN.fullmatch(normalized):
            query = query.where(func.upper(Booking.id).like(f"{normalized[4:]}%"))
        elif LIVE_REFERENCE_PATTERN.fullmatch(normalized):
            query = query.where(func.upper(Booking.id).like(f"{normalized[5:]}%"))
        else:
            if not UUID_PATTERN.fullmatch(normalized):
                return None
            query = query.where(func.upper(Booking.id) == normalized)

        booking = (
            self.db.execute(
                query.order_by(
                    Booking.drop_off_datetime.asc(), Booking.created_at.asc()
                ).limit(1)
            )
            .unique()
            .scalars()
            .first()
        )
        if booking is None:
            return None
        return to_booking_record(booking)
