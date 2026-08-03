from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import cast

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.models.booking import Booking
from app.adapters.persistence.sqlalchemy.models.booking import BookingUpdate
from app.adapters.persistence.sqlalchemy.models.booking_conversation import (
    BookingConversation,
)
from app.adapters.persistence.sqlalchemy.session import get_db
from app.domain.auth.entities import UserRole
from app.dto.booking_conversation import BookingConversationMessageOut
from app.dto.booking_conversation import BookingConversationOut
from app.dto.booking_conversation import ConversationState
from app.dto.booking_conversation import SendConversationMessagePayload
from app.entrypoints.api.dependencies import CurrentUser
from app.entrypoints.api.dependencies import get_current_admin
from app.entrypoints.api.dependencies import get_current_customer
from app.shared.errors import ConflictError
from app.shared.errors import ForbiddenError
from app.shared.errors import NotFoundError
from app.shared.serialization import isoformat_or_none


router = APIRouter(tags=["booking-conversations"])


def _require_player(current_user: CurrentUser) -> None:
    if current_user.role != UserRole.CUSTOMER.value:
        raise ForbiddenError("Insufficient permissions for this resource")


def _get_conversation(
    db: Session,
    conversation_id: str,
    *,
    player_id: str | None = None,
    for_update: bool = False,
) -> tuple[BookingConversation, str]:
    statement = (
        select(BookingConversation, Booking.user_id)
        .join(Booking, Booking.id == BookingConversation.booking_id)
        .where(BookingConversation.booking_id == conversation_id)
    )
    if player_id is not None:
        statement = statement.where(Booking.user_id == player_id)
    if for_update:
        statement = statement.with_for_update()
    row = db.execute(statement).first()
    if row is None:
        raise NotFoundError("Conversation not found")
    return row[0], row[1]


def _messages_by_booking_id(
    db: Session,
    booking_ids: list[str],
) -> dict[str, list[BookingConversationMessageOut]]:
    messages: dict[str, list[BookingConversationMessageOut]] = {
        booking_id: [] for booking_id in booking_ids
    }
    if not booking_ids:
        return messages
    updates = (
        db.execute(
            select(BookingUpdate)
            .where(
                BookingUpdate.booking_id.in_(booking_ids),
                BookingUpdate.channel == "conversation",
                BookingUpdate.comment.is_not(None),
            )
            .order_by(BookingUpdate.created_at.asc())
        )
        .scalars()
        .all()
    )
    for update in updates:
        if not update.comment or not update.comment.strip():
            continue
        messages[update.booking_id].append(
            BookingConversationMessageOut(
                id=update.id,
                author_user_id=update.author_user_id,
                author_role=update.author_role,
                body=update.comment,
                created_at=isoformat_or_none(update.created_at),
            )
        )
    return messages


def _conversation_to_dto(
    conversation: BookingConversation,
    *,
    player_id: str,
    messages: list[BookingConversationMessageOut],
) -> BookingConversationOut:
    return BookingConversationOut(
        id=conversation.booking_id,
        booking_id=conversation.booking_id,
        player_id=player_id,
        state=cast(ConversationState, conversation.state),
        support_requested_at=conversation.support_requested_at.isoformat(),
        player_last_read_at=isoformat_or_none(conversation.player_last_read_at),
        admin_last_read_at=isoformat_or_none(conversation.admin_last_read_at),
        created_at=isoformat_or_none(conversation.created_at),
        updated_at=isoformat_or_none(conversation.updated_at),
        messages=messages,
    )


def _conversation_with_messages(
    db: Session,
    conversation: BookingConversation,
    *,
    player_id: str,
) -> BookingConversationOut:
    messages = _messages_by_booking_id(db, [conversation.booking_id])
    return _conversation_to_dto(
        conversation,
        player_id=player_id,
        messages=messages[conversation.booking_id],
    )


def _list_conversations(
    db: Session,
    *,
    player_id: str | None = None,
) -> list[BookingConversationOut]:
    statement = (
        select(BookingConversation, Booking.user_id)
        .join(Booking, Booking.id == BookingConversation.booking_id)
        .order_by(BookingConversation.updated_at.desc())
    )
    if player_id is not None:
        statement = statement.where(Booking.user_id == player_id)
    rows = db.execute(statement).all()
    messages = _messages_by_booking_id(
        db,
        [row[0].booking_id for row in rows],
    )
    return [
        _conversation_to_dto(
            row[0],
            player_id=row[1],
            messages=messages[row[0].booking_id],
        )
        for row in rows
    ]


def _request_support(
    db: Session,
    *,
    booking_id: str,
    player_id: str,
) -> BookingConversationOut:
    booking = db.execute(
        select(Booking)
        .where(Booking.id == booking_id, Booking.user_id == player_id)
        .with_for_update()
    ).scalar_one_or_none()
    if booking is None:
        raise NotFoundError("Booking not found")

    now = datetime.now(timezone.utc)
    conversation = db.get(BookingConversation, booking_id)
    if conversation is None:
        conversation = BookingConversation(
            booking_id=booking_id,
            state="waiting_admin",
            support_requested_at=now,
            updated_at=now,
        )
        db.add(conversation)
    elif conversation.state in {"resolved", "closed"}:
        conversation.state = "waiting_admin"
        conversation.support_requested_at = now
        conversation.updated_at = now

    db.flush()
    db.refresh(conversation)
    return _conversation_with_messages(
        db,
        conversation,
        player_id=player_id,
    )


