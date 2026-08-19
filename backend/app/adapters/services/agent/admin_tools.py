from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.models import BookingConversation
from app.adapters.persistence.sqlalchemy.models import BookingFeedback
from app.adapters.persistence.sqlalchemy.models import BookingUpdate
from app.adapters.persistence.sqlalchemy.models import Payment
from app.adapters.persistence.sqlalchemy.models import SupportConversation
from app.adapters.persistence.sqlalchemy.models import SupportConversationMessage
from app.domain.booking.enums import BookingStatus
from app.domain.booking.policies import BOOKING_STATUS_TRANSITIONS
from app.domain.catalog.policies import InventoryAvailability
from app.dto.agent import AgentToolResult
from app.dto.store import analytics_summary_to_dto
from app.ports.services.clock import Clock
from app.shared.errors import BadRequestError
from app.shared.serialization import isoformat_or_none
from app.use_cases.agent.tools import AgentToolbox
from app.use_cases.store.get_store_analytics import AnalyticsFeedback
from app.use_cases.store.get_store_analytics import AnalyticsPayment
from app.use_cases.store.get_store_analytics import GetStoreAnalyticsUseCase


ALL_ADMIN_AGENT_TOOL_SPECS: tuple[dict[str, object], ...] = (
    {
        "name": "get_admin_operations_summary",
        "description": "Get current booking, inventory, payment, feedback, and unread support workload totals.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "find_admin_bookings",
        "description": "Find up to ten bookings and return their current status and allowed next statuses.",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": [status.value for status in BookingStatus],
                },
                "search": {"type": "string", "maxLength": 100},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "find_admin_inventory",
        "description": "Find up to ten inventory items by name or availability and return live stock values.",
        "parameters": {
            "type": "object",
            "properties": {
                "availability": {
                    "type": "string",
                    "enum": ["in_stock", "low_stock", "out_of_stock"],
                },
                "search": {"type": "string", "maxLength": 100},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "get_admin_payment_queue",
        "description": "Get recent payment requests for review. Payment decisions must remain in the payment screen.",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["pending", "paid", "failed", "cancelled"],
                }
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "get_admin_support_queue",
        "description": "Get recent booking-support conversations and their current states.",
        "parameters": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string",
                    "enum": ["waiting_admin", "admin_joined", "resolved", "closed"],
                }
            },
            "additionalProperties": False,
        },
    },
)


# FYP scope: the completed admin tools stay defined below for later re-enablement.
ACTIVE_ADMIN_AGENT_TOOL_NAMES = {
    "get_admin_operations_summary",
    # "find_admin_bookings",
    # "find_admin_inventory",
    # "get_admin_payment_queue",
    # "get_admin_support_queue",
}
ADMIN_AGENT_TOOL_SPECS = tuple(
    spec
    for spec in ALL_ADMIN_AGENT_TOOL_SPECS
    if spec["name"] in ACTIVE_ADMIN_AGENT_TOOL_NAMES
)


