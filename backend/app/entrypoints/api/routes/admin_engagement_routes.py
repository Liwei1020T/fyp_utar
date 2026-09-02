from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from datetime import timezone
from typing import cast

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import Response
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.models import Booking
from app.adapters.persistence.sqlalchemy.models import BookingStatusHistory
from app.adapters.persistence.sqlalchemy.models import BookingFeedback
from app.adapters.persistence.sqlalchemy.models import NotificationDelivery
from app.adapters.persistence.sqlalchemy.models import Profile
from app.adapters.persistence.sqlalchemy.models import StoreSettings
from app.adapters.persistence.sqlalchemy.models import StringCatalogItem
from app.adapters.persistence.sqlalchemy.models import User
from app.adapters.persistence.sqlalchemy.session import SessionLocal
from app.adapters.persistence.sqlalchemy.session import get_db
from app.adapters.services.openwa import send_openwa_text
from app.config.settings import get_settings
from app.domain.booking.policies import booking_order_code
from app.dto.notifications import AdminNotificationOut
from app.dto.notifications import NotificationCategory
from app.dto.notifications import SendNotificationPayload
from app.dto.racket_feedback import AdminFeedbackOut
from app.entrypoints.api.dependencies import CurrentUser
from app.entrypoints.api.dependencies import get_current_admin
from app.entrypoints.api.dependencies import get_recommendation_repository
from app.domain.recommendation.learning_signals import build_feedback_snapshot
from app.dto.recommendation import feedback_snapshot_to_dict
from app.entrypoints.api.routes.racket_feedback_routes import feedback_to_dto
from app.shared.errors import NotFoundError


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/feedback/summary", response_model=dict)
def get_admin_feedback_summary(
    _: CurrentUser = Depends(get_current_admin),
    recommendation_repository=Depends(get_recommendation_repository),
) -> dict[str, object]:
    rows = recommendation_repository.list_feedback_rows()
    model_keys = sorted(
        {row.racket_model_key for row in rows if row.racket_model_key is not None}
    )
    global_snapshot = build_feedback_snapshot(rows, target_racket_model_key=None)
    return {
        "global": feedback_snapshot_to_dict(
            global_snapshot,
            racket_model_key=None,
        ),
        "racket_contexts": [
            feedback_snapshot_to_dict(
                build_feedback_snapshot(rows, target_racket_model_key=model_key),
                racket_model_key=model_key,
            )
            for model_key in model_keys
        ],
    }


@dataclass(frozen=True, slots=True)
class _NotificationDeliveryTarget:
    recipient: str
    title: str
    body: str
    endpoint: str
    access_token: str | None


def _feedback_query(
    *,
    booking_id: str | None,
    string_id: str | None,
    rating: int | None,
    date_from: date | None,
    date_to: date | None,
):
    query = (
        select(BookingFeedback, Booking, User, StringCatalogItem)
        .join(Booking, Booking.id == BookingFeedback.booking_id)
        .join(User, User.id == BookingFeedback.user_id)
        .join(StringCatalogItem, StringCatalogItem.catalog_id == Booking.string_id)
    )
    if booking_id:
        query = query.where(BookingFeedback.booking_id == booking_id)
    if string_id:
        query = query.where(Booking.string_id == string_id)
    if rating is not None:
        query = query.where(BookingFeedback.rating == rating)
    if date_from is not None:
        query = query.where(
            BookingFeedback.created_at
            >= datetime.combine(date_from, time.min, tzinfo=timezone.utc)
        )
    if date_to is not None:
        query = query.where(
            BookingFeedback.created_at
            <= datetime.combine(date_to, time.max, tzinfo=timezone.utc)
        )
    return query.order_by(
        BookingFeedback.created_at.desc(),
        BookingFeedback.id.desc(),
    )


def _admin_feedback_dto(
    feedback: BookingFeedback,
    booking: Booking,
    user: User,
    string_item: StringCatalogItem,
) -> AdminFeedbackOut:
    return AdminFeedbackOut(
        **feedback_to_dto(feedback).model_dump(),
        order_code=booking_order_code(booking.id),
        string_id=booking.string_id,
        string_name=string_item.display_name,
        customer_username=user.username,
        customer_phone_number=user.phone_number,
    )


def _notification_dto(
    notification: NotificationDelivery,
    user: User,
) -> AdminNotificationOut:
    return AdminNotificationOut(
        id=notification.id,
        user_id=notification.user_id,
        customer_username=user.username,
        customer_phone_number=user.phone_number,
        category=cast(NotificationCategory, notification.category),
        title=notification.title,
        body=notification.body,
        route=notification.route,
        status=notification.status,
        provider_message=notification.provider_message,
        attempts=notification.attempts,
        created_at=notification.created_at,
        last_attempt_at=notification.last_attempt_at,
    )


