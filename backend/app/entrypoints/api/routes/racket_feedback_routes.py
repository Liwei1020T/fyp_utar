from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import cast

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy import delete
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.models.booking import Booking
from app.adapters.persistence.sqlalchemy.models.booking import BookingStatusHistory
from app.adapters.persistence.sqlalchemy.models.racket_feedback import BookingFeedback
from app.adapters.persistence.sqlalchemy.models.racket_feedback import Racket
from app.adapters.persistence.sqlalchemy.models.string_catalog_item import (
    RecommendationScoreCache,
)
from app.adapters.persistence.sqlalchemy.session import get_db
from app.domain.booking.enums import BookingStatus
from app.dto.racket_feedback import CreateFeedbackPayload
from app.dto.racket_feedback import CreateRacketPayload
from app.dto.racket_feedback import FeedbackOut
from app.dto.racket_feedback import FeedbackEligibilityOut
from app.dto.racket_feedback import RacketDetailOut
from app.dto.racket_feedback import RacketOut
from app.dto.racket_feedback import RacketServiceHistoryOut
from app.dto.racket_feedback import SentimentTag
from app.dto.racket_feedback import UpdateRacketPayload
from app.dto.racket_feedback import UpdateFeedbackPayload
from app.entrypoints.api.dependencies import CurrentUser
from app.entrypoints.api.dependencies import get_current_customer
from app.entrypoints.api.dependencies import get_clock
from app.dto.auth import MessageResponse
from app.ports.services.clock import Clock
from app.shared.errors import ConflictError
from app.shared.errors import NotFoundError
from app.shared.serialization import number_to_float


router = APIRouter(tags=["rackets", "feedback"])

DURABILITY_MIN_AGE = timedelta(days=7)
STRUCTURED_FEEDBACK_FIELDS = {
    "recommendation_relevance",
    "string_satisfaction",
    "tension_satisfaction",
    "comfort",
    "control",
    "repulsion",
    "durability",
    "would_use_again",
}
RECOMMENDATION_FEATURE_FIELDS = {"comfort", "control", "repulsion", "durability"}
FEEDBACK_ALGORITHM_VERSIONS = {
    "fyp1_similarity_preferences_community_v10",
    "fyp1_similarity_preferences_community_racket_cf_v11",
}


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


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _booking_completed_at(booking: Booking) -> datetime | None:
    return next(
        (
            _utc(entry.changed_at)
            for entry in reversed(booking.status_history)
            if entry.new_status == BookingStatus.COMPLETED.value
        ),
        None,
    )


