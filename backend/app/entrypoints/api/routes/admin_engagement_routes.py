from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timezone
from typing import cast
from urllib import request as urllib_request

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import Response
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.models import Booking
from app.adapters.persistence.sqlalchemy.models import BookingFeedback
from app.adapters.persistence.sqlalchemy.models import DeviceToken
from app.adapters.persistence.sqlalchemy.models import NotificationDelivery
from app.adapters.persistence.sqlalchemy.models import StoreSettings
from app.adapters.persistence.sqlalchemy.models import StringCatalogItem
from app.adapters.persistence.sqlalchemy.models import User
from app.adapters.persistence.sqlalchemy.session import SessionLocal
from app.adapters.persistence.sqlalchemy.session import get_db
from app.config.settings import get_settings
from app.domain.booking.policies import booking_order_code
from app.dto.notifications import AdminDeviceTokenOut
from app.dto.notifications import AdminNotificationOut
from app.dto.notifications import DevicePlatform
from app.dto.notifications import NotificationCategory
from app.dto.notifications import SendNotificationPayload
from app.dto.racket_feedback import AdminFeedbackOut
from app.entrypoints.api.dependencies import CurrentUser
from app.entrypoints.api.dependencies import get_current_admin
from app.entrypoints.api.routes.racket_feedback_routes import feedback_to_dto
from app.shared.errors import NotFoundError


router = APIRouter(prefix="/admin", tags=["admin"])


@dataclass(frozen=True, slots=True)
class _NotificationDeliveryTarget:
    token: str
    title: str
    body: str
    route: str | None
    endpoint: str


def _token_preview(token: str) -> str:
    return f"{token[:8]}…{token[-6:]}"


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
    device_token: DeviceToken | None,
) -> AdminNotificationOut:
    return AdminNotificationOut(
        id=notification.id,
        user_id=notification.user_id,
        customer_username=user.username,
        customer_phone_number=user.phone_number,
        token_preview=_token_preview(device_token.token) if device_token else None,
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
    device_token = (
        db.get(DeviceToken, notification.device_token_id)
        if notification.device_token_id
        else db.scalar(
            select(DeviceToken)
            .where(
                DeviceToken.user_id == notification.user_id,
                DeviceToken.enabled.is_(True),
            )
            .order_by(DeviceToken.last_seen_at.desc())
            .limit(1)
        )
    )
    notification.attempts += 1
    notification.last_attempt_at = datetime.now(timezone.utc)
    if device_token is None or not device_token.enabled:
        notification.status = "failed"
        notification.provider_message = "No active device token"
        return False
    notification.device_token_id = device_token.id

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

    settings = get_settings()
    if not settings.expo_push_enabled:
        notification.status = "disabled"
        notification.provider_message = "Expo push delivery is disabled"
        return False

    notification.status = "pending"
    notification.provider_message = None
    return True


def _send_notification_to_provider(
    target: _NotificationDeliveryTarget,
) -> tuple[str, str | None]:
    body = json.dumps(
        {
            "to": target.token,
            "title": target.title,
            "body": target.body,
            "data": {"route": target.route} if target.route else {},
        }
    ).encode("utf-8")
    request = urllib_request.Request(
        target.endpoint,
        data=body,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib_request.urlopen(request, timeout=5) as response:
            provider_response = json.loads(response.read().decode("utf-8"))
        if not isinstance(provider_response, dict):
            raise ValueError("Expo returned an invalid response")
        ticket = provider_response.get("data", {})
        if not isinstance(ticket, dict):
            raise ValueError("Expo returned an invalid delivery ticket")
        status = "sent" if ticket.get("status") == "ok" else "failed"
        provider_message = ticket.get("message") or ticket.get("id")
        return status, str(provider_message) if provider_message is not None else None
    except (OSError, TypeError, ValueError) as exc:
        return "failed", str(exc)[:500]


def _notification_response_for_session(
    db: Session,
    notification: NotificationDelivery,
) -> AdminNotificationOut:
    user = db.get(User, notification.user_id)
    if user is None:
        raise NotFoundError("User not found")
    device_token = (
        db.get(DeviceToken, notification.device_token_id)
        if notification.device_token_id
        else None
    )
    return _notification_dto(notification, user, device_token)


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
        device_token = (
            db.get(DeviceToken, notification.device_token_id)
            if notification.device_token_id
            else None
        )
        if device_token is None or not device_token.enabled:
            provider_message = "No active device token"
        else:
            target = _NotificationDeliveryTarget(
                token=device_token.token,
                title=notification.title,
                body=notification.body,
                route=notification.route,
                endpoint=get_settings().expo_push_endpoint,
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


@router.get("/device-tokens", response_model=list[AdminDeviceTokenOut])
def admin_device_tokens(
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db, scope="function"),
) -> list[AdminDeviceTokenOut]:
    rows = db.execute(
        select(DeviceToken, User)
        .join(User, User.id == DeviceToken.user_id)
        .order_by(DeviceToken.last_seen_at.desc())
    ).all()
    return [
        AdminDeviceTokenOut(
            id=token.id,
            user_id=token.user_id,
            token_preview=_token_preview(token.token),
            platform=cast(DevicePlatform, token.platform),
            device_name=token.device_name,
            enabled=token.enabled,
            last_seen_at=token.last_seen_at,
            customer_username=user.username,
            customer_phone_number=user.phone_number,
        )
        for token, user in rows
    ]


@router.get("/notifications", response_model=list[AdminNotificationOut])
def admin_notifications(
    status: str | None = Query(default=None, max_length=20),
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db, scope="function"),
) -> list[AdminNotificationOut]:
    query = (
        select(NotificationDelivery, User, DeviceToken)
        .join(User, User.id == NotificationDelivery.user_id)
        .outerjoin(DeviceToken, DeviceToken.id == NotificationDelivery.device_token_id)
    )
    if status:
        query = query.where(NotificationDelivery.status == status)
    rows = db.execute(query.order_by(NotificationDelivery.created_at.desc())).all()
    return [
        _notification_dto(notification, user, device_token)
        for notification, user, device_token in rows
    ]


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
