from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import cast

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.models.booking import Booking
from app.adapters.persistence.sqlalchemy.models.booking import BookingStatusHistory
from app.adapters.persistence.sqlalchemy.models.booking import BookingUpdate
from app.adapters.persistence.sqlalchemy.models.commerce import Payment
from app.adapters.persistence.sqlalchemy.models.notification import DeviceToken
from app.adapters.persistence.sqlalchemy.models.notification import NotificationDelivery
from app.adapters.persistence.sqlalchemy.models.notification import NotificationRead
from app.adapters.persistence.sqlalchemy.models.recommendation_log import (
    RecommendationRun,
)
from app.adapters.persistence.sqlalchemy.session import get_db
from app.dto.notifications import DevicePlatform
from app.dto.notifications import DeviceTokenOut
from app.dto.notifications import MarkNotificationsReadOut
from app.dto.notifications import MarkNotificationsReadPayload
from app.dto.notifications import NotificationCategory
from app.dto.notifications import NotificationOut
from app.dto.notifications import NotificationPreferencesPayload
from app.dto.notifications import PushTokenPayload
from app.dto.notifications import notification_preferences_to_dto
from app.entrypoints.api.dependencies import CurrentUser
from app.entrypoints.api.dependencies import get_current_customer
from app.entrypoints.api.dependencies import get_profile_repository
from app.shared.errors import NotFoundError


router = APIRouter(prefix="/notifications", tags=["notifications"])
devices_router = APIRouter(prefix="/devices", tags=["devices"])

MAX_NOTIFICATION_EVENTS = 200

STATUS_TITLES = {
    "awaiting_dropoff": "Awaiting drop-off",
    "in_progress": "Stringing in progress",
    "ready_for_collection": "Ready for collection",
    "completed": "Service completed",
    "cancelled": "Booking cancelled",
    "rejected": "Booking rejected",
}


def _derived_notification_events(
    db: Session,
    *,
    user_id: str,
    enabled_categories: set[str] | None,
    limit: int,
) -> list[NotificationOut]:
    # ponytail: cap each source at 200 rows; add cursor queries if user histories
    # outgrow the FYP notification feed.
    status_rows = db.execute(
        select(BookingStatusHistory, Booking.id)
        .join(Booking, Booking.id == BookingStatusHistory.booking_id)
        .where(Booking.user_id == user_id)
        .order_by(BookingStatusHistory.changed_at.desc())
        .limit(MAX_NOTIFICATION_EVENTS)
    ).all()
    update_rows = db.execute(
        select(BookingUpdate, Booking.id)
        .join(Booking, Booking.id == BookingUpdate.booking_id)
        .where(
            Booking.user_id == user_id,
            BookingUpdate.author_role == "admin",
            BookingUpdate.channel == "service",
        )
        .order_by(BookingUpdate.created_at.desc())
        .limit(MAX_NOTIFICATION_EVENTS)
    ).all()
    chat_rows = db.execute(
        select(BookingUpdate, Booking.id)
        .join(Booking, Booking.id == BookingUpdate.booking_id)
        .where(
            Booking.user_id == user_id,
            BookingUpdate.author_role == "admin",
            BookingUpdate.channel == "conversation",
        )
        .order_by(BookingUpdate.created_at.desc())
        .limit(MAX_NOTIFICATION_EVENTS)
    ).all()
    payments = db.scalars(
        select(Payment)
        .where(Payment.user_id == user_id)
        .order_by(Payment.updated_at.desc())
        .limit(MAX_NOTIFICATION_EVENTS)
    ).all()
    recommendation_runs = db.scalars(
        select(RecommendationRun)
        .where(RecommendationRun.user_id == user_id)
        .order_by(RecommendationRun.generated_at.desc())
        .limit(MAX_NOTIFICATION_EVENTS)
    ).all()
    persisted_notifications = db.scalars(
        select(NotificationDelivery)
        .where(NotificationDelivery.user_id == user_id)
        .order_by(NotificationDelivery.created_at.desc())
        .limit(MAX_NOTIFICATION_EVENTS)
    ).all()

    events = [
        NotificationOut(
            id=f"booking-status:{history.id}",
            user_id=user_id,
            category="booking" if history.old_status is None else "service",
            title=(
                "Booking created"
                if history.old_status is None
                else STATUS_TITLES.get(
                    history.new_status,
                    f"Booking status: {history.new_status.replace('_', ' ').title()}",
                )
            ),
            body=history.note
            or (
                "Your booking was received by the shop."
                if history.old_status is None
                else f"Your booking moved to {history.new_status.replace('_', ' ')}."
            ),
            created_at=history.changed_at,
            route=f"/player/bookings/{booking_id}",
        )
        for history, booking_id in status_rows
    ]
    events.extend(
        NotificationOut(
            id=f"booking-update:{update.id}",
            user_id=user_id,
            category="service",
            title="New booking update",
            body=(
                update.comment[:500]
                if update.comment
                else "The shop added a new service update."
            ),
            created_at=update.created_at,
            route=f"/player/bookings/{booking_id}",
        )
        for update, booking_id in update_rows
    )
    events.extend(
        NotificationOut(
            id=f"conversation-update:{update.id}",
            user_id=user_id,
            category="chat",
            title="New shop reply",
            body=update.comment[:500] if update.comment else "The shop replied.",
            created_at=update.created_at,
            route=f"/player/chat/{booking_id}",
        )
        for update, booking_id in chat_rows
    )
    events.extend(_payment_notification(payment) for payment in payments)
    events.extend(
        NotificationOut(
            id=f"recommendation:{run.id}",
            user_id=user_id,
            category="recommendation",
            title="Recommendation ready",
            body="Your latest string recommendation is ready to review.",
            created_at=run.generated_at,
            route="/player/results",
        )
        for run in recommendation_runs
    )
    events.extend(
        NotificationOut(
            id=f"push:{notification.id}",
            user_id=user_id,
            category=cast(NotificationCategory, notification.category),
            title=notification.title,
            body=notification.body,
            created_at=notification.created_at,
            route=notification.route or "/player/notifications",
        )
        for notification in persisted_notifications
    )

    if enabled_categories is not None:
        events = [event for event in events if event.category in enabled_categories]
    return sorted(events, key=lambda event: event.created_at, reverse=True)[:limit]