def _prepare_notification_delivery(
    db: Session,
    notification: NotificationDelivery,
) -> bool:
    settings = get_settings()
    profile = db.scalar(select(Profile).where(Profile.user_id == notification.user_id))
    user_preferences = dict(profile.notification_preferences or {}) if profile else {}
    if not user_preferences.get(notification.category, True):
        notification.status = "disabled"
        notification.provider_message = "User disabled this notification category"
        return False

    store_settings = db.get(StoreSettings, "main")
    category_settings = (
        dict(store_settings.notification_settings or {}).get(notification.category, {})
        if store_settings
        else {}
    )
    if isinstance(category_settings, dict) and not category_settings.get(
        "enabled", True
    ):
        notification.status = "disabled"
        notification.provider_message = "Notification category is disabled"
        return False

    if settings.openwa_enabled:
        notification.attempts += 1
        notification.last_attempt_at = datetime.now(timezone.utc)
        notification.status = "pending"
        notification.provider_message = None
        return True

    notification.status = "disabled"
    notification.provider_message = "Remote delivery is disabled"
    return False


def _send_notification_to_provider(
    target: _NotificationDeliveryTarget,
) -> tuple[str, str | None]:
    try:
        return (
            "sent",
            send_openwa_text(
                endpoint=target.endpoint,
                api_key=target.access_token,
                chat_id=target.recipient,
                text=f"*{target.title}*\n{target.body}",
            ),
        )
    except (OSError, TypeError, ValueError) as exc:
        return "failed", str(exc)[:500]


def _notification_response_for_session(
    db: Session,
    notification: NotificationDelivery,
) -> AdminNotificationOut:
    user = db.get(User, notification.user_id)
    if user is None:
        raise NotFoundError("User not found")
    return _notification_dto(notification, user)


def _read_notification_response(notification_id: str) -> AdminNotificationOut:
    with SessionLocal() as db:
        notification = db.get(NotificationDelivery, notification_id)
        if notification is None:
            raise NotFoundError("Notification not found")
        return _notification_response_for_session(db, notification)


def _persist_notification_outcome(
    notification_id: str,
    *,
    status: str,
    provider_message: str | None,
) -> AdminNotificationOut:
    with SessionLocal() as db:
        notification = db.get(NotificationDelivery, notification_id)
        if notification is None:
            raise NotFoundError("Notification not found")
        notification.status = status
        notification.provider_message = provider_message
        db.commit()
        db.refresh(notification)
        return _notification_response_for_session(db, notification)


def _deliver_notification(notification_id: str) -> AdminNotificationOut:
    target: _NotificationDeliveryTarget | None = None
    provider_message: str | None = None
    with SessionLocal() as db:
        notification = db.get(NotificationDelivery, notification_id)
        if notification is None:
            raise NotFoundError("Notification not found")
        settings = get_settings()
        if settings.openwa_enabled:
            user = db.get(User, notification.user_id)
            if user is None:
                provider_message = "User not found"
            else:
                phone_digits = "".join(
                    character for character in user.phone_number if character.isdigit()
                )
                target = _NotificationDeliveryTarget(
                    recipient=f"{phone_digits}@c.us",
                    title=notification.title,
                    body=notification.body,
                    endpoint=(
                        f"{settings.openwa_base_url.rstrip('/')}"
                        f"/sessions/{settings.openwa_session_id}/messages/send-text"
                    ),
                    access_token=(
                        settings.openwa_api_key.get_secret_value()
                        if settings.openwa_api_key is not None
                        else None
                    ),
                )

    if target is None:
        status = "failed"
    else:
        status, provider_message = _send_notification_to_provider(target)

    return _persist_notification_outcome(
        notification_id,
        status=status,
        provider_message=provider_message,
    )


