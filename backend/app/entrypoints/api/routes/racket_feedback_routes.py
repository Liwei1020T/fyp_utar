from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy import delete
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.models.booking import Booking
from app.adapters.persistence.sqlalchemy.models.racket_feedback import BookingFeedback
from app.adapters.persistence.sqlalchemy.models.racket_feedback import Racket
from app.adapters.persistence.sqlalchemy.models.racket_feedback import (
    RacketModelCatalog,
)
from app.adapters.persistence.sqlalchemy.models.string_catalog_item import (
    RecommendationScoreCache,
)
from app.adapters.persistence.sqlalchemy.session import get_db
from app.domain.booking.enums import BookingStatus
from app.dto.racket_feedback import CreateFeedbackPayload
from app.dto.racket_feedback import CreateRacketPayload
from app.dto.racket_feedback import FeedbackOut
from app.dto.racket_feedback import RacketDetailOut
from app.dto.racket_feedback import RacketModelOptionOut
from app.dto.racket_feedback import RacketOut
from app.dto.racket_feedback import RacketServiceHistoryOut
from app.dto.racket_feedback import UpdateRacketPayload
from app.dto.racket_feedback import UpdateFeedbackPayload
from app.entrypoints.api.dependencies import CurrentUser
from app.entrypoints.api.dependencies import get_current_customer
from app.dto.auth import MessageResponse
from app.domain.recommendation.learning_signals import canonical_racket_model_key
from app.domain.recommendation.learning_signals import standard_racket_model_for_key
from app.domain.recommendation.scoring import ALGORITHM_VERSION
from app.shared.errors import BadRequestError
from app.shared.errors import ConflictError
from app.shared.errors import NotFoundError
from app.shared.serialization import number_to_float


router = APIRouter(tags=["rackets", "feedback"])

RECOMMENDATION_FEATURE_FIELDS = {"comfort", "control", "repulsion"}
PERSONAL_HISTORY_FIELDS = {"string_satisfaction", "would_use_again"}
RacketServiceSummary = tuple[int, str | None, float | None, str | None]


def _racket_to_dto(
    racket: Racket,
    service_summary: RacketServiceSummary | None = None,
) -> RacketOut:
    service_count, current_string_id, current_tension, last_serviced_at = (
        service_summary or (0, None, None, None)
    )
    return RacketOut(
        id=racket.id,
        user_id=racket.user_id,
        nickname=racket.nickname,
        model_key=canonical_racket_model_key(racket.brand, racket.model),
        brand=racket.brand,
        model=racket.model,
        weight_class=racket.weight_class,
        balance_point=racket.balance_point,
        grip_size=racket.grip_size,
        preferred_use=racket.preferred_use,
        notes=racket.notes,
        service_count=service_count,
        current_string_id=current_string_id,
        current_tension=current_tension,
        last_serviced_at=last_serviced_at,
        created_at=racket.created_at.isoformat(),
        updated_at=racket.updated_at.isoformat(),
    )


def _racket_service_summaries(
    db: Session,
    *,
    racket_ids: list[str],
    user_id: str,
) -> dict[str, RacketServiceSummary]:
    if not racket_ids:
        return {}
    rows = db.execute(
        select(
            Booking.racket_id,
            Booking.string_id,
            Booking.requested_tension,
            Booking.collection_datetime,
            Booking.updated_at,
            Booking.created_at,
        )
        .where(
            Booking.racket_id.in_(racket_ids),
            Booking.user_id == user_id,
            Booking.status == BookingStatus.COMPLETED.value,
        )
        .order_by(Booking.updated_at.desc(), Booking.created_at.desc())
    ).all()
    counts: dict[str, int] = {}
    latest: dict[str, tuple[str | None, float | None, str | None]] = {}
    for (
        racket_id,
        string_id,
        tension,
        collection_datetime,
        updated_at,
        created_at,
    ) in rows:
        if racket_id is None:
            continue
        counts[racket_id] = counts.get(racket_id, 0) + 1
        if racket_id not in latest:
            serviced_at = collection_datetime or updated_at or created_at
            latest[racket_id] = (
                string_id,
                number_to_float(tension),
                serviced_at.isoformat() if serviced_at is not None else None,
            )
    return {
        racket_id: (
            count,
            latest.get(racket_id, (None, None, None))[0],
            latest.get(racket_id, (None, None, None))[1],
            latest.get(racket_id, (None, None, None))[2],
        )
        for racket_id, count in counts.items()
    }


def _resolve_racket_identity(
    db: Session,
    *,
    model_key: str | None,
    brand: str,
    model: str,
) -> tuple[str, str]:
    if model_key is not None:
        standard_model = standard_racket_model_for_key(model_key)
        if standard_model is not None:
            return standard_model
        managed_model = db.execute(
            select(RacketModelCatalog).where(
                RacketModelCatalog.model_key == model_key,
                RacketModelCatalog.is_active.is_(True),
            )
        ).scalar_one_or_none()
        if managed_model is None:
            raise BadRequestError("Unknown or inactive racket model")
        return managed_model.brand, managed_model.model

    canonical_key = canonical_racket_model_key(brand, model)
    if canonical_key is None:
        return brand, model
    standard_model = standard_racket_model_for_key(canonical_key)
    assert standard_model is not None
    return standard_model


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
        would_use_again=feedback.would_use_again,
        comment=feedback.comment,
        string_feedback=feedback.string_feedback,
        service_feedback=feedback.service_feedback,
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


