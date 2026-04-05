from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query

from app.dto.catalog import StringOut
from app.dto.catalog import string_to_dto
from app.dto.common import page_to_dict
from app.entrypoints.api.dependencies import get_catalog_repository
from app.entrypoints.api.dependencies import get_current_customer
from app.use_cases.catalog.get_string import GetStringUseCase
from app.use_cases.catalog.list_strings import ListStringsUseCase


router = APIRouter(prefix="/strings", tags=["strings"])


@router.get("", response_model=dict)
def list_active_strings(
    search: str | None = Query(default=None, max_length=100),
    brand: str | None = Query(default=None, max_length=100),
    sort_by: str = Query(default="brand"),
    sort_order: str = Query(default="asc"),
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: object = Depends(get_current_customer),
    catalog_repository=Depends(get_catalog_repository),
) -> dict[str, object]:
    page = ListStringsUseCase(catalog_repository=catalog_repository).execute(
        is_active=True,
        brand=brand,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )
    return page_to_dict(page, lambda item: string_to_dto(item).model_dump())


@router.get("/{string_id}", response_model=StringOut)
def get_string(
    string_id: str,
    _: object = Depends(get_current_customer),
    catalog_repository=Depends(get_catalog_repository),
) -> StringOut:
    item = GetStringUseCase(catalog_repository=catalog_repository).execute(
        string_id=string_id
    )
    return string_to_dto(item)
