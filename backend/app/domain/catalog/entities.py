from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StringItem:
    id: str
    brand: str
    model_name: str
    normalized_name: str
    price_rm: float | None
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
    source_item_id: str | None
    source_url: str | None
    stock_level: int
    admin_note: str | None
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None