def _invalidate_feedback_caches(db: Session) -> None:
    db.execute(
        delete(RecommendationScoreCache).where(
            RecommendationScoreCache.algorithm_version == ALGORITHM_VERSION
        )
    )


def _invalidate_user_racket_cache(db: Session, user_id: str) -> None:
    db.execute(
        delete(RecommendationScoreCache).where(
            RecommendationScoreCache.user_id == user_id,
            RecommendationScoreCache.algorithm_version == ALGORITHM_VERSION,
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
    summaries = _racket_service_summaries(
        db,
        racket_ids=[racket.id for racket in rackets],
        user_id=current_user.user_id,
    )
    return [_racket_to_dto(racket, summaries.get(racket.id)) for racket in rackets]


@router.get("/racket-models", response_model=list[RacketModelOptionOut])
def list_racket_models(
    _: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db, scope="function"),
) -> list[RacketModelOptionOut]:
    models = (
        db.execute(
            select(RacketModelCatalog)
            .where(RacketModelCatalog.is_active.is_(True))
            .order_by(RacketModelCatalog.brand.asc(), RacketModelCatalog.model.asc())
        )
        .scalars()
        .all()
    )
    return [
        RacketModelOptionOut(
            key=model.model_key,
            brand=model.brand,
            model=model.model,
        )
        for model in models
    ]


@router.post("/rackets", response_model=RacketOut)
def create_racket(
    payload: CreateRacketPayload,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db, scope="function"),
) -> RacketOut:
    values = payload.model_dump()
    model_key = values.pop("model_key")
    values["brand"], values["model"] = _resolve_racket_identity(
        db,
        model_key=model_key,
        brand=payload.brand,
        model=payload.model,
    )
    racket = Racket(user_id=current_user.user_id, **values)
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
            feedback=feedback_to_dto(feedback) if feedback is not None else None,
        )
        for booking, feedback in rows
    ]
    current_service = service_history[0] if service_history else None
    return RacketDetailOut(
        **_racket_to_dto(
            racket,
            (
                len(service_history),
                current_service.string_id if current_service else None,
                current_service.requested_tension if current_service else None,
                current_service.serviced_at if current_service else None,
            ),
        ).model_dump(),
        service_history=service_history,
    )


@router.patch("/rackets/{racket_id}", response_model=RacketOut)
def update_racket(
    racket_id: str,
    payload: UpdateRacketPayload,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db, scope="function"),
) -> RacketOut:
    racket = _get_owned_racket(db, racket_id, current_user.user_id)
    previous_identity = (racket.brand, racket.model)
    values = payload.model_dump(exclude_unset=True)
    model_key = values.pop("model_key", None)
    if model_key is not None:
        values["brand"], values["model"] = _resolve_racket_identity(
            db,
            model_key=model_key,
            brand=racket.brand,
            model=racket.model,
        )
    elif "brand" in values or "model" in values:
        values["brand"], values["model"] = _resolve_racket_identity(
            db,
            model_key=None,
            brand=values.get("brand", racket.brand),
            model=values.get("model", racket.model),
        )
    if not values:
        raise BadRequestError("At least one persisted racket field is required")
    next_identity = (
        values.get("brand", racket.brand),
        values.get("model", racket.model),
    )
    if next_identity != previous_identity:
        _invalidate_user_racket_cache(db, current_user.user_id)
    for field_name, value in values.items():
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
    _invalidate_user_racket_cache(db, current_user.user_id)
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

    values = payload.model_dump()

    feedback = BookingFeedback(
        booking_id=booking.id,
        user_id=current_user.user_id,
        **values,
    )
    db.add(feedback)
    if any(
        values.get(field_name) is not None
        for field_name in RECOMMENDATION_FEATURE_FIELDS & payload.model_fields_set
    ):
        _invalidate_feedback_caches(db)
    if any(
        values.get(field_name) is not None
        for field_name in PERSONAL_HISTORY_FIELDS & payload.model_fields_set
    ):
        _invalidate_user_racket_cache(db, current_user.user_id)
    db.flush()
    db.refresh(feedback)
    return feedback_to_dto(feedback)


@router.patch("/bookings/{booking_id}/feedback", response_model=FeedbackOut)
def update_feedback(
    booking_id: str,
    payload: UpdateFeedbackPayload,
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
    feedback = db.execute(
        select(BookingFeedback)
        .where(BookingFeedback.booking_id == booking.id)
        .with_for_update()
    ).scalar_one_or_none()
    if feedback is None:
        raise NotFoundError("Feedback not found")

    values = payload.model_dump(exclude_unset=True)

    changed_features = {
        field_name
        for field_name in RECOMMENDATION_FEATURE_FIELDS & payload.model_fields_set
        if getattr(feedback, field_name) != values.get(field_name)
    }
    changed_personal_history = {
        field_name
        for field_name in PERSONAL_HISTORY_FIELDS & payload.model_fields_set
        if getattr(feedback, field_name) != values.get(field_name)
    }
    for field_name, value in values.items():
        setattr(feedback, field_name, value)
    if changed_features:
        _invalidate_feedback_caches(db)
    if changed_personal_history:
        _invalidate_user_racket_cache(db, current_user.user_id)

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
