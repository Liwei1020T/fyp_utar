from __future__ import annotations

from datetime import date

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query

from app.dto.common import page_to_dict
from app.dto.store import StoreSettingsOut
from app.dto.store import settings_to_dto
from app.dto.store import slot_to_dto
from app.entrypoints.api.dependencies import get_booking_repository
from app.entrypoints.api.dependencies import get_clock
from app.entrypoints.api.dependencies import get_current_customer
from app.entrypoints.api.dependencies import get_store_repository
from app.use_cases.store.get_store_settings import GetStoreSettingsUseCase
from app.use_cases.store.list_slots import ListSlotsUseCase


router = APIRouter(tags=["store"])


@router.get("/store-settings", response_model=StoreSettingsOut)
def public_get_store_settings(
    _: object = Depends(get_current_customer),
    store_repository=Depends(get_store_repository),
) -> StoreSettingsOut:
    settings = GetStoreSettingsUseCase(store_repository=store_repository).execute()
    return settings_to_dto(settings)


@router.get("/slots", response_model=dict)
def public_list_slots(
    date_value: date | None = Query(default=None, alias="date"),
    date_from: date | None = Query(default=None),
    days: int = Query(default=7, ge=1, le=31),
    _: object = Depends(get_current_customer),
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
