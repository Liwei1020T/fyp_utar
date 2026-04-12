from __future__ import annotations

from collections.abc import Mapping
from collections.abc import Sequence
from typing import Any
from typing import cast

from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.adapters.persistence.sqlalchemy.recommendation_matrix_import import (
    import_recommendation_matrix_csv,
)
from app.adapters.persistence.sqlalchemy.models import InventoryMovement
from app.adapters.persistence.sqlalchemy.models import StringCatalogItem
from app.adapters.persistence.sqlalchemy.models import StringCatalogMetric
from app.adapters.persistence.sqlalchemy.models import StringCatalogTag
from app.adapters.persistence.sqlalchemy.models import StringInventoryItem
from app.adapters.persistence.sqlalchemy.models import StringOfficialPerformance
from app.adapters.persistence.sqlalchemy.models import StringRecommendationMatrix
from app.adapters.persistence.sqlalchemy.repositories.mappers import (
    to_official_performance,
)
from app.adapters.persistence.sqlalchemy.repositories.mappers import (
    to_recommendation_matrix_entry,
)
from app.adapters.persistence.sqlalchemy.repositories.mappers import to_string_item
from app.config.settings import get_settings
from app.domain.catalog.entities import InventoryMovementRecord
from app.domain.catalog.entities import RecommendationMatrixImportReport
from app.domain.catalog.entities import RecommendationMatrixInspectionRecord
from app.domain.catalog.entities import StringItem
from app.domain.catalog.entities import (
    StringOfficialPerformance as OfficialPerformanceRecord,
)
from app.domain.catalog.policies import InventoryAvailability
from app.shared.pagination import Page


class SqlAlchemyCatalogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _base_query(self):
        return select(StringCatalogItem).options(
            selectinload(StringCatalogItem.brand_ref),
            selectinload(StringCatalogItem.metrics),
            selectinload(StringCatalogItem.tags),
            selectinload(StringCatalogItem.official_performance),
            selectinload(StringCatalogItem.inventory_item).selectinload(
                StringInventoryItem.movements
            ),
            selectinload(StringCatalogItem.recommendation_entries).selectinload(
                StringRecommendationMatrix.feature_definition
            ),
        )

    def _apply_string_filters(
        self,
        query,
        count_query,
        *,
        is_active: bool | None = None,
        brand: str | None = None,
        series: str | None = None,
        gauge_min: float | None = None,
        gauge_max: float | None = None,
        is_hybrid: bool | None = None,
        search: str | None = None,
    ):
        if is_active is not None:
            predicate = StringCatalogItem.is_active.is_(is_active)
            query = query.where(predicate)
            count_query = count_query.where(predicate)

        if brand:
            brand_term = f"%{brand.strip()}%"
            brand_filter = or_(
                StringCatalogItem.display_name.ilike(brand_term),
                StringCatalogItem.original_brand_label.ilike(brand_term),
                StringCatalogItem.brand_code.ilike(brand_term),
            )
            query = query.where(brand_filter)
            count_query = count_query.where(brand_filter)

        if series:
            term = f"%{series.strip()}%"
            series_filter = or_(
                StringCatalogItem.series_key.ilike(term),
                StringCatalogItem.series_label.ilike(term),
            )
            query = query.where(series_filter)
            count_query = count_query.where(series_filter)

        if gauge_min is not None:
            gauge_min_filter = StringCatalogItem.gauge_main_mm >= gauge_min
            query = query.where(gauge_min_filter)
            count_query = count_query.where(gauge_min_filter)
        if gauge_max is not None:
            gauge_max_filter = StringCatalogItem.gauge_main_mm <= gauge_max
            query = query.where(gauge_max_filter)
            count_query = count_query.where(gauge_max_filter)

        if is_hybrid is not None:
            predicate = StringCatalogItem.is_hybrid.is_(is_hybrid)
            query = query.where(predicate)
            count_query = count_query.where(predicate)

        if search:
            term = f"%{search.strip()}%"
            search_filter = or_(
                StringCatalogItem.display_name.ilike(term),
                StringCatalogItem.model_name.ilike(term),
                StringCatalogItem.series_label.ilike(term),
                StringCatalogItem.material_summary_en.ilike(term),
                StringCatalogItem.short_description.ilike(term),
                StringCatalogItem.tags.any(StringCatalogTag.tag_label.ilike(term)),
                StringCatalogItem.tags.any(StringCatalogTag.tag_key.ilike(term)),
                StringCatalogItem.brand_ref.has(
                    StringCatalogItem.brand_ref.property.mapper.class_.brand_name.ilike(
                        term
                    )
                ),
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        return query, count_query

    def get_by_id(
        self,
        string_id: str,
        *,
        include_inactive: bool = False,
    ) -> StringItem | None:
        item = self.db.execute(
            self._base_query().where(StringCatalogItem.catalog_id == string_id)
        ).scalar_one_or_none()
        if item is None or (not include_inactive and not item.is_active):
            return None
        return to_string_item(item)

    def list_strings(
        self,
        *,
        is_active: bool | None,
        brand: str | None,
        series: str | None,
        gauge_min: float | None,
        gauge_max: float | None,
        is_hybrid: bool | None,
        search: str | None,
        sort_by: str,
        sort_order: str,
        limit: int | None,
        offset: int,
    ) -> Page[StringItem]:
        query = self._base_query()
        count_query = select(func.count()).select_from(StringCatalogItem)
        query, count_query = self._apply_string_filters(
            query,
            count_query,
            is_active=is_active,
            brand=brand,
            series=series,
            gauge_min=gauge_min,
            gauge_max=gauge_max,
            is_hybrid=is_hybrid,
            search=search,
        )

        total = self.db.execute(count_query).scalar_one()
        sort_columns: dict[str, Any] = {
            "brand": StringCatalogItem.brand_code,
            "display_name": StringCatalogItem.display_name,
            "model_name": StringCatalogItem.model_name,
            "price_rm": StringInventoryItem.selling_price,
            "gauge_main_mm": StringCatalogItem.gauge_main_mm,
            "community_rating": StringCatalogMetric.community_rating,
            "created_at": StringCatalogItem.created_at,
            "updated_at": StringCatalogItem.updated_at,
        }
        sort_column = sort_columns.get(sort_by, StringCatalogItem.display_name)
        if sort_by == "price_rm":
            query = query.outerjoin(StringCatalogItem.inventory_item)
        elif sort_by == "community_rating":
            query = query.outerjoin(StringCatalogItem.metrics)
        if sort_order == "desc":
            query = query.order_by(
                sort_column.desc(), StringCatalogItem.display_name.asc()
            )
        else:
            query = query.order_by(
                sort_column.asc(), StringCatalogItem.display_name.asc()
            )

        if limit is not None:
            query = query.limit(limit).offset(offset)
        items = self.db.execute(query).unique().scalars().all()
        return Page(
            items=[to_string_item(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    def list_inventory(
        self,
        *,
        brand: str | None,
        search: str | None,
        availability: InventoryAvailability | None,
        limit: int | None,
        offset: int,
    ) -> Page[StringItem]:
        query = self._base_query().join(StringCatalogItem.inventory_item)
        count_query = (
            select(func.count())
            .select_from(StringCatalogItem)
            .join(StringCatalogItem.inventory_item)
        )
        query, count_query = self._apply_string_filters(
            query,
            count_query,
            brand=brand,
            search=search,
        )

        if availability == "in_stock":
            predicate = and_(
                StringCatalogItem.is_active.is_(True),
                StringInventoryItem.available_stock > 5,
            )
            query = query.where(predicate)
            count_query = count_query.where(predicate)
        elif availability == "low_stock":
            predicate = and_(
                StringCatalogItem.is_active.is_(True),
                StringInventoryItem.available_stock > 0,
                StringInventoryItem.available_stock <= 5,
            )
            query = query.where(predicate)
            count_query = count_query.where(predicate)
        elif availability == "out_of_stock":
            predicate = or_(
                StringCatalogItem.is_active.is_(False),
                StringInventoryItem.available_stock <= 0,
            )
            query = query.where(predicate)
            count_query = count_query.where(predicate)

        total = self.db.execute(count_query).scalar_one()
        query = query.order_by(
            StringCatalogItem.brand_code.asc(),
            StringCatalogItem.display_name.asc(),
        )
        if limit is not None:
            query = query.limit(limit).offset(offset)
        items = self.db.execute(query).unique().scalars().all()
        return Page(
            items=[to_string_item(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    def create(self, values: dict[str, object]) -> StringItem:
        catalog_values = self._mapping(values["catalog"])
        metric_values = self._mapping(values["metrics"])
        tag_values = self._sequence(values["tags"])
        official_values = self._mapping(values["official_performance"])
        inventory_values = self._mapping(values["inventory"])
        matrix_values = self._sequence(values["matrix_entries"])

        item = StringCatalogItem(**catalog_values)
        item.metrics = StringCatalogMetric(catalog_id=item.catalog_id, **metric_values)
        item.tags = [
            StringCatalogTag(catalog_id=item.catalog_id, **tag) for tag in tag_values
        ]
        item.official_performance = StringOfficialPerformance(
            catalog_id=item.catalog_id,
            **official_values,
        )
        item.inventory_item = StringInventoryItem(
            catalog_id=item.catalog_id,
            **inventory_values,
        )
        item.recommendation_entries = [
            StringRecommendationMatrix(catalog_id=item.catalog_id, **entry)
            for entry in matrix_values
        ]
        self.db.add(item)
        self.db.commit()
        return self.get_by_id(item.catalog_id, include_inactive=True)  # type: ignore[return-value]

    def update(self, string_id: str, values: dict[str, object]) -> StringItem:
        item = self.db.get(StringCatalogItem, string_id)
        assert item is not None
        for field, value in self._mapping(values["catalog"]).items():
            setattr(item, field, value)
        inventory_values = self._mapping(values.get("inventory") or {})
        if inventory_values and item.inventory_item is not None:
            for field, value in inventory_values.items():
                setattr(item.inventory_item, field, value)
        self.db.commit()
        return self.get_by_id(string_id, include_inactive=True)  # type: ignore[return-value]

    def deactivate(self, string_id: str) -> StringItem:
        item = self.db.get(StringCatalogItem, string_id)
        assert item is not None
        item.is_active = False
        if item.inventory_item is not None:
            item.inventory_item.is_active = False
        self.db.commit()
        return self.get_by_id(string_id, include_inactive=True)  # type: ignore[return-value]

    def update_inventory(self, string_id: str, values: dict[str, object]) -> StringItem:
        item = self.db.get(StringCatalogItem, string_id)
        assert item is not None
        inventory = item.inventory_item
        assert inventory is not None

        if "price_rm" in values:
            inventory.selling_price = cast(float | None, values["price_rm"])
        if "selling_price" in values:
            inventory.selling_price = cast(float | None, values["selling_price"])
        if "cost_price" in values:
            inventory.cost_price = cast(float | None, values["cost_price"])
        if "reorder_level" in values:
            inventory.reorder_level = int(cast(int, values["reorder_level"]))
        if "reorder_quantity" in values:
            inventory.reorder_quantity = int(cast(int, values["reorder_quantity"]))
        if "is_active" in values:
            inventory.is_active = bool(values["is_active"])
            item.is_active = bool(values["is_active"])

        current_stock = inventory.current_stock
        reserved_stock = inventory.reserved_stock
        if "current_stock" in values:
            current_stock = int(cast(int, values["current_stock"]))
        elif "stock_level" in values:
            current_stock = int(cast(int, values["stock_level"])) + reserved_stock
        if "reserved_stock" in values:
            reserved_stock = int(cast(int, values["reserved_stock"]))

        inventory.current_stock = current_stock
        inventory.reserved_stock = reserved_stock
        inventory.available_stock = max(current_stock - reserved_stock, 0)
        item.is_active = (
            item.is_active and inventory.is_active and inventory.available_stock > 0
        )

        note = values.get("admin_note")
        movement_type = values.get("movement_type") or "ADJUSTMENT"
        has_stock_change = (
            "stock_level" in values
            or "current_stock" in values
            or "reserved_stock" in values
        )
        if note is not None or has_stock_change:
            self.db.add(
                InventoryMovement(
                    inventory_id=inventory.inventory_id,
                    movement_type=str(movement_type),
                    quantity=inventory.available_stock,
                    reference_type=values.get("reference_type"),
                    reference_id=values.get("reference_id"),
                    note=str(note).strip()
                    if isinstance(note, str) and note.strip()
                    else None,
                )
            )

        self.db.commit()
        return self.get_by_id(string_id, include_inactive=True)  # type: ignore[return-value]

    def get_official_performance(
        self,
        string_id: str,
    ) -> OfficialPerformanceRecord | None:
        item = self.db.get(StringOfficialPerformance, string_id)
        return to_official_performance(item)

    def update_official_performance(
        self,
        string_id: str,
        values: dict[str, object],
    ) -> OfficialPerformanceRecord:
        item = self.db.get(StringOfficialPerformance, string_id)
        assert item is not None
        for field, value in values.items():
            setattr(item, field, value)
        parent = self.db.get(StringCatalogItem, string_id)
        assert parent is not None
        if "status" in values:
            parent.official_performance_status = str(values["status"])
        self.db.commit()
        refreshed = self.db.get(StringOfficialPerformance, string_id)
        assert refreshed is not None
        return to_official_performance(refreshed)  # type: ignore[return-value]

    def list_inventory_movements(
        self,
        string_id: str,
        *,
        limit: int | None,
        offset: int,
    ) -> Page[InventoryMovementRecord]:
        inventory = self.db.execute(
            select(StringInventoryItem).where(
                StringInventoryItem.catalog_id == string_id
            )
        ).scalar_one_or_none()
        if inventory is None:
            return Page(items=[], total=0, limit=limit, offset=offset)

        query = select(InventoryMovement).where(
            InventoryMovement.inventory_id == inventory.inventory_id
        )
        count_query = (
            select(func.count())
            .select_from(InventoryMovement)
            .where(InventoryMovement.inventory_id == inventory.inventory_id)
        )
        total = self.db.execute(count_query).scalar_one()
        query = query.order_by(InventoryMovement.created_at.desc())
        if limit is not None:
            query = query.limit(limit).offset(offset)
        items = self.db.execute(query).scalars().all()
        return Page(
            items=[
                InventoryMovementRecord(
                    movement_id=item.movement_id,
                    inventory_id=item.inventory_id,
                    movement_type=item.movement_type,
                    quantity=item.quantity,
                    reference_type=item.reference_type,
                    reference_id=item.reference_id,
                    note=item.note,
                    created_at=item.created_at,
                )
                for item in items
            ],
            total=total,
            limit=limit,
            offset=offset,
        )

    def get_recommendation_matrix(
        self,
        string_id: str,
    ) -> RecommendationMatrixInspectionRecord | None:
        item = self.db.execute(
            self._base_query().where(StringCatalogItem.catalog_id == string_id)
        ).scalar_one_or_none()
        if item is None:
            return None
        return RecommendationMatrixInspectionRecord(
            catalog_id=item.catalog_id,
            display_name=item.display_name,
            effective_scores=to_string_item(item).aspect_scores,
            official_performance=to_official_performance(item.official_performance),
            matrix_entries=[
                to_recommendation_matrix_entry(entry)
                for entry in sorted(
                    item.recommendation_entries,
                    key=lambda row: (
                        row.source_layer,
                        row.feature_key,
                    ),
                )
            ],
        )

    def import_recommendation_matrix(self) -> RecommendationMatrixImportReport:
        report = import_recommendation_matrix_csv(
            self.db,
            get_settings().recommendation_matrix_path,
        )
        self.db.commit()
        return report

    def list_active_catalog(self) -> list[StringItem]:
        items = (
            self.db.execute(
                self._base_query()
                .where(StringCatalogItem.is_active.is_(True))
                .order_by(
                    StringCatalogItem.brand_code.asc(),
                    StringCatalogItem.display_name.asc(),
                )
            )
            .scalars()
            .all()
        )
        return [to_string_item(item) for item in items]

    @staticmethod
    def _mapping(value: object) -> dict[str, object]:
        return dict(cast(Mapping[str, object], value))

    @staticmethod
    def _sequence(value: object) -> list[dict[str, object]]:
        return list(cast(Sequence[dict[str, object]], value))
