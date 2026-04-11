from __future__ import annotations

from datetime import date
from typing import Literal
from typing import cast

from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import Form
from fastapi import Query
from fastapi import UploadFile

from app.config.settings import get_settings
from app.dto.booking import BookingOut
from app.dto.booking import UpdateBookingStatusPayload
from app.dto.booking import booking_to_dto
from app.dto.catalog import AdminInventoryStringOut
from app.dto.catalog import InventoryUpdatePayload
from app.dto.catalog import StringOut
from app.dto.catalog import StringWritePayload
from app.dto.catalog import inventory_string_to_dto
from app.dto.catalog import string_to_dto
from app.dto.common import page_to_dict
from app.dto.recommendation import recommendation_log_to_dict
from app.dto.store import AnalyticsSummaryOut
from app.dto.store import CheckInLookupOut
from app.dto.store import CheckInPayload
from app.dto.store import PopularStringOut
from app.dto.store import ServiceQueueItemOut
from app.dto.store import ServiceQueueLaneOut
from app.dto.store import ServiceQueueOut
from app.dto.store import StoreBusinessHoursOut
from app.dto.store import StoreBusinessHoursPayload
from app.dto.store import StoreSettingsOut
from app.dto.store import StoreSettingsPayload
from app.dto.store import analytics_summary_to_dto
from app.dto.store import business_hours_to_dto
from app.dto.store import popular_string_to_dto
from app.dto.store import settings_to_dto
from app.dto.store import slot_to_dto
from app.entrypoints.api.dependencies import CurrentUser
from app.entrypoints.api.dependencies import get_booking_repository
from app.entrypoints.api.dependencies import get_catalog_repository
from app.entrypoints.api.dependencies import get_clock
from app.entrypoints.api.dependencies import get_current_admin
from app.entrypoints.api.dependencies import get_recommendation_log_repository
from app.entrypoints.api.dependencies import get_store_repository
from app.shared.upload_storage import save_booking_update_photo
from app.use_cases.booking.add_booking_update import AddBookingUpdateUseCase
from app.use_cases.booking.get_booking import GetBookingUseCase
from app.use_cases.booking.list_admin_bookings import ListAdminBookingsUseCase
from app.use_cases.booking.update_booking_status import UpdateBookingStatusUseCase
from app.use_cases.catalog.create_string import CreateStringUseCase
from app.use_cases.catalog.deactivate_string import DeactivateStringUseCase
from app.use_cases.catalog.get_string import GetStringUseCase
from app.use_cases.catalog.list_inventory_strings import ListInventoryStringsUseCase
from app.use_cases.catalog.list_strings import ListStringsUseCase
from app.use_cases.catalog.prepare_string_values import PrepareStringValuesUseCase
from app.use_cases.catalog.update_inventory_string import UpdateInventoryStringUseCase
from app.use_cases.catalog.update_string import UpdateStringUseCase
from app.use_cases.recommendation.list_recommendation_logs import (
    ListRecommendationLogsUseCase,
)
from app.use_cases.store.confirm_checkin import ConfirmCheckInUseCase
from app.use_cases.store.get_business_hours import GetBusinessHoursUseCase
from app.use_cases.store.get_queue import GetQueueUseCase
from app.use_cases.store.get_store_analytics import GetStoreAnalyticsUseCase
from app.use_cases.store.get_store_settings import GetStoreSettingsUseCase
from app.use_cases.store.list_slots import ListSlotsUseCase
from app.use_cases.store.lookup_checkin import LookupCheckInUseCase
from app.use_cases.store.update_business_hours import UpdateBusinessHoursUseCase
from app.use_cases.store.update_store_settings import UpdateStoreSettingsUseCase


router = APIRouter(prefix="/admin", tags=["admin"])

BookingPhotoType = Literal["racket", "service_progress", "other"]


async def save_update_photo_upload(
    photo: UploadFile,
) -> tuple[str, str | None, str | None]:
    photo_content_type = photo.content_type
    photo_original_name = photo.filename
    photo_path = save_booking_update_photo(
        content=await photo.read(),
        content_type=photo.content_type,
        original_name=photo.filename,
    )
    return photo_path, photo_original_name, photo_content_type


@router.get("/strings", response_model=dict)
def admin_list_strings(
    search: str | None = Query(default=None, max_length=100),
    brand: str | None = Query(default=None, max_length=100),
    is_active: bool | None = Query(default=None),
    sort_by: str = Query(default="updated_at"),
    sort_order: str = Query(default="desc"),
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: CurrentUser = Depends(get_current_admin),
    catalog_repository=Depends(get_catalog_repository),
) -> dict[str, object]:
    page = ListStringsUseCase(catalog_repository=catalog_repository).execute(
        is_active=is_active,
        brand=brand,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )
    return page_to_dict(page, lambda item: string_to_dto(item).model_dump())


