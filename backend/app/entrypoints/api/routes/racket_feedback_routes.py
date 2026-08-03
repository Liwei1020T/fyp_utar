from __future__ import annotations

from typing import cast

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.models.booking import Booking
from app.adapters.persistence.sqlalchemy.models.racket_feedback import BookingFeedback
from app.adapters.persistence.sqlalchemy.models.racket_feedback import Racket
from app.adapters.persistence.sqlalchemy.session import get_db
from app.domain.booking.enums import BookingStatus
from app.dto.racket_feedback import CreateFeedbackPayload
from app.dto.racket_feedback import CreateRacketPayload
from app.dto.racket_feedback import FeedbackOut
from app.dto.racket_feedback import RacketDetailOut
from app.dto.racket_feedback import RacketOut
from app.dto.racket_feedback import RacketServiceHistoryOut
from app.dto.racket_feedback import SentimentTag
from app.dto.racket_feedback import UpdateRacketPayload
from app.entrypoints.api.dependencies import CurrentUser
from app.entrypoints.api.dependencies import get_current_customer
from app.dto.auth import MessageResponse
from app.shared.errors import ConflictError
from app.shared.errors import NotFoundError
from app.shared.serialization import number_to_float


router = APIRouter(tags=["rackets", "feedback"])


def _racket_to_dto(racket: Racket) -> RacketOut:
    return RacketOut(
        id=racket.id,
        user_id=racket.user_id,
        nickname=racket.nickname,
        brand=racket.brand,
        model=racket.model,
        weight_class=racket.weight_class,
        balance_point=racket.balance_point,
        grip_size=racket.grip_size,
        preferred_use=racket.preferred_use,
        notes=racket.notes,
        created_at=racket.created_at.isoformat(),
        updated_at=racket.updated_at.isoformat(),
    )


def feedback_to_dto(feedback: BookingFeedback) -> FeedbackOut:
    return FeedbackOut(
        id=feedback.id,
        booking_id=feedback.booking_id,
        user_id=feedback.user_id,
        rating=feedback.rating,
        recommendation_relevance=feedback.recommendation_relevance,
        string_satisfaction=feedback.string_satisfaction,
        tension_satisfaction=feedback.tension_satisfaction,
        comfort=feedback.comfort,
        control=feedback.control,
        repulsion=feedback.repulsion,
        durability=feedback.durability,
        would_use_again=feedback.would_use_again,
        comment=feedback.comment,
        string_feedback=feedback.string_feedback,
        service_feedback=feedback.service_feedback,
        sentiment_tags=cast(list[SentimentTag], feedback.sentiment_tags),
        created_at=feedback.created_at.isoformat(),
        updated_at=feedback.updated_at.isoformat(),
    )


def _get_owned_racket(db: Session, racket_id: str, user_id: str) -> Racket:
    racket = db.execute(
        select(Racket).where(Racket.id == racket_id, Racket.user_id == user_id)
    ).scalar_one_or_none()
    if racket is None:
        raise NotFoundError("Racket not found")
    return racket


def _get_owned_booking(
    db: Session,
    booking_id: str,
    user_id: str,
    *,
    lock: bool = False,
) -> Booking:
    query = select(Booking).where(
        Booking.id == booking_id,
        Booking.user_id == user_id,
    )
    if lock:
        query = query.with_for_update()
    booking = db.execute(query).scalar_one_or_none()
    if booking is None:
        raise NotFoundError("Booking not found")
    return booking


@router.get("/rackets", response_model=list[RacketOut])
def list_rackets(
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db, scope="function"),
) -> list[RacketOut]:
    rackets = (
        db.execute(
            select(Racket)
            .where(Racket.user_id == current_user.user_id)
            .order_by(Racket.updated_at.desc(), Racket.created_at.desc())
        )
        .scalars()
        .all()
    )
    return [_racket_to_dto(racket) for racket in rackets]


