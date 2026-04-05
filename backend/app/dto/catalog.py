from __future__ import annotations

from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from app.domain.catalog.entities import StringItem
from app.domain.catalog.policies import inventory_availability
from app.shared.serialization import isoformat_or_none


InventoryAvailability = Literal["in_stock", "low_stock", "out_of_stock"]


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


class AdminInventoryStringOut(StringOut):
    stock_level: int
    availability: InventoryAvailability
    admin_note: str | None = None


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


class InventoryUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    price_rm: float | None = Field(default=None, ge=0, le=999)
    stock_level: int | None = Field(default=None, ge=0, le=9999)
    admin_note: str | None = Field(default=None, max_length=500)


def string_to_dto(item: StringItem) -> StringOut:
    return StringOut(
        id=item.id,
        brand=item.brand,
        model_name=item.model_name,
        normalized_name=item.normalized_name,
        price_rm=item.price_rm,
        attack=item.attack,
        comfort=item.comfort,
        control=item.control,
        durability=item.durability,
        elasticity=item.elasticity,
        sound=item.sound,
        string_movement=item.string_movement,
        tension_retention=item.tension_retention,
        value_for_money=item.value_for_money,
        beginner_fit_score=item.beginner_fit_score,
        stability_score=item.stability_score,
        all_round_score=item.all_round_score,
        source_item_id=item.source_item_id,
        source_url=item.source_url,
        is_active=item.is_active,
        created_at=isoformat_or_none(item.created_at),
        updated_at=isoformat_or_none(item.updated_at),
    )


def inventory_string_to_dto(item: StringItem) -> AdminInventoryStringOut:
    base = string_to_dto(item)
    return AdminInventoryStringOut(
        **base.model_dump(),
        stock_level=item.stock_level,
        availability=inventory_availability(item),
        admin_note=item.admin_note,
    )

