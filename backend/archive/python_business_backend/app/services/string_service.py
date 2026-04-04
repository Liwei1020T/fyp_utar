from decimal import Decimal

from sqlalchemy import delete
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import String
from app.db.models import StringTag
from app.db.session import create_all_tables
from app.db.session import SessionLocal
from app.schemas.string import StringPayload


class StringService:
    STRING_SORT_FIELDS = {
        "brand": String.brand,
        "model_name": String.model_name,
        "price": String.price,
        "rating": String.rating,
        "created_at": String.created_at,
        "updated_at": String.updated_at,
        "popularity_signal": String.popularity_signal,
    }

    def reset(self) -> None:
        create_all_tables()
        with SessionLocal() as db:
            db.execute(delete(StringTag))
            db.execute(delete(String))
            db.add_all(
                [
                    String(
                        external_id="seed-bg80",
                        brand="Yonex",
                        brand_en="Yonex",
                        model_name="BG80",
                        series="BG",
                        series_en="BG",
                        currency="RM",
                        gauge_raw="0.68mm",
                        gauge_mm=Decimal("0.68"),
                        material="High polymer nylon",
                        material_en="High polymer nylon",
                        color="Yellow",
                        rating=Decimal("4.60"),
                        rating_5_scale=Decimal("4.60"),
                        want_count=120,
                        used_count=95,
                        review_count=88,
                        popularity_signal=92,
                        feature_text="弹性好，控球好，声音清脆",
                        feature_text_en="High repulsion, good control, crisp hitting sound.",
                        source_url="https://stringsense.local/seed/bg80",
                        repulsion_score=Decimal("4.30"),
                        durability_score=Decimal("4.40"),
                        control_score=Decimal("4.60"),
                        sound_score=Decimal("4.50"),
                        tension_retention_score=Decimal("3.80"),
                        value_score=Decimal("4.00"),
                        availability_status="active",
                        price=39,
                        recommended_tension_min=20,
                        recommended_tension_max=28,
                        description="Balanced control and sharp repulsion.",
                        is_active=True,
                    ),
                    String(
                        external_id="seed-exbolt63",
                        brand="Yonex",
                        brand_en="Yonex",
                        model_name="Exbolt 63",
                        series="Exbolt",
                        series_en="Exbolt",
                        currency="RM",
                        gauge_raw="0.63mm",
                        gauge_mm=Decimal("0.63"),
                        material="Forged fiber",
                        material_en="Forged fiber",
                        color="White",
                        rating=Decimal("4.40"),
                        rating_5_scale=Decimal("4.40"),
                        want_count=80,
                        used_count=60,
                        review_count=47,
                        popularity_signal=78,
                        feature_text="弹性好，声音清脆",
                        feature_text_en="Lively response with crisp sound.",
                        source_url="https://stringsense.local/seed/exbolt63",
                        repulsion_score=Decimal("4.70"),
                        durability_score=Decimal("3.40"),
                        control_score=Decimal("3.80"),
                        sound_score=Decimal("4.60"),
                        tension_retention_score=Decimal("3.20"),
                        value_score=Decimal("4.10"),
                        availability_status="active",
                        price=42,
                        recommended_tension_min=20,
                        recommended_tension_max=27,
                        description="Thin gauge with lively repulsion.",
                        is_active=True,
                    ),
                ]
            )
            db.commit()

    def list_active(
        self,
        db: Session,
        *,
        search: str | None = None,
        brand: str | None = None,
        sort_by: str = "brand",
        sort_order: str = "asc",
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        return self._list_strings(
            db,
            active_only=True,
            search=search,
            brand=brand,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )

    def list_all(
        self,
        db: Session,
        *,
        search: str | None = None,
        brand: str | None = None,
        is_active: bool | None = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        return self._list_strings(
            db,
            active_only=False,
            search=search,
            brand=brand,
            is_active=is_active,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )

    def get(
        self, db: Session, string_id: str, *, include_inactive: bool = False
    ) -> dict | None:
        item = db.execute(
            select(String).where(String.id == string_id)
        ).scalar_one_or_none()
        if item is None:
            return None
        if not include_inactive and not item.is_active:
            return None
        return self._serialize(item)

    def create(self, db: Session, payload: StringPayload) -> dict:
        item = String(
            **payload.model_dump(),
            is_active=True,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return self._serialize(item)

    def update(
        self, db: Session, string_id: str, payload: StringPayload
    ) -> dict | None:
        item = db.execute(
            select(String).where(String.id == string_id)
        ).scalar_one_or_none()
        if item is None:
            return None

        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(item, field, value)

        db.commit()
        db.refresh(item)
        return self._serialize(item)

    def deactivate(self, db: Session, string_id: str) -> dict | None:
        item = db.execute(
            select(String).where(String.id == string_id)
        ).scalar_one_or_none()
        if item is None:
            return None

        item.is_active = False
        db.commit()
        db.refresh(item)
        return self._serialize(item)

    @staticmethod
    def _serialize(item: String) -> dict:
        return {
            "id": item.id,
            "external_id": item.external_id,
            "brand": item.brand,
            "brand_en": item.brand_en,
            "model_name": item.model_name,
            "series": item.series,
            "series_en": item.series_en,
            "gauge_raw": item.gauge_raw,
            "gauge_mm": StringService._decimal_to_float(item.gauge_mm),
            "material": item.material,
            "material_en": item.material_en,
            "color": item.color,
            "rating": StringService._decimal_to_float(item.rating),
            "rating_5_scale": StringService._decimal_to_float(item.rating_5_scale),
            "want_count": item.want_count,
            "used_count": item.used_count,
            "review_count": item.review_count,
            "popularity_signal": item.popularity_signal,
            "feature_text": item.feature_text,
            "feature_text_en": item.feature_text_en,
            "source_url": item.source_url,
            "repulsion_score": StringService._decimal_to_float(item.repulsion_score),
            "durability_score": StringService._decimal_to_float(item.durability_score),
            "control_score": StringService._decimal_to_float(item.control_score),
            "sound_score": StringService._decimal_to_float(item.sound_score),
            "tension_retention_score": StringService._decimal_to_float(
                item.tension_retention_score
            ),
            "value_score": StringService._decimal_to_float(item.value_score),
            "availability_status": item.availability_status,
            "price": StringService._decimal_to_float(item.price),
            "recommended_tension_min": item.recommended_tension_min,
            "recommended_tension_max": item.recommended_tension_max,
            "currency": item.currency,
            "description": item.description,
            "is_active": item.is_active,
        }

    @staticmethod
    def _decimal_to_float(value: Decimal | None) -> float | None:
        if value is None:
            return None
        return float(value)

    def _list_strings(
        self,
        db: Session,
        *,
        active_only: bool,
        search: str | None,
        brand: str | None,
        is_active: bool | None = None,
        sort_by: str,
        sort_order: str,
        limit: int | None,
        offset: int,
    ) -> tuple[list[dict], int]:
        query = select(String)
        count_query = select(func.count()).select_from(String)

        if active_only:
            query = query.where(String.is_active.is_(True))
            count_query = count_query.where(String.is_active.is_(True))
        elif is_active is not None:
            query = query.where(String.is_active.is_(is_active))
            count_query = count_query.where(String.is_active.is_(is_active))

        if brand:
            query = query.where(String.brand.ilike(f"%{brand.strip()}%"))
            count_query = count_query.where(String.brand.ilike(f"%{brand.strip()}%"))

        if search:
            term = f"%{search.strip()}%"
            conditions = or_(
                String.brand.ilike(term),
                String.model_name.ilike(term),
                String.series.ilike(term),
                String.external_id.ilike(term),
            )
            query = query.where(conditions)
            count_query = count_query.where(conditions)

        total = db.execute(count_query).scalar_one()

        sort_column = self.STRING_SORT_FIELDS.get(sort_by, String.brand)
        if sort_order == "desc":
            query = query.order_by(
                sort_column.desc().nullslast(), String.model_name.asc()
            )
        else:
            query = query.order_by(
                sort_column.asc().nullslast(), String.model_name.asc()
            )

        if limit is not None:
            query = query.limit(limit).offset(offset)

        items = db.execute(query).scalars().all()
        return [self._serialize(item) for item in items], total


string_service = StringService()