def _payment_notification(payment: Payment) -> NotificationOut:
    is_top_up = payment.payment_type == "wallet_top_up"
    subject = "Wallet top-up" if is_top_up else "Payment"
    titles = {
        "pending": f"{subject} pending",
        "paid": f"{subject} confirmed",
        "failed": f"{subject} failed",
        "cancelled": f"{subject} cancelled",
    }
    return NotificationOut(
        id=f"payment:{payment.id}:{payment.status}",
        user_id=payment.user_id,
        category="payment",
        title=titles.get(payment.status, f"{subject} updated"),
        body=payment.note or f"{payment.reference} is {payment.status}.",
        created_at=(
            payment.created_at if payment.status == "pending" else payment.updated_at
        ),
        route=(
            f"/player/payments/{payment.booking_id}"
            if payment.booking_id
            else "/player/wallet"
        ),
    )


def _with_read_state(
    db: Session,
    *,
    user_id: str,
    events: list[NotificationOut],
) -> list[NotificationOut]:
    if not events:
        return []
    event_ids = [event.id for event in events]
    read_ids = set(
        db.scalars(
            select(NotificationRead.event_id).where(
                NotificationRead.user_id == user_id,
                NotificationRead.event_id.in_(event_ids),
            )
        ).all()
    )
    return [event.model_copy(update={"read": event.id in read_ids}) for event in events]


@router.get("", response_model=list[NotificationOut])
def list_notifications(
    limit: int = Query(default=100, ge=1, le=MAX_NOTIFICATION_EVENTS),
    current_user: CurrentUser = Depends(get_current_customer),
    profile_repository=Depends(get_profile_repository),
    db: Session = Depends(get_db, scope="function"),
) -> list[NotificationOut]:
    preferences = notification_preferences_to_dto(
        profile_repository.get_notification_preferences(current_user.user_id)
    ).model_dump()
    enabled_categories = {
        category for category, enabled in preferences.items() if enabled
    }
    events = _derived_notification_events(
        db,
        user_id=current_user.user_id,
        enabled_categories=enabled_categories,
        limit=limit,
    )
    return _with_read_state(db, user_id=current_user.user_id, events=events)


@router.patch("/read", response_model=MarkNotificationsReadOut)
def mark_notifications_read(
    payload: MarkNotificationsReadPayload,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db, scope="function"),
) -> MarkNotificationsReadOut:
    event_ids = list(dict.fromkeys(payload.event_ids))
    owned_ids = {
        event.id
        for event in _derived_notification_events(
            db,
            user_id=current_user.user_id,
            enabled_categories=None,
            limit=MAX_NOTIFICATION_EVENTS,
        )
    }
    if any(event_id not in owned_ids for event_id in event_ids):
        raise NotFoundError("Notification not found")

    already_read = set(
        db.scalars(
            select(NotificationRead.event_id).where(
                NotificationRead.user_id == current_user.user_id,
                NotificationRead.event_id.in_(event_ids),
            )
        ).all()
    )
    db.add_all(
        NotificationRead(user_id=current_user.user_id, event_id=event_id)
        for event_id in event_ids
        if event_id not in already_read
    )
    db.flush()
    return MarkNotificationsReadOut(
        marked_count=len(event_ids),
        marked_read_ids=event_ids,
    )


@router.get("/preferences", response_model=NotificationPreferencesPayload)
def get_notification_preferences(
    current_user: CurrentUser = Depends(get_current_customer),
    profile_repository=Depends(get_profile_repository),
) -> NotificationPreferencesPayload:
    return notification_preferences_to_dto(
        profile_repository.get_notification_preferences(current_user.user_id)
    )


@router.put("/preferences", response_model=NotificationPreferencesPayload)
def update_notification_preferences(
    payload: NotificationPreferencesPayload,
    current_user: CurrentUser = Depends(get_current_customer),
    profile_repository=Depends(get_profile_repository),
) -> NotificationPreferencesPayload:
    values = profile_repository.update_notification_preferences(
        current_user.user_id,
        payload.model_dump(),
    )
    return notification_preferences_to_dto(values)


def _token_preview(token: str) -> str:
    return f"{token[:8]}…{token[-6:]}"


@devices_router.post("/push-token", response_model=DeviceTokenOut)
def register_push_token(
    payload: PushTokenPayload,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db, scope="function"),
) -> DeviceTokenOut:
    record = db.scalar(select(DeviceToken).where(DeviceToken.token == payload.token))
    now = datetime.now(timezone.utc)
    if record is None:
        record = DeviceToken(
            user_id=current_user.user_id,
            token=payload.token,
            platform=payload.platform,
            device_name=payload.device_name,
            enabled=payload.enabled,
            last_seen_at=now,
        )
        db.add(record)
    else:
        record.user_id = current_user.user_id
        record.platform = payload.platform
        record.device_name = payload.device_name
        record.enabled = payload.enabled
        record.last_seen_at = now
    db.flush()
    db.refresh(record)
    return DeviceTokenOut(
        id=record.id,
        user_id=record.user_id,
        token_preview=_token_preview(record.token),
        platform=cast(DevicePlatform, record.platform),
        device_name=record.device_name,
        enabled=record.enabled,
        last_seen_at=record.last_seen_at,
    )
