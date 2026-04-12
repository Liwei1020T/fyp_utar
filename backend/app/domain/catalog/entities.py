from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


ASPECT_FEATURE_KEYS = {
    "attack",
    "comfort",
    "control",
    "durability",
    "elasticity",
    "sound",
    "string_movement",
    "tension_retention",
    "value_for_money",
    "beginner_fit_score",
    "stability_score",
    "all_round_score",
}


@dataclass(frozen=True)
class StringTag:
    tag_key: str
    tag_label: str
    tag_count: int


@dataclass(frozen=True)
class StringOfficialPerformance:
    catalog_id: str
    source_type: str | None
    source_name: str | None
    source_url: str | None
    source_region: str | None
    category: float | None
    feature: float | None
    feel: float | None
    repulsion_power: float | None
    durability: float | None
    hitting_sound: float | None
    shock_absorption: float | None
    control: float | None
    notes: str | None
    status: str
    updated_at: datetime | None


@dataclass(frozen=True)
class InventorySnapshot:
    inventory_id: str
    current_stock: int
    reserved_stock: int
    available_stock: int
    reorder_level: int
    reorder_quantity: int
    cost_price: float | None
    selling_price: float | None
    is_active: bool
    latest_note: str | None
    updated_at: datetime | None


@dataclass(frozen=True)
class InventoryMovementRecord:
    movement_id: str
    inventory_id: str
    movement_type: str
    quantity: int
    reference_type: str | None
    reference_id: str | None
    note: str | None
    created_at: datetime | None


@dataclass(frozen=True)
class StringItem:
    id: str
    brand: str
    brand_code: str
    display_name: str
    model_name: str
    normalized_name: str
    series_key: str | None
    series_label: str | None
    is_hybrid: bool
    gauge_main_mm: float | None
    gauge_cross_mm: float | None
    gauge_label: str | None
    material_summary_en: str | None
    color_options_en: list[str]
    short_description: str
    full_description: str
    official_performance_status: str
    source_dataset_url: str | None
    source_language: str | None
    original_name: str | None
    original_brand_label: str | None
    original_series: str | None
    original_material: str | None
    original_color: str | None
    community_rating: float | None
    want_count: int
    used_count: int
    review_count: int
    tags: list[StringTag]
    official_performance: StringOfficialPerformance | None
    inventory: InventorySnapshot | None
    aspect_scores: dict[str, float]
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None

    @property
    def price_rm(self) -> float | None:
        return self.inventory.selling_price if self.inventory else None

    @property
    def source_item_id(self) -> str | None:
        return self.original_name

    @property
    def source_url(self) -> str | None:
        return self.source_dataset_url

    @property
    def stock_level(self) -> int:
        if self.inventory is None:
            return 0
        return self.inventory.available_stock

    @property
    def current_stock(self) -> int:
        if self.inventory is None:
            return 0
        return self.inventory.current_stock

    @property
    def reserved_stock(self) -> int:
        if self.inventory is None:
            return 0
        return self.inventory.reserved_stock

    @property
    def available_stock(self) -> int:
        if self.inventory is None:
            return 0
        return self.inventory.available_stock

    @property
    def reorder_level(self) -> int:
        if self.inventory is None:
            return 0
        return self.inventory.reorder_level

    @property
    def reorder_quantity(self) -> int:
        if self.inventory is None:
            return 0
        return self.inventory.reorder_quantity

    @property
    def cost_price(self) -> float | None:
        return self.inventory.cost_price if self.inventory else None

    @property
    def selling_price(self) -> float | None:
        return self.inventory.selling_price if self.inventory else None

    @property
    def admin_note(self) -> str | None:
        if self.inventory is None:
            return None
        return self.inventory.latest_note

    def aspect_score(self, feature_key: str, default: float = 0.5) -> float:
        return self.aspect_scores.get(feature_key, default)

    @property
    def attack(self) -> float:
        return self.aspect_score("attack")

    @property
    def comfort(self) -> float:
        return self.aspect_score("comfort")

    @property
    def control(self) -> float:
        return self.aspect_score("control")

    @property
    def durability(self) -> float:
        return self.aspect_score("durability")

    @property
    def elasticity(self) -> float:
        return self.aspect_score("elasticity")

    @property
    def sound(self) -> float:
        return self.aspect_score("sound")

    @property
    def string_movement(self) -> float:
        return self.aspect_score("string_movement")

    @property
    def tension_retention(self) -> float:
        return self.aspect_score("tension_retention")

    @property
    def value_for_money(self) -> float:
        return self.aspect_score("value_for_money")

    @property
    def beginner_fit_score(self) -> float:
        return self.aspect_score("beginner_fit_score")

    @property
    def stability_score(self) -> float:
        return self.aspect_score("stability_score")

    @property
    def all_round_score(self) -> float:
        return self.aspect_score("all_round_score")
