from __future__ import annotations

from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator

from app.domain.catalog.entities import InventoryMovementRecord
from app.domain.catalog.entities import RecommendationMatrixEntryRecord
from app.domain.catalog.entities import RecommendationMatrixImportReport
from app.domain.catalog.entities import RecommendationMatrixInspectionRecord
from app.domain.catalog.entities import StringItem
from app.domain.catalog.entities import StringOfficialPerformance
from app.domain.catalog.policies import inventory_availability
from app.shared.serialization import isoformat_or_none
from app.shared.upload_storage import build_signed_media_url


InventoryAvailability = Literal["in_stock", "low_stock", "out_of_stock"]
PricingMode = Literal["fixed_price", "quoted_at_shop", "price_pending"]


class CatalogTagOut(BaseModel):
    tag_key: str
    tag_label: str
    tag_count: int


class StringOut(BaseModel):
    id: str
    brand: str
    brand_code: str
    display_name: str
    model_name: str
    normalized_name: str
    price_rm: float | None = None
    available_stock: int
    availability_status: InventoryAvailability
    attack: float
    comfort: float
    control: float
    durability: float
    elasticity: float
    sound: float
    string_movement: float
    tension_retention: float
    value_for_money: float
    attacking_fit_score: float
    control_fit_score: float
    beginner_fit_score: float
    stability_score: float
    all_round_score: float
    series_key: str | None = None
    series_label: str | None = None
    is_hybrid: bool
    gauge_main_mm: float | None = None
    gauge_cross_mm: float | None = None
    gauge_label: str | None = None
    category: str | None = None
    main_trait: str | None = None
    tension_min_lbs: int | None = None
    tension_max_lbs: int | None = None
    material_summary_en: str | None = None
    image_url: str | None = None
    color_options_en: list[str] = Field(default_factory=list)
    short_description: str
    full_description: str
    official_performance_status: str
    source_item_id: str | None = None
    source_url: str | None = None
    source_language: str | None = None
    original_name: str | None = None
    original_brand_label: str | None = None
    original_series: str | None = None
    original_material: str | None = None
    original_color: str | None = None
    community_rating: float | None = None
    want_count: int
    used_count: int
    review_count: int
    tags: list[CatalogTagOut] = Field(default_factory=list)
    aspect_scores: dict[str, float] = Field(default_factory=dict)
    is_active: bool
    created_at: str | None = None
    updated_at: str | None = None


class AdminInventoryStringOut(StringOut):
    stock_level: int
    current_stock: int
    reserved_stock: int
    available_stock: int
    reorder_level: int
    reorder_quantity: int
    cost_price: float | None = None
    selling_price: float | None = None
    pricing_mode: PricingMode
    availability_status: InventoryAvailability
    availability: InventoryAvailability
    admin_note: str | None = None


class OfficialPerformanceOut(BaseModel):
    catalog_id: str
    source_type: str | None = None
    source_name: str | None = None
    source_region: str | None = None
    category: float | None = None
    feature: float | None = None
    feel: float | None = None
    repulsion_power: float | None = None
    durability: float | None = None
    hitting_sound: float | None = None
    shock_absorption: float | None = None
    control: float | None = None
    notes: str | None = None
    status: str
    updated_at: str | None = None


class InventoryMovementOut(BaseModel):
    movement_id: str
    inventory_id: str
    movement_type: str
    quantity: int
    reference_type: str | None = None
    reference_id: str | None = None
    note: str | None = None
    created_at: str | None = None


class RecommendationMatrixEntryOut(BaseModel):
    catalog_id: str
    feature_key: str
    feature_label: str | None = None
    feature_group: str | None = None
    source_layer: str
    raw_value: float | None = None
    normalized_score: float | None = None
    evidence_note: str | None = None
    updated_at: str | None = None


class RecommendationMatrixInspectionOut(BaseModel):
    catalog_id: str
    display_name: str
    effective_scores: dict[str, float] = Field(default_factory=dict)
    official_performance: OfficialPerformanceOut | None = None
    matrix_by_source: dict[str, list[RecommendationMatrixEntryOut]] = Field(
        default_factory=dict
    )