@router.post("/strings", response_model=StringOut)
def admin_create_string(
    payload: StringWritePayload,
    _: CurrentUser = Depends(get_current_admin),
    catalog_repository=Depends(get_catalog_repository),
) -> StringOut:
    values = PrepareStringValuesUseCase(
        approved_strings_path=get_settings().approved_strings_path
    ).execute(
        brand=payload.brand,
        model_name=payload.model_name,
        overrides=payload.model_dump(exclude_none=True),
    )
    item = CreateStringUseCase(catalog_repository=catalog_repository).execute(values)
    return string_to_dto(item)


@router.put("/strings/{string_id}", response_model=StringOut)
def admin_update_string(
    string_id: str,
    payload: StringWritePayload,
    _: CurrentUser = Depends(get_current_admin),
    catalog_repository=Depends(get_catalog_repository),
) -> StringOut:
    values = PrepareStringValuesUseCase(
        approved_strings_path=get_settings().approved_strings_path
    ).execute(
        brand=payload.brand,
        model_name=payload.model_name,
        overrides=payload.model_dump(exclude_none=True),
    )
    item = UpdateStringUseCase(catalog_repository=catalog_repository).execute(
        string_id=string_id,
        values=values,
    )
    return string_to_dto(item)


@router.delete("/strings/{string_id}", response_model=StringOut)
def admin_deactivate_string(
    string_id: str,
    _: CurrentUser = Depends(get_current_admin),
    catalog_repository=Depends(get_catalog_repository),
) -> StringOut:
    item = DeactivateStringUseCase(catalog_repository=catalog_repository).execute(
        string_id
    )
    return string_to_dto(item)


@router.get("/inventory/strings", response_model=dict)
def admin_inventory_strings(
    search: str | None = Query(default=None, max_length=100),
    brand: str | None = Query(default=None, max_length=100),
    availability: Literal["in_stock", "low_stock", "out_of_stock"] | None = Query(
        default=None
    ),
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: CurrentUser = Depends(get_current_admin),
    catalog_repository=Depends(get_catalog_repository),
) -> dict[str, object]:
    page = ListInventoryStringsUseCase(catalog_repository=catalog_repository).execute(
        brand=brand,
        search=search,
        availability=availability,
        limit=limit,
        offset=offset,
    )
    return page_to_dict(page, lambda item: inventory_string_to_dto(item).model_dump())


@router.get("/inventory/strings/{string_id}", response_model=AdminInventoryStringOut)
def admin_inventory_string_detail(
    string_id: str,
    _: CurrentUser = Depends(get_current_admin),
    catalog_repository=Depends(get_catalog_repository),
) -> AdminInventoryStringOut:
    item = GetStringUseCase(catalog_repository=catalog_repository).execute(
        string_id=string_id,
        include_inactive=True,
    )
    return inventory_string_to_dto(item)


@router.patch("/inventory/strings/{string_id}", response_model=AdminInventoryStringOut)
def admin_update_inventory_string(
    string_id: str,
    payload: InventoryUpdatePayload,
    _: CurrentUser = Depends(get_current_admin),
    catalog_repository=Depends(get_catalog_repository),
) -> AdminInventoryStringOut:
    values: dict[str, object] = {}
    if "price_rm" in payload.model_fields_set:
        values["price_rm"] = payload.price_rm
    if "stock_level" in payload.model_fields_set:
        stock_level = payload.stock_level or 0
        values["stock_level"] = stock_level
        values["is_active"] = stock_level > 0
    if "admin_note" in payload.model_fields_set:
        values["admin_note"] = (
            payload.admin_note.strip() if payload.admin_note else None
        )
    item = UpdateInventoryStringUseCase(catalog_repository=catalog_repository).execute(
        string_id=string_id,
        values=values,
    )
    return inventory_string_to_dto(item)


@router.get("/bookings", response_model=dict)
def admin_bookings(
    status: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=100),
    sort_by: str = Query(default="updated_at"),
    sort_order: str = Query(default="desc"),
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: CurrentUser = Depends(get_current_admin),
    booking_repository=Depends(get_booking_repository),
) -> dict[str, object]:
    page = ListAdminBookingsUseCase(booking_repository=booking_repository).execute(
        status=status,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )
    return page_to_dict(
        page,
        lambda item: booking_to_dto(
            item, include_user=True, include_history=True
        ).model_dump(),
    )