def run_due_feedback_followups(
    *,
    now: datetime | None = None,
) -> dict[str, int]:
    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    else:
        current_time = current_time.astimezone(timezone.utc)
    completed = (
        select(
            BookingStatusHistory.booking_id.label("booking_id"),
            func.max(BookingStatusHistory.changed_at).label("completed_at"),
        )
        .where(BookingStatusHistory.new_status == "completed")
        .group_by(BookingStatusHistory.booking_id)
        .subquery()
    )
    queued: list[tuple[str, bool]] = []
    with SessionLocal() as db:
        rows = db.execute(
            select(Booking, completed.c.completed_at)
            .join(completed, completed.c.booking_id == Booking.id)
            .outerjoin(BookingFeedback, BookingFeedback.booking_id == Booking.id)
            .where(
                Booking.status == "completed",
                BookingFeedback.id.is_(None),
                completed.c.completed_at <= current_time - timedelta(days=7),
            )
        ).all()
        for booking, completed_at in rows:
            if completed_at.tzinfo is None:
                completed_at = completed_at.replace(tzinfo=timezone.utc)
            age = current_time - completed_at.astimezone(timezone.utc)
            if age >= timedelta(days=10):
                title = "A quick feedback reminder"
                body = (
                    "Tell us how your string setup is performing. "
                    "This is the final reminder."
                )
            else:
                title = "How is your string setup?"
                body = (
                    "Your service was completed 7 days ago. "
                    "Share how the string feels and how it is holding up."
                )
            route = f"/player/feedback/{booking.id}"
            # ponytail: single-process dedupe; add a unique follow-up key before
            # running multiple backend workers.
            exists = db.scalar(
                select(NotificationDelivery.id).where(
                    NotificationDelivery.user_id == booking.user_id,
                    NotificationDelivery.title == title,
                    NotificationDelivery.route == route,
                )
            )
            if exists:
                continue
            notification = NotificationDelivery(
                user_id=booking.user_id,
                category="service",
                title=title,
                body=body,
                route=route,
            )
            db.add(notification)
            db.flush()
            queued.append(
                (notification.id, _prepare_notification_delivery(db, notification))
            )
        db.commit()

    delivered = 0
    for notification_id, should_deliver in queued:
        if should_deliver:
            _deliver_notification(notification_id)
            delivered += 1
    return {"created": len(queued), "delivery_attempts": delivered}


@router.get("/feedback", response_model=dict)
def admin_feedback(
    booking_id: str | None = Query(default=None, max_length=36),
    string_id: str | None = Query(default=None, max_length=120),
    rating: int | None = Query(default=None, ge=1, le=5),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db, scope="function"),
) -> dict[str, object]:
    query = _feedback_query(
        booking_id=booking_id,
        string_id=string_id,
        rating=rating,
        date_from=date_from,
        date_to=date_to,
    )
    total = (
        db.scalar(select(func.count()).select_from(query.order_by(None).subquery()))
        or 0
    )
    rows = db.execute(query.limit(limit).offset(offset)).all()
    items = [
        _admin_feedback_dto(feedback, booking, user, string_item).model_dump()
        for feedback, booking, user, string_item in rows
    ]
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/feedback/export")
def admin_export_feedback(
    booking_id: str | None = Query(default=None, max_length=36),
    string_id: str | None = Query(default=None, max_length=120),
    rating: int | None = Query(default=None, ge=1, le=5),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db, scope="function"),
) -> Response:
    rows = db.execute(
        _feedback_query(
            booking_id=booking_id,
            string_id=string_id,
            rating=rating,
            date_from=date_from,
            date_to=date_to,
        )
    ).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(AdminFeedbackOut.model_fields)
    for feedback, booking, user, string_item in rows:
        item = _admin_feedback_dto(feedback, booking, user, string_item)
        writer.writerow(
            [
                json.dumps(value) if isinstance(value, list) else value
                for value in item.model_dump().values()
            ]
        )
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=feedback.csv"},
    )


@router.get("/notifications", response_model=list[AdminNotificationOut])
def admin_notifications(
    status: str | None = Query(default=None, max_length=20),
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db, scope="function"),
) -> list[AdminNotificationOut]:
    query = select(NotificationDelivery, User).join(
        User, User.id == NotificationDelivery.user_id
    )
    if status:
        query = query.where(NotificationDelivery.status == status)
    rows = db.execute(query.order_by(NotificationDelivery.created_at.desc())).all()
    return [_notification_dto(notification, user) for notification, user in rows]


@router.post("/notifications", response_model=AdminNotificationOut)
def admin_send_notification(
    payload: SendNotificationPayload,
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db, scope="function"),
) -> AdminNotificationOut:
    user = db.get(User, payload.user_id)
    if user is None:
        raise NotFoundError("User not found")
    notification = NotificationDelivery(**payload.model_dump())
    db.add(notification)
    db.flush()
    should_deliver = _prepare_notification_delivery(db, notification)
    db.commit()
    if should_deliver:
        return _deliver_notification(notification.id)
    return _read_notification_response(notification.id)


@router.post(
    "/notifications/{notification_id}/resend",
    response_model=AdminNotificationOut,
)
def admin_resend_notification(
    notification_id: str,
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db, scope="function"),
) -> AdminNotificationOut:
    notification = db.get(NotificationDelivery, notification_id)
    if notification is None:
        raise NotFoundError("Notification not found")
    user = db.get(User, notification.user_id)
    assert user is not None
    should_deliver = _prepare_notification_delivery(db, notification)
    db.commit()
    if should_deliver:
        return _deliver_notification(notification.id)
    return _read_notification_response(notification.id)
