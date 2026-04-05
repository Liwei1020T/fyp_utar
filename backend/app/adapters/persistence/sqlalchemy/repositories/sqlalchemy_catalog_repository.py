from __future__ import annotations

from typing import Any

from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.models import StringCatalogItem
from app.adapters.persistence.sqlalchemy.repositories.mappers import to_string_item
from app.domain.catalog.entities import StringItem
from app.domain.catalog.policies import InventoryAvailability
from app.shared.pagination import Page


class SqlAlchemyCatalogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(
        self,
        string_id: str,
        *,
        include_inactive: bool = False,
    ) -> StringItem | None:
        item = self.db.execute(
            select(StringCatalogItem).where(StringCatalogItem.id == string_id)
        ).scalar_one_or_none()
        if item is None or (not include_inactive and not item.is_active):
            return None
        return to_string_item(item)

    def list_strings(
        self,
        *,
        is_active: bool | None,
        brand: str | None,
        search: str | None,
        sort_by: str,
        sort_order: str,
        limit: int | None,
        offset: int,
    ) -> Page[StringItem]:
        query = select(StringCatalogItem)
        count_query = select(func.count()).select_from(StringCatalogItem)

        if is_active is not None:
            active_filter = StringCatalogItem.is_active.is_(is_active)
            query = query.where(active_filter)
            count_query = count_query.where(active_filter)
        if brand:
            brand_filter = StringCatalogItem.brand.ilike(f"%{brand.strip()}%")
            query = query.where(brand_filter)
            count_query = count_query.where(brand_filter)
        if search:
            term = f"%{search.strip()}%"
            search_filter = or_(
                StringCatalogItem.brand.ilike(term),
                StringCatalogItem.model_name.ilike(term),
                StringCatalogItem.normalized_name.ilike(term),
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        total = self.db.execute(count_query).scalar_one()
        sort_columns: dict[str, Any] = {
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
        sort_column = sort_columns[sort_by]
        if sort_order == "desc":
            query = query.order_by(sort_column.desc(), StringCatalogItem.model_name.asc())
        else:
            query = query.order_by(sort_column.asc(), StringCatalogItem.model_name.asc())

        if limit is not None:
            query = query.limit(limit).offset(offset)
        items = self.db.execute(query).scalars().all()
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
        query = select(StringCatalogItem)
        count_query = select(func.count()).select_from(StringCatalogItem)

        if brand:
            brand_filter = StringCatalogItem.brand.ilike(f"%{brand.strip()}%")
            query = query.where(brand_filter)
            count_query = count_query.where(brand_filter)
        if search:
            term = f"%{search.strip()}%"
            search_filter = or_(
                StringCatalogItem.brand.ilike(term),
                StringCatalogItem.model_name.ilike(term),
                StringCatalogItem.normalized_name.ilike(term),
                StringCatalogItem.admin_note.ilike(term),
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        if availability == "in_stock":
            availability_filter = StringCatalogItem.is_active.is_(True) & (
                StringCatalogItem.stock_level > 5
            )
            query = query.where(availability_filter)
            count_query = count_query.where(availability_filter)
        elif availability == "low_stock":
            availability_filter = (
                StringCatalogItem.is_active.is_(True)
                & (StringCatalogItem.stock_level > 0)
                & (StringCatalogItem.stock_level <= 5)
            )
            query = query.where(availability_filter)
            count_query = count_query.where(availability_filter)
        elif availability == "out_of_stock":
            availability_filter = StringCatalogItem.is_active.is_(False) | (
                StringCatalogItem.stock_level <= 0
            )
            query = query.where(availability_filter)
            count_query = count_query.where(availability_filter)

        total = self.db.execute(count_query).scalar_one()
        query = query.order_by(
            StringCatalogItem.brand.asc(),
            StringCatalogItem.model_name.asc(),
        )
        if limit is not None:
            query = query.limit(limit).offset(offset)
        items = self.db.execute(query).scalars().all()
        return Page(
            items=[to_string_item(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    def create(self, values: dict[str, object]) -> StringItem:
        item = StringCatalogItem(**values)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return to_string_item(item)

    def update(self, string_id: str, values: dict[str, object]) -> StringItem:
        item = self.db.get(StringCatalogItem, string_id)
        assert item is not None
        for field, value in values.items():
            setattr(item, field, value)
        self.db.commit()
        self.db.refresh(item)
        return to_string_item(item)

    def deactivate(self, string_id: str) -> StringItem:
        item = self.db.get(StringCatalogItem, string_id)
        assert item is not None
        item.is_active = False
        self.db.commit()
        self.db.refresh(item)
        return to_string_item(item)

    def update_inventory(self, string_id: str, values: dict[str, object]) -> StringItem:
        item = self.db.get(StringCatalogItem, string_id)
        assert item is not None
        for field, value in values.items():
            setattr(item, field, value)
        self.db.commit()
        self.db.refresh(item)
        return to_string_item(item)

    def list_active_catalog(self) -> list[StringItem]:
        items = self.db.execute(
            select(StringCatalogItem)
            .where(StringCatalogItem.is_active.is_(True))
            .order_by(StringCatalogItem.brand.asc(), StringCatalogItem.model_name.asc())
        ).scalars().all()
        return [to_string_item(item) for item in items]