@router.get("/bookings/{booking_id}", response_model=BookingOut)
def admin_get_booking(
    booking_id: str,
    _: CurrentUser = Depends(get_current_admin),
    booking_repository=Depends(get_booking_repository),
) -> BookingOut:
    booking = GetBookingUseCase(booking_repository=booking_repository).execute(
        booking_id
    )
    return booking_to_dto(booking, include_user=True, include_history=True)


@router.patch("/bookings/{booking_id}/status", response_model=BookingOut)
def admin_update_booking_status(
    booking_id: str,
    payload: UpdateBookingStatusPayload,
    current_user: CurrentUser = Depends(get_current_admin),
    booking_repository=Depends(get_booking_repository),
) -> BookingOut:
    booking = UpdateBookingStatusUseCase(booking_repository=booking_repository).execute(
        booking_id=booking_id,
        next_status=payload.status,
        changed_by_user_id=current_user.user_id,
        note=payload.note,
    )
    return booking_to_dto(booking, include_user=True, include_history=True)


@router.post("/bookings/{booking_id}/updates", response_model=BookingOut)
async def admin_add_booking_update(
    booking_id: str,
    comment: str | None = Form(default=None),
    photo: UploadFile | None = File(default=None),
    photo_type: BookingPhotoType = Form(default="other"),
    current_user: CurrentUser = Depends(get_current_admin),
    booking_repository=Depends(get_booking_repository),
) -> BookingOut:
    photo_path = None
    photo_original_name = None
    photo_content_type = None
    if photo is not None:
        (
            photo_path,
            photo_original_name,
            photo_content_type,
        ) = await save_update_photo_upload(photo)

    booking = AddBookingUpdateUseCase(booking_repository=booking_repository).execute(
        booking_id=booking_id,
        author_user_id=current_user.user_id,
        author_role=current_user.role,
        comment=comment,
        photo_path=photo_path,
        photo_original_name=photo_original_name,
        photo_content_type=photo_content_type,
        photo_type=photo_type if photo_path else None,
    )
    return booking_to_dto(booking, include_user=True, include_history=True)


@router.post("/bookings/{booking_id}/photos", response_model=BookingOut)
async def admin_upload_booking_photo(
    booking_id: str,
    photo: UploadFile = File(...),
    comment: str | None = Form(default=None),
    photo_type: BookingPhotoType = Form(default="racket"),
    current_user: CurrentUser = Depends(get_current_admin),
    booking_repository=Depends(get_booking_repository),
) -> BookingOut:
    (
        photo_path,
        photo_original_name,
        photo_content_type,
    ) = await save_update_photo_upload(photo)
    booking = AddBookingUpdateUseCase(booking_repository=booking_repository).execute(
        booking_id=booking_id,
        author_user_id=current_user.user_id,
        author_role=current_user.role,
        comment=comment,
        photo_path=photo_path,
        photo_original_name=photo_original_name,
        photo_content_type=photo_content_type,
        photo_type=photo_type,
    )
    return booking_to_dto(booking, include_user=True, include_history=True)


@router.get("/recommendations/logs", response_model=dict)
def admin_recommendation_logs(
    phone_number: str | None = Query(default=None, max_length=30),
    algorithm_version: str | None = Query(default=None, max_length=80),
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: CurrentUser = Depends(get_current_admin),
    recommendation_log_repository=Depends(get_recommendation_log_repository),
) -> dict[str, object]:
    page = ListRecommendationLogsUseCase(
        recommendation_log_repository=recommendation_log_repository
    ).execute(
        phone_number=phone_number,
        algorithm_version=algorithm_version,
        limit=limit,
        offset=offset,
    )
    return page_to_dict(page, recommendation_log_to_dict)


@router.get("/business-hours", response_model=StoreBusinessHoursOut)
def admin_get_business_hours(
    _: CurrentUser = Depends(get_current_admin),
    store_repository=Depends(get_store_repository),
) -> StoreBusinessHoursOut:
    hours = GetBusinessHoursUseCase(store_repository=store_repository).execute()
    return business_hours_to_dto(hours)


@router.put("/business-hours", response_model=StoreBusinessHoursOut)
def admin_update_business_hours(
    payload: StoreBusinessHoursPayload,
    _: CurrentUser = Depends(get_current_admin),
    store_repository=Depends(get_store_repository),
) -> StoreBusinessHoursOut:
    hours = UpdateBusinessHoursUseCase(store_repository=store_repository).execute(
        days=[day.model_dump() for day in payload.days],
        special_closed_dates=payload.special_closed_dates,
    )
    return business_hours_to_dto(hours)