def _completed_at(db: Session, booking_id: str) -> datetime | None:
    value = db.execute(
        select(BookingStatusHistory.changed_at)
        .where(
            BookingStatusHistory.booking_id == booking_id,
            BookingStatusHistory.new_status == BookingStatus.COMPLETED.value,
        )
        .order_by(BookingStatusHistory.changed_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    return _utc(value) if value is not None else None


def _durability_available_at(completed_at: datetime | None) -> datetime | None:
    return completed_at + DURABILITY_MIN_AGE if completed_at is not None else None


def feedback_to_dto(
    feedback: BookingFeedback,
    *,
    completed_at: datetime | None = None,
    now: datetime | None = None,
) -> FeedbackOut:
    durability_available_at = _durability_available_at(completed_at)
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
        durability_available_at=(
            durability_available_at.isoformat()
            if durability_available_at is not None
            else None
        ),
        can_rate_durability=(
            durability_available_at is not None
            and now is not None
            and _utc(now) >= durability_available_at
        ),
        durability_rated_at=(
            feedback.durability_rated_at.isoformat()
            if feedback.durability_rated_at is not None
            else None
        ),
        structured_field_confirmed_at=feedback.structured_field_confirmed_at or {},
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


def _require_durability_eligible(
    *,
    completed_at: datetime | None,
    now: datetime,
) -> None:
    available_at = _durability_available_at(completed_at)
    if available_at is None or _utc(now) < available_at:
        raise ConflictError(
            "Durability feedback is available seven days after completion"
        )


def _confirmed_fields(
    *,
    supplied_fields: set[str],
    values: dict[str, object],
    now: datetime,
) -> dict[str, str]:
    confirmed_at = now.isoformat()
    return {
        field_name: confirmed_at
        for field_name in STRUCTURED_FEEDBACK_FIELDS & supplied_fields
        if values.get(field_name) is not None
    }


def _invalidate_feedback_caches(db: Session) -> None:
    db.execute(
        delete(RecommendationScoreCache).where(
            RecommendationScoreCache.algorithm_version.in_(FEEDBACK_ALGORITHM_VERSIONS)
        )
    )


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
    rows = (
        db.execute(
            select(Booking, BookingFeedback)
            .outerjoin(BookingFeedback, BookingFeedback.booking_id == Booking.id)
            .options(
                joinedload(Booking.string_item),
                joinedload(Booking.status_history),
            )
            .where(
                Booking.racket_id == racket.id,
                Booking.user_id == current_user.user_id,
                Booking.status == BookingStatus.COMPLETED.value,
            )
            .order_by(Booking.updated_at.desc(), Booking.created_at.desc())
        )
        .unique()
        .all()
    )
    service_history = [
        RacketServiceHistoryOut(
            booking_id=booking.id,
            string_id=booking.string_id,
            string_name=booking.string_item.display_name,
            requested_tension=number_to_float(booking.requested_tension),
            serviced_at=(
                booking.collection_datetime or booking.updated_at or booking.created_at
            ).isoformat(),
            feedback=(
                feedback_to_dto(
                    feedback,
                    completed_at=_booking_completed_at(booking),
                    now=datetime.now(timezone.utc),
                )
                if feedback is not None
                else None
            ),
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
    clock: Clock = Depends(get_clock),
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

    now = _utc(clock.now())
    completed_at = _completed_at(db, booking.id)
    values = payload.model_dump()
    if payload.durability is not None:
        _require_durability_eligible(completed_at=completed_at, now=now)

    feedback = BookingFeedback(
        booking_id=booking.id,
        user_id=current_user.user_id,
        **values,
        durability_rated_at=now if payload.durability is not None else None,
        structured_field_confirmed_at=_confirmed_fields(
            supplied_fields=set(payload.model_fields_set),
            values=values,
            now=now,
        ),
    )
    db.add(feedback)
    if any(
        values.get(field_name) is not None
        for field_name in RECOMMENDATION_FEATURE_FIELDS & payload.model_fields_set
    ):
        _invalidate_feedback_caches(db)
    db.flush()
    db.refresh(feedback)
    return feedback_to_dto(feedback, completed_at=completed_at, now=now)


@router.patch("/bookings/{booking_id}/feedback", response_model=FeedbackOut)
def update_feedback(
    booking_id: str,
    payload: UpdateFeedbackPayload,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db, scope="function"),
    clock: Clock = Depends(get_clock),
) -> FeedbackOut:
    booking = _get_owned_booking(
        db,
        booking_id,
        current_user.user_id,
        lock=True,
    )
    if booking.status != BookingStatus.COMPLETED.value:
        raise ConflictError("Feedback is only available for completed bookings")
    feedback = db.execute(
        select(BookingFeedback)
        .where(BookingFeedback.booking_id == booking.id)
        .with_for_update()
    ).scalar_one_or_none()
    if feedback is None:
        raise NotFoundError("Feedback not found")

    now = _utc(clock.now())
    completed_at = _completed_at(db, booking.id)
    values = payload.model_dump(exclude_unset=True)
    if "durability" in payload.model_fields_set and payload.durability is not None:
        _require_durability_eligible(completed_at=completed_at, now=now)

    changed_features = {
        field_name
        for field_name in RECOMMENDATION_FEATURE_FIELDS & payload.model_fields_set
        if getattr(feedback, field_name) != values.get(field_name)
    }
    confirmed = dict(feedback.structured_field_confirmed_at or {})
    for field_name in STRUCTURED_FEEDBACK_FIELDS & payload.model_fields_set:
        if values.get(field_name) is None:
            confirmed.pop(field_name, None)
        else:
            confirmed[field_name] = now.isoformat()

    for field_name, value in values.items():
        setattr(feedback, field_name, value)
    feedback.structured_field_confirmed_at = confirmed
    if "durability" in payload.model_fields_set:
        feedback.durability_rated_at = now if payload.durability is not None else None
    if changed_features:
        _invalidate_feedback_caches(db)

    db.flush()
    db.refresh(feedback)
    return feedback_to_dto(feedback, completed_at=completed_at, now=now)


@router.get("/bookings/{booking_id}/feedback", response_model=FeedbackOut | None)
def get_feedback(
    booking_id: str,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db, scope="function"),
    clock: Clock = Depends(get_clock),
) -> FeedbackOut | None:
    booking = _get_owned_booking(db, booking_id, current_user.user_id)
    feedback = db.execute(
        select(BookingFeedback).where(BookingFeedback.booking_id == booking.id)
    ).scalar_one_or_none()
    if feedback is None:
        return None
    return feedback_to_dto(
        feedback,
        completed_at=_completed_at(db, booking.id),
        now=clock.now(),
    )


@router.get(
    "/bookings/{booking_id}/feedback-eligibility",
    response_model=FeedbackEligibilityOut,
)
def get_feedback_eligibility(
    booking_id: str,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db, scope="function"),
    clock: Clock = Depends(get_clock),
) -> FeedbackEligibilityOut:
    booking = _get_owned_booking(db, booking_id, current_user.user_id)
    if booking.status != BookingStatus.COMPLETED.value:
        raise ConflictError("Feedback is only available for completed bookings")
    available_at = _durability_available_at(_completed_at(db, booking.id))
    return FeedbackEligibilityOut(
        durability_available_at=(
            available_at.isoformat() if available_at is not None else None
        ),
        can_rate_durability=(
            available_at is not None and _utc(clock.now()) >= available_at
        ),
    )