class RecommendationMatrixImportReportOut(BaseModel):
    csv_path: str
    source_layer: str
    total_csv_rows: int
    matched_strings: int
    unmatched_strings: int
    inserted_entries: int
    updated_entries: int
    unchanged_entries: int
    matched_by: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class StringWritePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brand: str = Field(min_length=1, max_length=120)
    model_name: str = Field(min_length=1, max_length=120)
    price_rm: float | None = Field(default=None, ge=0, le=999)
    display_name: str | None = Field(default=None, min_length=1, max_length=160)
    series_key: str | None = Field(default=None, max_length=80)
    series_label: str | None = Field(default=None, max_length=120)
    is_hybrid: bool | None = None
    gauge_main_mm: float | None = Field(default=None, ge=0.4, le=1.2)
    gauge_cross_mm: float | None = Field(default=None, ge=0.4, le=1.2)
    gauge_label: str | None = Field(default=None, max_length=80)
    category: str | None = Field(default=None, max_length=40)
    main_trait: str | None = Field(default=None, max_length=120)
    tension_min_lbs: int | None = Field(default=None, ge=15, le=40)
    tension_max_lbs: int | None = Field(default=None, ge=15, le=40)
    material_summary_en: str | None = Field(default=None, max_length=2000)
    image_url: str | None = Field(default=None, max_length=2000)
    color_options_en: list[str] | None = None
    short_description: str | None = Field(default=None, max_length=1000)
    full_description: str | None = Field(default=None, max_length=4000)
    source_language: str | None = Field(default=None, max_length=32)
    original_name: str | None = Field(default=None, max_length=160)
    original_brand_label: str | None = Field(default=None, max_length=160)
    original_series: str | None = Field(default=None, max_length=160)
    original_material: str | None = Field(default=None, max_length=4000)
    original_color: str | None = Field(default=None, max_length=4000)
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_tension_range(self) -> "StringWritePayload":
        if (
            self.tension_min_lbs is not None
            and self.tension_max_lbs is not None
            and self.tension_max_lbs < self.tension_min_lbs
        ):
            raise ValueError(
                "tension_max_lbs must be greater than or equal to tension_min_lbs"
            )
        return self


class InventoryUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    price_rm: float | None = Field(default=None, ge=0, le=999)
    stock_level: int | None = Field(default=None, ge=0, le=9999)
    current_stock: int | None = Field(default=None, ge=0, le=9999)
    reserved_stock: int | None = Field(default=None, ge=0, le=9999)
    reorder_level: int | None = Field(default=None, ge=0, le=9999)
    reorder_quantity: int | None = Field(default=None, ge=0, le=9999)
    cost_price: float | None = Field(default=None, ge=0, le=999)
    selling_price: float | None = Field(default=None, ge=0, le=999)
    pricing_mode: PricingMode | None = None
    availability_status: InventoryAvailability | None = None
    is_active: bool | None = None
    admin_note: str | None = Field(default=None, max_length=500)
    movement_type: str | None = Field(default=None, max_length=40)
    reference_type: str | None = Field(default=None, max_length=60)
    reference_id: str | None = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def validate_pricing_mode(self) -> "InventoryUpdatePayload":
        price_value = (
            self.selling_price if self.selling_price is not None else self.price_rm
        )
        if self.pricing_mode == "fixed_price" and price_value is None:
            raise ValueError("fixed_price mode requires price_rm or selling_price")
        if (
            self.pricing_mode in {"quoted_at_shop", "price_pending"}
            and price_value is not None
        ):
            raise ValueError(
                "quoted_at_shop and price_pending modes require a null price value"
            )
        return self


class OfficialPerformancePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: str | None = Field(default=None, max_length=40)
    source_name: str | None = Field(default=None, max_length=160)
    source_region: str | None = Field(default=None, max_length=60)
    category: float | None = Field(default=None, ge=0, le=10)
    feature: float | None = Field(default=None, ge=0, le=10)
    feel: float | None = Field(default=None, ge=0, le=10)
    repulsion_power: float | None = Field(default=None, ge=0, le=10)
    durability: float | None = Field(default=None, ge=0, le=10)
    hitting_sound: float | None = Field(default=None, ge=0, le=10)
    shock_absorption: float | None = Field(default=None, ge=0, le=10)
    control: float | None = Field(default=None, ge=0, le=10)
    notes: str | None = Field(default=None, max_length=4000)
    status: str | None = Field(default=None, max_length=40)


class StringEditorUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    catalog: StringWritePayload | None = None
    inventory: InventoryUpdatePayload | None = None
    official_performance: OfficialPerformancePayload | None = None

    @model_validator(mode="after")
    def validate_at_least_one_section(self) -> "StringEditorUpdatePayload":
        if not any(
            section is not None
            for section in (
                self.catalog,
                self.inventory,
                self.official_performance,
            )
        ):
            raise ValueError("At least one editor section must be provided")
        return self