@router.get("/slots", response_model=dict)
def admin_list_slots(
    date_value: date | None = Query(default=None, alias="date"),
    date_from: date | None = Query(default=None),
    days: int = Query(default=7, ge=1, le=31),
    _: CurrentUser = Depends(get_current_admin),
    store_repository=Depends(get_store_repository),
    booking_repository=Depends(get_booking_repository),
    clock=Depends(get_clock),
) -> dict[str, object]:
    page = ListSlotsUseCase(
        store_repository=store_repository,
        booking_repository=booking_repository,
        clock=clock,
    ).execute(date_value=date_value, date_from=date_from, days=days)
    return page_to_dict(page, lambda item: slot_to_dto(item).model_dump())


@router.get("/check-in/lookup", response_model=CheckInLookupOut)
def admin_lookup_check_in(
    reference: str = Query(min_length=1, max_length=120),
    _: CurrentUser = Depends(get_current_admin),
    booking_repository=Depends(get_booking_repository),
) -> CheckInLookupOut:
    lookup = LookupCheckInUseCase(booking_repository=booking_repository).execute(
        booking_id=None,
        reference=reference,
    )
    return CheckInLookupOut(
        matched_by=cast(Literal["booking_id", "check_in_reference"], lookup.matched_by),
        booking=booking_to_dto(
            lookup.booking,
            include_user=True,
            include_history=True,
        ).model_dump(),
    )


@router.post("/check-in", response_model=BookingOut)
def admin_check_in_booking(
    payload: CheckInPayload,
    current_user: CurrentUser = Depends(get_current_admin),
    booking_repository=Depends(get_booking_repository),
) -> BookingOut:
    lookup_use_case = LookupCheckInUseCase(booking_repository=booking_repository)
    booking = ConfirmCheckInUseCase(
        booking_repository=booking_repository,
        lookup_check_in_use_case=lookup_use_case,
    ).execute(
        booking_id=payload.booking_id,
        reference=payload.reference,
        admin_user_id=current_user.user_id,
        note=payload.note,
    )
    return booking_to_dto(booking, include_user=True, include_history=True)


@router.get("/service-queue", response_model=ServiceQueueOut)
def admin_service_queue(
    _: CurrentUser = Depends(get_current_admin),
    booking_repository=Depends(get_booking_repository),
) -> ServiceQueueOut:
    queue = GetQueueUseCase(booking_repository=booking_repository).execute()
    return ServiceQueueOut(
        generated_at=queue.generated_at,
        lanes=[
            ServiceQueueLaneOut(
                status=lane.status,
                title=lane.title,
                items=[
                    ServiceQueueItemOut(
                        queue_position=item.queue_position,
                        booking=booking_to_dto(
                            item.booking,
                            include_user=True,
                            include_history=True,
                        ).model_dump(),
                    )
                    for item in lane.items
                ],
            )
            for lane in queue.lanes
        ],
    )


@router.get("/store-settings", response_model=StoreSettingsOut)
def admin_get_store_settings(
    _: CurrentUser = Depends(get_current_admin),
    store_repository=Depends(get_store_repository),
) -> StoreSettingsOut:
    settings = GetStoreSettingsUseCase(store_repository=store_repository).execute()
    return settings_to_dto(settings)


@router.put("/store-settings", response_model=StoreSettingsOut)
def admin_update_store_settings(
    payload: StoreSettingsPayload,
    _: CurrentUser = Depends(get_current_admin),
    store_repository=Depends(get_store_repository),
) -> StoreSettingsOut:
    settings = UpdateStoreSettingsUseCase(store_repository=store_repository).execute(
        payload.model_dump()
    )
    return settings_to_dto(settings)


@router.get("/analytics/summary", response_model=AnalyticsSummaryOut)
def admin_analytics_summary(
    _: CurrentUser = Depends(get_current_admin),
    booking_repository=Depends(get_booking_repository),
    catalog_repository=Depends(get_catalog_repository),
    clock=Depends(get_clock),
) -> AnalyticsSummaryOut:
    summary = GetStoreAnalyticsUseCase(
        booking_repository=booking_repository,
        catalog_repository=catalog_repository,
        clock=clock,
    ).execute_summary()
    return analytics_summary_to_dto(summary)


@router.get("/analytics/popular-strings", response_model=list[PopularStringOut])
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
