from decimal import Decimal

from sqlalchemy import delete
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import BOOKING_STATUS_TRANSITIONS
from app.core.constants import BookingStatus
from app.core.exceptions import BadRequestError
from app.core.exceptions import ConflictError
from app.core.exceptions import NotFoundError
from app.db.models import AppUser
from app.db.models import Booking
from app.db.models import BookingStatusHistory
from app.db.models import String
from app.db.session import create_all_tables
from app.db.session import SessionLocal


class BookingService:
    def reset(self) -> None:
        create_all_tables()
        with SessionLocal() as db:
            db.execute(delete(BookingStatusHistory))
            db.execute(delete(Booking))
            db.commit()

    def create(self, db: Session, *, customer_user_id: str, payload: dict) -> dict:
        string_item = self._require_active_string(db, payload["string_id"])
        self._validate_requested_tension(string_item, payload.get("requested_tension"))

        booking = Booking(
            customer_user_id=customer_user_id,
            string_id=string_item.id,
            racket_brand=payload.get("racket_brand"),
            racket_model=payload.get("racket_model"),
            requested_tension=payload.get("requested_tension"),
            appointment_date=payload.get("appointment_date"),
            appointment_slot=payload.get("appointment_slot"),
            notes=payload.get("notes"),
            status=BookingStatus.PENDING.value,
        )
        db.add(booking)
        db.flush()
        db.add(
            BookingStatusHistory(
                booking_id=booking.id,
                old_status=None,
                new_status=BookingStatus.PENDING.value,
                changed_by_user_id=customer_user_id,
            )
        )
        db.commit()
        db.refresh(booking)
        return self._serialize_booking(db, booking)

    def list_for_customer(self, db: Session, user_id: str) -> list[dict]:
        items = (
            db.execute(
                select(Booking)
                .where(Booking.customer_user_id == user_id)
                .order_by(Booking.created_at.desc())
            )
            .scalars()
            .all()
        )
        return [self._serialize_booking(db, item) for item in items]

    def get_for_customer(
        self, db: Session, booking_id: str, user_id: str
    ) -> dict | None:
        item = db.execute(
            select(Booking).where(
                Booking.id == booking_id,
                Booking.customer_user_id == user_id,
            )
        ).scalar_one_or_none()
        if item is None:
            return None
        return self._serialize_booking(db, item)

    def get_by_id(self, db: Session, booking_id: str) -> dict | None:
        item = db.execute(
            select(Booking).where(Booking.id == booking_id)
        ).scalar_one_or_none()
        if item is None:
            return None
        return self._serialize_booking(db, item)

    def list_all(
        self,
        db: Session,
        *,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        query = (
            select(Booking)
            .join(String, String.id == Booking.string_id)
            .join(AppUser, AppUser.id == Booking.customer_user_id)
        )
        count_query = (
            select(func.count())
            .select_from(Booking)
            .join(String, String.id == Booking.string_id)
            .join(AppUser, AppUser.id == Booking.customer_user_id)
        )

        if status:
            query = query.where(Booking.status == status)
            count_query = count_query.where(Booking.status == status)

        if search:
            term = f"%{search.strip()}%"
            conditions = or_(
                Booking.racket_brand.ilike(term),
                Booking.racket_model.ilike(term),
                String.brand.ilike(term),
                String.model_name.ilike(term),
                AppUser.phone_number.ilike(term),
            )
            query = query.where(conditions)
            count_query = count_query.where(conditions)

        total = db.execute(count_query).scalar_one()
        sort_column = {
            "created_at": Booking.created_at,
            "appointment_date": Booking.appointment_date,
            "status": Booking.status,
            "updated_at": Booking.updated_at,
        }.get(sort_by, Booking.created_at)

        if sort_order == "asc":
            query = query.order_by(
                sort_column.asc().nullslast(), Booking.created_at.asc()
            )
        else:
            query = query.order_by(
                sort_column.desc().nullslast(), Booking.created_at.desc()
            )

        if limit is not None:
            query = query.limit(limit).offset(offset)

        items = db.execute(query).scalars().all()
        return [self._serialize_booking(db, item) for item in items], total

    def update_status(
        self,
        db: Session,
        booking_id: str,
        status: str,
        changed_by_user_id: str | None = None,
    ) -> dict | None:
        item = db.execute(
            select(Booking).where(Booking.id == booking_id)
        ).scalar_one_or_none()
        if item is None:
            return None

        old_status = BookingStatus(item.status)
        next_status = BookingStatus(status)
        allowed_statuses = BOOKING_STATUS_TRANSITIONS.get(old_status, set())
        if next_status not in allowed_statuses:
            raise ConflictError("Invalid booking status transition")
        item.status = next_status.value
        db.add(
            BookingStatusHistory(
                booking_id=booking_id,
                old_status=old_status.value,
                new_status=next_status.value,
                changed_by_user_id=changed_by_user_id,
            )
        )
        db.commit()
        db.refresh(item)
        return self._serialize_booking(db, item)

    def history_for(self, db: Session, booking_id: str) -> list[dict]:
        history = (
            db.execute(
                select(BookingStatusHistory)
                .where(BookingStatusHistory.booking_id == booking_id)
                .order_by(BookingStatusHistory.changed_at)
            )
            .scalars()
            .all()
        )
        return [
            {
                "booking_id": item.booking_id,
                "old_status": item.old_status,
                "new_status": item.new_status,
            }
            for item in history
        ]

    def _serialize_booking(self, db: Session, booking: Booking) -> dict:
        string_item = db.execute(
            select(String).where(String.id == booking.string_id)
        ).scalar_one_or_none()
        string_name = (
            f"{string_item.brand} {string_item.model_name}"
            if string_item is not None
            else booking.string_id
        )
        return {
            "id": booking.id,
            "customer_user_id": booking.customer_user_id,
            "string_id": booking.string_id,
            "string_name": string_name,
            "racket_brand": booking.racket_brand,
            "racket_model": booking.racket_model,
            "requested_tension": self._decimal_to_float(booking.requested_tension),
            "appointment_date": booking.appointment_date.isoformat()
            if booking.appointment_date is not None
            else None,
            "appointment_slot": booking.appointment_slot,
            "notes": booking.notes,
            "status": booking.status,
            "created_at": booking.created_at.isoformat()
            if booking.created_at is not None
            else None,
            "updated_at": booking.updated_at.isoformat()
            if booking.updated_at is not None
            else None,
        }

    @staticmethod
    def _decimal_to_float(value: Decimal | None) -> float | None:
        if value is None:
            return None
        return float(value)

    @staticmethod
    def _require_active_string(db: Session, string_id: str) -> String:
        string_item = db.execute(
            select(String).where(String.id == string_id)
        ).scalar_one_or_none()
        if string_item is None:
            raise NotFoundError("String not found")
        if not string_item.is_active:
            raise ConflictError("Booking must reference an active string")
        return string_item

    @staticmethod
    def _validate_requested_tension(
        string_item: String,
        requested_tension: Decimal | None,
    ) -> None:
        if requested_tension is None:
            return
        minimum = string_item.recommended_tension_min
        maximum = string_item.recommended_tension_max
        if minimum is not None and requested_tension < minimum:
            raise BadRequestError("Requested tension is outside this string range")
        if maximum is not None and requested_tension > maximum:
            raise BadRequestError("Requested tension is outside this string range")


booking_service = BookingService()
