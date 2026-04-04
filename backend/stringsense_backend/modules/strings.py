from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.orm import Session

from stringsense_backend.api.dependencies import get_current_customer
from stringsense_backend.core.config import get_settings
from stringsense_backend.core.errors import NotFoundError
from stringsense_backend.core.http import page_response
from stringsense_backend.core.serialization import decimal_to_float
from stringsense_backend.core.serialization import isoformat_or_none
from stringsense_backend.db.catalog_seed import merge_with_approved_defaults
from stringsense_backend.db.models import StringCatalogItem
from stringsense_backend.db.session import get_db


router = APIRouter(prefix="/strings", tags=["strings"])

SortField = Literal[
    "brand",
    "model_name",
    "price_rm",
    "attack",
    "comfort",
    "control",
    "durability",
    "elasticity",
    "sound",
    "tension_retention",
    "value_for_money",
    "created_at",
    "updated_at",
]
SortOrder = Literal["asc", "desc"]

STRING_SORT_FIELDS: dict[str, object] = {
    "brand": StringCatalogItem.brand,
    "model_name": StringCatalogItem.model_name,
    "price_rm": StringCatalogItem.price_rm,
    "attack": StringCatalogItem.attack,
    "comfort": StringCatalogItem.comfort,
    "control": StringCatalogItem.control,
    "durability": StringCatalogItem.durability,
    "elasticity": StringCatalogItem.elasticity,
    "sound": StringCatalogItem.sound,
    "tension_retention": StringCatalogItem.tension_retention,
    "value_for_money": StringCatalogItem.value_for_money,
    "created_at": StringCatalogItem.created_at,
    "updated_at": StringCatalogItem.updated_at,
}


class StringOut(BaseModel):
    id: str
    brand: str
    model_name: str
    normalized_name: str
    price_rm: float | None = None
    attack: float
    comfort: float
    control: float
    durability: float
    elasticity: float
    sound: float
    string_movement: float
    tension_retention: float
    value_for_money: float
    beginner_fit_score: float
    stability_score: float
    all_round_score: float
    source_item_id: str | None = None
    source_url: str | None = None
    is_active: bool
    created_at: str | None = None
    updated_at: str | None = None


class StringWritePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brand: str = Field(min_length=1, max_length=100)
    model_name: str = Field(min_length=1, max_length=100)
    price_rm: float | None = Field(default=None, ge=0, le=999)
    attack: float | None = Field(default=None, ge=0, le=1)
    comfort: float | None = Field(default=None, ge=0, le=1)
    control: float | None = Field(default=None, ge=0, le=1)
    durability: float | None = Field(default=None, ge=0, le=1)
    elasticity: float | None = Field(default=None, ge=0, le=1)
    sound: float | None = Field(default=None, ge=0, le=1)
    string_movement: float | None = Field(default=None, ge=0, le=1)
    tension_retention: float | None = Field(default=None, ge=0, le=1)
    value_for_money: float | None = Field(default=None, ge=0, le=1)
    beginner_fit_score: float | None = Field(default=None, ge=0, le=1)
    stability_score: float | None = Field(default=None, ge=0, le=1)
    all_round_score: float | None = Field(default=None, ge=0, le=1)
    source_item_id: str | None = None
    source_url: str | None = None
    is_active: bool | None = None


def serialize_string(item: StringCatalogItem) -> StringOut:
    return StringOut(
        id=item.id,
        brand=item.brand,
        model_name=item.model_name,
        normalized_name=item.normalized_name,
        price_rm=decimal_to_float(item.price_rm),
        attack=float(item.attack),
        comfort=float(item.comfort),
        control=float(item.control),
        durability=float(item.durability),
        elasticity=float(item.elasticity),
        sound=float(item.sound),
        string_movement=float(item.string_movement),
        tension_retention=float(item.tension_retention),
        value_for_money=float(item.value_for_money),
        beginner_fit_score=float(item.beginner_fit_score),
        stability_score=float(item.stability_score),
        all_round_score=float(item.all_round_score),
        source_item_id=item.source_item_id,
        source_url=item.source_url,
        is_active=item.is_active,
        created_at=isoformat_or_none(item.created_at),
        updated_at=isoformat_or_none(item.updated_at),
    )


def get_string_or_404(
    db: Session,
    string_id: str,
    *,
    include_inactive: bool = False,
) -> StringCatalogItem:
    item = db.execute(
        select(StringCatalogItem).where(StringCatalogItem.id == string_id)
    ).scalar_one_or_none()
    if item is None or (not include_inactive and not item.is_active):
        raise NotFoundError("String not found")
    return item


def list_strings(
    db: Session,
    *,
    is_active: bool | None,
    brand: str | None,
    search: str | None,
    sort_by: SortField,
    sort_order: SortOrder,
    limit: int | None,
    offset: int,
) -> dict[str, object]:
    query = select(StringCatalogItem)
    count_query = select(func.count()).select_from(StringCatalogItem)

    if is_active is not None:
        query = query.where(StringCatalogItem.is_active.is_(is_active))
        count_query = count_query.where(StringCatalogItem.is_active.is_(is_active))
    if brand:
        condition = StringCatalogItem.brand.ilike(f"%{brand.strip()}%")
        query = query.where(condition)
        count_query = count_query.where(condition)
    if search:
        term = f"%{search.strip()}%"
        condition = or_(
            StringCatalogItem.brand.ilike(term),
            StringCatalogItem.model_name.ilike(term),
            StringCatalogItem.normalized_name.ilike(term),
        )
        query = query.where(condition)
        count_query = count_query.where(condition)

    total = db.execute(count_query).scalar_one()
    sort_column = STRING_SORT_FIELDS[sort_by]
    if sort_order == "desc":
        query = query.order_by(sort_column.desc(), StringCatalogItem.model_name.asc())
    else:
        query = query.order_by(sort_column.asc(), StringCatalogItem.model_name.asc())

    if limit is not None:
        query = query.limit(limit).offset(offset)
    items = db.execute(query).scalars().all()
    return page_response(
        items=[serialize_string(item).model_dump() for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


def build_string_values(payload: StringWritePayload) -> dict[str, object]:
    settings = get_settings()
    return merge_with_approved_defaults(
        settings.approved_strings_path,
        brand=payload.brand,
        model_name=payload.model_name,
        overrides=payload.model_dump(exclude_none=True),
    )


@router.get("", response_model=dict)
def list_active_strings(
    search: str | None = Query(default=None, max_length=100),
    brand: str | None = Query(default=None, max_length=100),
    sort_by: SortField = Query(default="brand"),
    sort_order: SortOrder = Query(default="asc"),
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: object = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return list_strings(
        db,
        is_active=True,
        brand=brand,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )


@router.get("/{string_id}", response_model=StringOut)
def get_string(
    string_id: str,
    _: object = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> StringOut:
    return serialize_string(get_string_or_404(db, string_id))
