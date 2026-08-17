from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
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
from app.adapters.persistence.sqlalchemy.session import get_db
from app.config.settings import get_settings
from app.dto.store import AnalyticsSummaryOut
from app.dto.store import PopularStringOut
from app.dto.store import analytics_summary_to_dto
from app.dto.store import popular_string_to_dto
from app.entrypoints.api.dependencies import CurrentUser
from app.entrypoints.api.dependencies import get_booking_repository
from app.entrypoints.api.dependencies import get_catalog_repository
from app.entrypoints.api.dependencies import get_clock
from app.entrypoints.api.dependencies import get_current_admin
from app.use_cases.store.get_store_analytics import AnalyticsFeedback
from app.use_cases.store.get_store_analytics import AnalyticsPayment
from app.use_cases.store.get_store_analytics import GetStoreAnalyticsUseCase


router = APIRouter(prefix="/admin/analytics", tags=["admin"])


@router.get("/summary", response_model=AnalyticsSummaryOut)
def admin_analytics_summary(
    _: CurrentUser = Depends(get_current_admin),
    booking_repository=Depends(get_booking_repository),
    catalog_repository=Depends(get_catalog_repository),
    clock=Depends(get_clock),
    db: Session = Depends(get_db, scope="function"),
) -> AnalyticsSummaryOut:
    booking_unread_chats = (
        db.scalar(
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
                    BookingUpdate.created_at > BookingConversation.admin_last_read_at,
                ),
            )
        )
        or 0
    )
    general_unread_chats = (
        db.scalar(
            select(func.count(func.distinct(SupportConversation.id)))
            .join(
                SupportConversationMessage,
                SupportConversationMessage.conversation_id == SupportConversation.id,
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
        booking_repository=booking_repository,
        catalog_repository=catalog_repository,
        clock=clock,
    ).execute_summary(
        payments=[
            AnalyticsPayment(
                status=payment.status,
                payment_type=payment.payment_type,
                amount=float(payment.amount),
                updated_at=payment.updated_at,
            )
            for payment in db.execute(select(Payment)).scalars()
        ],
        feedback=[
            AnalyticsFeedback(booking_id=item.booking_id, rating=item.rating)
            for item in db.scalars(select(BookingFeedback))
        ],
        unread_chats=booking_unread_chats + general_unread_chats,
        store_timezone=get_settings().store_timezone,
    )
    return analytics_summary_to_dto(summary)


@router.get("/popular-strings", response_model=list[PopularStringOut])
def admin_popular_strings(
    limit: int = Query(default=5, ge=1, le=20),
    _: CurrentUser = Depends(get_current_admin),
    booking_repository=Depends(get_booking_repository),
    catalog_repository=Depends(get_catalog_repository),
    clock=Depends(get_clock),
) -> list[PopularStringOut]:
    items = GetStoreAnalyticsUseCase(
        booking_repository=booking_repository,
        catalog_repository=catalog_repository,
        clock=clock,
    ).execute_popular_strings(limit=limit)
    return [popular_string_to_dto(item) for item in items]