@dataclass
class AdminAgentToolbox(AgentToolbox):
    db: Session
    clock: Clock
    store_timezone: str

    def execute(
        self,
        *,
        name: str,
        arguments: dict[str, object],
        user_id: str,
    ) -> AgentToolResult:
        del user_id
        if name == "get_admin_operations_summary":
            return self.get_admin_operations_summary()
        if name == "find_admin_bookings":
            return self.find_admin_bookings(
                status=_optional_choice(
                    arguments,
                    "status",
                    {status.value for status in BookingStatus},
                ),
                search=_optional_text(arguments, "search", max_length=100),
            )
        if name == "find_admin_inventory":
            return self.find_admin_inventory(
                availability=cast(
                    InventoryAvailability | None,
                    _optional_choice(
                        arguments,
                        "availability",
                        {"in_stock", "low_stock", "out_of_stock"},
                    ),
                ),
                search=_optional_text(arguments, "search", max_length=100),
            )
        if name == "get_admin_payment_queue":
            return self.get_admin_payment_queue(
                status=_optional_choice(
                    arguments,
                    "status",
                    {"pending", "paid", "failed", "cancelled"},
                )
            )
        if name == "get_admin_support_queue":
            return self.get_admin_support_queue(
                state=_optional_choice(
                    arguments,
                    "state",
                    {"waiting_admin", "admin_joined", "resolved", "closed"},
                )
            )
        raise BadRequestError("Unknown admin Agent tool")

    def get_admin_operations_summary(self) -> AgentToolResult:
        booking_unread_chats = (
            self.db.scalar(
                select(func.count(func.distinct(BookingConversation.booking_id)))
                .join(
                    BookingUpdate,
                    BookingUpdate.booking_id == BookingConversation.booking_id,
                )
                .where(
                    BookingUpdate.channel == "conversation",
                    BookingUpdate.author_role == "customer",
                    or_(
                        BookingConversation.admin_last_read_at.is_(None),
                        BookingUpdate.created_at
                        > BookingConversation.admin_last_read_at,
                    ),
                )
            )
            or 0
        )
        general_unread_chats = (
            self.db.scalar(
                select(func.count(func.distinct(SupportConversation.id)))
                .join(
                    SupportConversationMessage,
                    SupportConversationMessage.conversation_id
                    == SupportConversation.id,
                )
                .where(
                    SupportConversationMessage.author_role == "customer",
                    or_(
                        SupportConversation.admin_last_read_at.is_(None),
                        SupportConversationMessage.created_at
                        > SupportConversation.admin_last_read_at,
                    ),
                )
            )
            or 0
        )
        summary = GetStoreAnalyticsUseCase(
            booking_repository=self.booking_repository,
            catalog_repository=self.catalog_repository,
            clock=self.clock,
        ).execute_summary(
            payments=[
                AnalyticsPayment(
                    status=payment.status,
                    payment_type=payment.payment_type,
                    amount=float(payment.amount),
                    updated_at=payment.updated_at,
                )
                for payment in self.db.scalars(select(Payment))
            ],
            feedback=[
                AnalyticsFeedback(booking_id=item.booking_id, rating=item.rating)
                for item in self.db.scalars(select(BookingFeedback))
            ],
            unread_chats=booking_unread_chats + general_unread_chats,
            store_timezone=self.store_timezone,
        )
        return AgentToolResult(
            data={"operations": analytics_summary_to_dto(summary).model_dump()},
            sources=[
                {
                    "source_type": "admin_operations",
                    "source_id": "current",
                    "label": "Current admin operations",
                    "version": self.clock.now().isoformat(),
                }
            ],
        )

    def find_admin_bookings(
        self,
        *,
        status: str | None,
        search: str | None,
    ) -> AgentToolResult:
        page = self.booking_repository.list_admin(
            status=status,
            search=search,
            sort_by="updated_at",
            sort_order="desc",
            limit=10,
            offset=0,
        )
        bookings = [
            {
                "booking_id": item.id,
                "order_code": item.order_code,
                "status": item.status,
                "string_name": item.string_name,
                "customer_username": item.customer_username,
                "customer_phone": _masked_phone(item.customer_phone_number),
                "racket": " ".join(
                    value for value in (item.racket_brand, item.racket_model) if value
                )
                or None,
                "requested_tension": item.requested_tension,
                "drop_off_datetime": isoformat_or_none(item.drop_off_datetime),
                "updated_at": isoformat_or_none(item.updated_at),
                "allowed_next_statuses": sorted(
                    status.value
                    for status in BOOKING_STATUS_TRANSITIONS[BookingStatus(item.status)]
                ),
            }
            for item in page.items
        ]
        return AgentToolResult(
            data={"bookings": bookings, "total": page.total},
            sources=[
                {
                    "source_type": "booking",
                    "source_id": item.id,
                    "label": f"Booking {item.order_code}",
                    "version": isoformat_or_none(item.updated_at),
                }
                for item in page.items
            ],
        )

    def find_admin_inventory(
        self,
        *,
        availability: InventoryAvailability | None,
        search: str | None,
    ) -> AgentToolResult:
        page = self.catalog_repository.list_inventory(
            brand=None,
            search=search,
            availability=availability,
            limit=10,
            offset=0,
        )
        return AgentToolResult(
            data={
                "inventory": [
                    {
                        "catalog_id": item.id,
                        "display_name": item.display_name,
                        "current_stock": item.current_stock,
                        "reserved_stock": item.reserved_stock,
                        "available_stock": item.available_stock,
                        "reorder_level": item.reorder_level,
                        "availability_status": (
                            item.inventory.availability_status
                            if item.inventory
                            else "out_of_stock"
                        ),
                        "selling_price": item.selling_price,
                        "updated_at": isoformat_or_none(item.updated_at),
                    }
                    for item in page.items
                ],
                "total": page.total,
            },
            sources=[
                {
                    "source_type": "admin_inventory",
                    "source_id": item.id,
                    "label": item.display_name,
                    "version": isoformat_or_none(item.updated_at),
                }
                for item in page.items
            ],
        )

    def get_admin_payment_queue(self, *, status: str | None) -> AgentToolResult:
        query = select(Payment).order_by(Payment.updated_at.desc()).limit(20)
        if status:
            query = query.where(Payment.status == status)
        payments = list(self.db.scalars(query))
        return AgentToolResult(
            data={
                "payments": [
                    {
                        "payment_id": payment.id,
                        "booking_id": payment.booking_id,
                        "status": payment.status,
                        "payment_type": payment.payment_type,
                        "amount_rm": float(payment.amount),
                        "reference": payment.reference,
                        "updated_at": payment.updated_at.isoformat(),
                    }
                    for payment in payments
                ]
            },
            sources=[
                {
                    "source_type": "payment",
                    "source_id": payment.id,
                    "label": f"Payment {payment.reference}",
                    "version": payment.updated_at.isoformat(),
                }
                for payment in payments
            ],
        )

    def get_admin_support_queue(self, *, state: str | None) -> AgentToolResult:
        query = (
            select(BookingConversation)
            .order_by(BookingConversation.updated_at.desc())
            .limit(20)
        )
        if state:
            query = query.where(BookingConversation.state == state)
        conversations = list(self.db.scalars(query))
        return AgentToolResult(
            data={
                "conversations": [
                    {
                        "conversation_id": conversation.booking_id,
                        "booking_id": conversation.booking_id,
                        "state": conversation.state,
                        "support_requested_at": conversation.support_requested_at.isoformat(),
                        "updated_at": conversation.updated_at.isoformat(),
                    }
                    for conversation in conversations
                ]
            },
            sources=[
                {
                    "source_type": "admin_conversation",
                    "source_id": conversation.booking_id,
                    "label": f"Support conversation {conversation.booking_id}",
                    "version": conversation.updated_at.isoformat(),
                }
                for conversation in conversations
            ],
        )


def _optional_text(
    arguments: dict[str, object],
    key: str,
    *,
    max_length: int,
) -> str | None:
    value = arguments.get(key)
    if value is None:
        return None
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value.strip()) > max_length
    ):
        raise BadRequestError(f"{key} must be a non-empty string")
    return value.strip()


def _optional_choice(
    arguments: dict[str, object],
    key: str,
    choices: set[str],
) -> str | None:
    value = _optional_text(arguments, key, max_length=100)
    if value is not None and value not in choices:
        raise BadRequestError(f"Unsupported {key}")
    return value


def _masked_phone(value: str | None) -> str | None:
    if not value:
        return None
    return f"***{value[-4:]}"