def string_to_dto(item: StringItem) -> StringOut:
    return StringOut(
        id=item.id,
        brand=item.brand,
        brand_code=item.brand_code,
        display_name=item.display_name,
        model_name=item.model_name,
        normalized_name=item.normalized_name,
        price_rm=item.price_rm,
        available_stock=item.available_stock,
        availability_status=(
            item.inventory.availability_status
            if item.inventory
            else inventory_availability(item)
        ),
        attack=item.attack,
        comfort=item.comfort,
        control=item.control,
        durability=item.durability,
        elasticity=item.elasticity,
        sound=item.sound,
        string_movement=item.string_movement,
        tension_retention=item.tension_retention,
        value_for_money=item.value_for_money,
        attacking_fit_score=item.attacking_fit_score,
        control_fit_score=item.control_fit_score,
        beginner_fit_score=item.beginner_fit_score,
        stability_score=item.stability_score,
        all_round_score=item.all_round_score,
        series_key=item.series_key,
        series_label=item.series_label,
        is_hybrid=item.is_hybrid,
        gauge_main_mm=item.gauge_main_mm,
        gauge_cross_mm=item.gauge_cross_mm,
        gauge_label=item.gauge_label,
        category=item.category,
        main_trait=item.main_trait,
        tension_min_lbs=item.tension_min_lbs,
        tension_max_lbs=item.tension_max_lbs,
        material_summary_en=item.material_summary_en,
        image_url=(build_signed_media_url(item.image_url) if item.image_url else None),
        color_options_en=item.color_options_en,
        short_description=item.short_description,
        full_description=item.full_description,
        official_performance_status=item.official_performance_status,
        source_item_id=item.source_item_id,
        source_url=item.source_url,
        source_language=item.source_language,
        original_name=item.original_name,
        original_brand_label=item.original_brand_label,
        original_series=item.original_series,
        original_material=item.original_material,
        original_color=item.original_color,
        community_rating=item.community_rating,
        want_count=item.want_count,
        used_count=item.used_count,
        review_count=item.review_count,
        tags=[
            CatalogTagOut(
                tag_key=tag.tag_key,
                tag_label=tag.tag_label,
                tag_count=tag.tag_count,
            )
            for tag in item.tags
        ],
        aspect_scores=item.aspect_scores,
        is_active=item.is_active,
        created_at=isoformat_or_none(item.created_at),
        updated_at=isoformat_or_none(item.updated_at),
    )


def inventory_string_to_dto(item: StringItem) -> AdminInventoryStringOut:
    base = string_to_dto(item)
    return AdminInventoryStringOut(
        **base.model_dump(),
        stock_level=item.stock_level,
        current_stock=item.current_stock,
        reserved_stock=item.reserved_stock,
        reorder_level=item.reorder_level,
        reorder_quantity=item.reorder_quantity,
        cost_price=item.cost_price,
        selling_price=item.selling_price,
        pricing_mode=item.inventory.pricing_mode if item.inventory else "price_pending",
        availability=inventory_availability(item),
        admin_note=item.admin_note,
    )


def official_performance_to_dto(
    item: StringOfficialPerformance,
) -> OfficialPerformanceOut:
    return OfficialPerformanceOut(
        catalog_id=item.catalog_id,
        source_type=item.source_type,
        source_name=item.source_name,
        source_region=item.source_region,
        category=item.category,
        feature=item.feature,
        feel=item.feel,
        repulsion_power=item.repulsion_power,
        durability=item.durability,
        hitting_sound=item.hitting_sound,
        shock_absorption=item.shock_absorption,
        control=item.control,
        notes=item.notes,
        status=item.status,
        updated_at=isoformat_or_none(item.updated_at),
    )


def inventory_movement_to_dto(item: InventoryMovementRecord) -> InventoryMovementOut:
    return InventoryMovementOut(
        movement_id=item.movement_id,
        inventory_id=item.inventory_id,
        movement_type=item.movement_type,
        quantity=item.quantity,
        reference_type=item.reference_type,
        reference_id=item.reference_id,
        note=item.note,
        created_at=isoformat_or_none(item.created_at),
    )


def recommendation_matrix_entry_to_dto(
    item: RecommendationMatrixEntryRecord,
) -> RecommendationMatrixEntryOut:
    return RecommendationMatrixEntryOut(
        catalog_id=item.catalog_id,
        feature_key=item.feature_key,
        feature_label=item.feature_label,
        feature_group=item.feature_group,
        source_layer=item.source_layer,
        raw_value=item.raw_value,
        normalized_score=item.normalized_score,
        evidence_note=item.evidence_note,
        updated_at=isoformat_or_none(item.updated_at),
    )


def recommendation_matrix_inspection_to_dto(
    item: RecommendationMatrixInspectionRecord,
) -> RecommendationMatrixInspectionOut:
    grouped: dict[str, list[RecommendationMatrixEntryOut]] = {}
    for entry in item.matrix_entries:
        grouped.setdefault(entry.source_layer, []).append(
            recommendation_matrix_entry_to_dto(entry)
        )

    return RecommendationMatrixInspectionOut(
        catalog_id=item.catalog_id,
        display_name=item.display_name,
        effective_scores=item.effective_scores,
        official_performance=official_performance_to_dto(item.official_performance)
        if item.official_performance
        else None,
        matrix_by_source=grouped,
    )


def recommendation_matrix_import_report_to_dto(
    item: RecommendationMatrixImportReport,
) -> RecommendationMatrixImportReportOut:
    return RecommendationMatrixImportReportOut(
        csv_path=item.csv_path,
        source_layer=item.source_layer,
        total_csv_rows=item.total_csv_rows,
        matched_strings=item.matched_strings,
        unmatched_strings=item.unmatched_strings,
        inserted_entries=item.inserted_entries,
        updated_entries=item.updated_entries,
        unchanged_entries=item.unchanged_entries,
        matched_by=item.matched_by,
        warnings=item.warnings,
    )