@router.post("/rackets", response_model=RacketOut)
def create_racket(
    payload: CreateRacketPayload,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db, scope="function"),
) -> RacketOut:
    racket = Racket(user_id=current_user.user_id, **payload.model_dump())
    db.add(racket)
    db.flush()
    db.refresh(racket)
    return _racket_to_dto(racket)


@router.get("/rackets/{racket_id}", response_model=RacketDetailOut)
def get_racket(
    racket_id: str,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db, scope="function"),
) -> RacketDetailOut:
    racket = _get_owned_racket(db, racket_id, current_user.user_id)
    rows = db.execute(
        select(Booking, BookingFeedback)
        .outerjoin(BookingFeedback, BookingFeedback.booking_id == Booking.id)
        .options(joinedload(Booking.string_item))
        .where(
            Booking.racket_id == racket.id,
            Booking.user_id == current_user.user_id,
            Booking.status == BookingStatus.COMPLETED.value,
        )
        .order_by(Booking.updated_at.desc(), Booking.created_at.desc())
    ).all()
    service_history = [
        RacketServiceHistoryOut(
            booking_id=booking.id,
            string_id=booking.string_id,
            string_name=booking.string_item.display_name,
            requested_tension=number_to_float(booking.requested_tension),
            serviced_at=(
                booking.collection_datetime or booking.updated_at or booking.created_at
            ).isoformat(),
            feedback=feedback_to_dto(feedback) if feedback is not None else None,
        )
        for booking, feedback in rows
    ]
    return RacketDetailOut(
        **_racket_to_dto(racket).model_dump(),
        service_history=service_history,
    )


@router.get(
    "/rackets/{racket_id}/history",
    response_model=list[RacketServiceHistoryOut],
)
def get_racket_history(
    racket_id: str,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db, scope="function"),
) -> list[RacketServiceHistoryOut]:
    return get_racket(racket_id, current_user, db).service_history


@router.patch("/rackets/{racket_id}", response_model=RacketOut)
def update_racket(
    racket_id: str,
    payload: UpdateRacketPayload,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db, scope="function"),
) -> RacketOut:
    racket = _get_owned_racket(db, racket_id, current_user.user_id)
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(racket, field_name, value)
    db.flush()
    db.refresh(racket)
    return _racket_to_dto(racket)


@router.delete("/rackets/{racket_id}", response_model=MessageResponse)
def delete_racket(
    racket_id: str,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db, scope="function"),
) -> MessageResponse:
    racket = _get_owned_racket(db, racket_id, current_user.user_id)
    db.delete(racket)
    db.flush()
    return MessageResponse(message="Racket deleted")


@router.post("/bookings/{booking_id}/feedback", response_model=FeedbackOut)
def create_feedback(
    booking_id: str,
    payload: CreateFeedbackPayload,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db, scope="function"),
) -> FeedbackOut:
    booking = _get_owned_booking(
        db,
        booking_id,
        current_user.user_id,
        lock=True,
    )
    if booking.status != BookingStatus.COMPLETED.value:
        raise ConflictError("Feedback is only available for completed bookings")
    existing = db.execute(
        select(BookingFeedback).where(BookingFeedback.booking_id == booking.id)
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError("Feedback already exists for this booking")

    feedback = BookingFeedback(
        booking_id=booking.id,
        user_id=current_user.user_id,
        **payload.model_dump(),
    )
    db.add(feedback)
    db.flush()
    db.refresh(feedback)
    return feedback_to_dto(feedback)


@router.get("/bookings/{booking_id}/feedback", response_model=FeedbackOut | None)
def get_feedback(
    booking_id: str,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db, scope="function"),
) -> FeedbackOut | None:
    booking = _get_owned_booking(db, booking_id, current_user.user_id)
    feedback = db.execute(
        select(BookingFeedback).where(BookingFeedback.booking_id == booking.id)
    ).scalar_one_or_none()
    if feedback is None:
        return None
    return feedback_to_dto(feedback)