def _send_message(
    db: Session,
    *,
    conversation_id: str,
    current_user: CurrentUser,
    body: str,
    player_endpoint: bool,
) -> BookingConversationOut:
    conversation, player_id = _get_conversation(
        db,
        conversation_id,
        player_id=current_user.user_id if player_endpoint else None,
        for_update=True,
    )
    if conversation.state in {"resolved", "closed"}:
        raise ConflictError("Conversation is not open")

    now = datetime.now(timezone.utc)
    db.add(
        BookingUpdate(
            booking_id=conversation.booking_id,
            author_user_id=current_user.user_id,
            author_role=current_user.role,
            channel="conversation",
            comment=body,
        )
    )
    if current_user.role == UserRole.ADMIN.value:
        conversation.state = "admin_joined"
    conversation.updated_at = now
    db.flush()
    db.refresh(conversation)
    return _conversation_with_messages(
        db,
        conversation,
        player_id=player_id,
    )


def _mark_read(
    db: Session,
    *,
    conversation_id: str,
    current_user: CurrentUser,
    player_endpoint: bool,
) -> BookingConversationOut:
    conversation, player_id = _get_conversation(
        db,
        conversation_id,
        player_id=current_user.user_id if player_endpoint else None,
        for_update=True,
    )
    if player_endpoint:
        conversation.player_last_read_at = datetime.now(timezone.utc)
    else:
        conversation.admin_last_read_at = datetime.now(timezone.utc)
    db.flush()
    db.refresh(conversation)
    return _conversation_with_messages(
        db,
        conversation,
        player_id=player_id,
    )


def _set_admin_state(
    db: Session,
    *,
    conversation_id: str,
    state: ConversationState,
) -> BookingConversationOut:
    conversation, player_id = _get_conversation(
        db,
        conversation_id,
        for_update=True,
    )
    if state == "resolved" and conversation.state == "closed":
        raise ConflictError("Closed conversations cannot be resolved")
    conversation.state = state
    conversation.updated_at = datetime.now(timezone.utc)
    db.flush()
    db.refresh(conversation)
    return _conversation_with_messages(
        db,
        conversation,
        player_id=player_id,
    )


@router.get("/conversations", response_model=list[BookingConversationOut])
def list_player_conversations(
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db, scope="function"),
) -> list[BookingConversationOut]:
    _require_player(current_user)
    return _list_conversations(db, player_id=current_user.user_id)


@router.post(
    "/bookings/{booking_id}/support",
    response_model=BookingConversationOut,
)
def request_booking_support(
    booking_id: str,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db, scope="function"),
) -> BookingConversationOut:
    _require_player(current_user)
    return _request_support(
        db,
        booking_id=booking_id,
        player_id=current_user.user_id,
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=BookingConversationOut,
)
def get_player_conversation(
    conversation_id: str,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db, scope="function"),
) -> BookingConversationOut:
    _require_player(current_user)
    conversation, player_id = _get_conversation(
        db,
        conversation_id,
        player_id=current_user.user_id,
    )
    return _conversation_with_messages(
        db,
        conversation,
        player_id=player_id,
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=BookingConversationOut,
)
def send_player_conversation_message(
    conversation_id: str,
    payload: SendConversationMessagePayload,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db, scope="function"),
) -> BookingConversationOut:
    _require_player(current_user)
    return _send_message(
        db,
        conversation_id=conversation_id,
        current_user=current_user,
        body=payload.body,
        player_endpoint=True,
    )


@router.post(
    "/conversations/{conversation_id}/read",
    response_model=BookingConversationOut,
)
def mark_player_conversation_read(
    conversation_id: str,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db, scope="function"),
) -> BookingConversationOut:
    _require_player(current_user)
    return _mark_read(
        db,
        conversation_id=conversation_id,
        current_user=current_user,
        player_endpoint=True,
    )


@router.get(
    "/admin/conversations",
    response_model=list[BookingConversationOut],
)
def list_admin_conversations(
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db, scope="function"),
) -> list[BookingConversationOut]:
    return _list_conversations(db)


@router.get(
    "/admin/conversations/{conversation_id}",
    response_model=BookingConversationOut,
)
def get_admin_conversation(
    conversation_id: str,
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db, scope="function"),
) -> BookingConversationOut:
    conversation, player_id = _get_conversation(db, conversation_id)
    return _conversation_with_messages(
        db,
        conversation,
        player_id=player_id,
    )


@router.post(
    "/admin/conversations/{conversation_id}/messages",
    response_model=BookingConversationOut,
)
def send_admin_conversation_message(
    conversation_id: str,
    payload: SendConversationMessagePayload,
    current_user: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db, scope="function"),
) -> BookingConversationOut:
    return _send_message(
        db,
        conversation_id=conversation_id,
        current_user=current_user,
        body=payload.body,
        player_endpoint=False,
    )


@router.post(
    "/admin/conversations/{conversation_id}/read",
    response_model=BookingConversationOut,
)
def mark_admin_conversation_read(
    conversation_id: str,
    current_user: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db, scope="function"),
) -> BookingConversationOut:
    return _mark_read(
        db,
        conversation_id=conversation_id,
        current_user=current_user,
        player_endpoint=False,
    )


@router.post(
    "/admin/conversations/{conversation_id}/resolve",
    response_model=BookingConversationOut,
)
def resolve_admin_conversation(
    conversation_id: str,
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db, scope="function"),
) -> BookingConversationOut:
    return _set_admin_state(
        db,
        conversation_id=conversation_id,
        state="resolved",
    )


@router.post(
    "/admin/conversations/{conversation_id}/close",
    response_model=BookingConversationOut,
)
def close_admin_conversation(
    conversation_id: str,
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db, scope="function"),
) -> BookingConversationOut:
    return _set_admin_state(
        db,
        conversation_id=conversation_id,
        state="closed",
    )
