from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query

from app.dto.catalog import string_to_dto
from app.dto.common import page_to_dict
from app.entrypoints.api.dependencies import get_catalog_repository
from app.entrypoints.api.dependencies import get_current_customer
from app.entrypoints.api.dependencies import get_recommendation_repository
from app.domain.recommendation.learning_signals import build_community_snapshot
from app.dto.recommendation import community_snapshot_to_dict
from app.use_cases.catalog.list_strings import ListStringsUseCase


router = APIRouter(prefix="/strings", tags=["strings"])


@router.get("", response_model=dict)
def list_active_strings(
    search: str | None = Query(default=None, max_length=100),
    brand: str | None = Query(default=None, max_length=100),
    series: str | None = Query(default=None, max_length=100),
    gauge_min: float | None = Query(default=None, ge=0.4, le=1.2),
    gauge_max: float | None = Query(default=None, ge=0.4, le=1.2),
    is_hybrid: bool | None = Query(default=None),
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
        series=series,
        gauge_min=gauge_min,
        gauge_max=gauge_max,
        is_hybrid=is_hybrid,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )
    return page_to_dict(page, lambda item: string_to_dto(item).model_dump())


@router.get("/community-summary", response_model=dict)
def get_community_summary(
    _: object = Depends(get_current_customer),
    recommendation_repository=Depends(get_recommendation_repository),
) -> dict[str, object]:
    snapshot = build_community_snapshot(
        recommendation_repository.list_community_feedback_rows(),
        target_racket_model_key=None,
    )
    return community_snapshot_to_dict(snapshot, racket_model_key=None)
