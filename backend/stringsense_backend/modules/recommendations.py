from __future__ import annotations

import json

from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from ai_service.schemas import RecommendationRequest
from ai_service.schemas import RecommendationResponse

from stringsense_backend.api.dependencies import CurrentUser
from stringsense_backend.api.dependencies import get_current_customer
from stringsense_backend.core.errors import BadRequestError
from stringsense_backend.core.errors import NotFoundError
from stringsense_backend.core.http import page_response
from stringsense_backend.db.models import RecommendationLog
from stringsense_backend.db.models import StringCatalogItem
from stringsense_backend.db.models import User
from stringsense_backend.db.session import get_db
from stringsense_backend.modules.ai import ai_service
from stringsense_backend.modules.profile import get_profile_or_none
from stringsense_backend.modules.profile import serialize_profile


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


class ProfileRecommendationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    top_n: int = Field(default=5, ge=1, le=10)


def active_catalog(db: Session) -> list[StringCatalogItem]:
    return (
        db.execute(
            select(StringCatalogItem)
            .where(StringCatalogItem.is_active.is_(True))
            .order_by(StringCatalogItem.brand.asc(), StringCatalogItem.model_name.asc())
        )
        .scalars()
        .all()
    )


def log_recommendation(
    db: Session,
    *,
    user_id: str | None,
    request_payload: dict[str, object],
    response_payload: RecommendationResponse,
) -> None:
    db.add(
        RecommendationLog(
            user_id=user_id,
            request_json=json.dumps(
                request_payload, ensure_ascii=False, sort_keys=True
            ),
            recommendation_json=response_payload.model_dump_json(),
            algorithm_version=response_payload.algorithm_version,
        )
    )
    db.flush()


@router.post("/preview", response_model=RecommendationResponse)
def preview_recommendations(
    payload: RecommendationRequest,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    result = ai_service.recommend(active_catalog(db), payload)
    log_recommendation(
        db,
        user_id=current_user.user_id,
        request_payload=payload.model_dump(mode="json"),
        response_payload=result,
    )
    db.commit()
    return result


@router.post("/profile", response_model=RecommendationResponse)
def recommend_for_profile(
    payload: ProfileRecommendationPayload,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    profile = get_profile_or_none(db, current_user.user_id)
    if profile is None:
        raise NotFoundError("Profile not found")

    profile_payload = serialize_profile(profile).model_dump(
        exclude={"created_at", "updated_at"}
    )
    profile_payload["top_n"] = payload.top_n
    try:
        request = RecommendationRequest(**profile_payload)
    except Exception as exc:  # pragma: no cover - converted below
        raise BadRequestError(
            "Profile is incomplete for recommendation", details=str(exc)
        ) from exc

    result = ai_service.recommend(active_catalog(db), request)
    log_recommendation(
        db,
        user_id=current_user.user_id,
        request_payload=request.model_dump(mode="json"),
        response_payload=result,
    )
    db.commit()
    return result


def recommendation_logs_page(
    *,
    phone_number: str | None,
    algorithm_version: str | None,
    limit: int | None,
    offset: int,
    db: Session,
) -> dict[str, object]:
    query = select(RecommendationLog).options(joinedload(RecommendationLog.user))
    count_query = select(func.count()).select_from(RecommendationLog)

    if algorithm_version:
        query = query.where(RecommendationLog.algorithm_version == algorithm_version)
        count_query = count_query.where(
            RecommendationLog.algorithm_version == algorithm_version
        )
    if phone_number:
        query = query.join(RecommendationLog.user)
        count_query = count_query.join(RecommendationLog.user)
        query = query.where(User.phone_number.ilike(f"%{phone_number}%"))
        count_query = count_query.where(User.phone_number.ilike(f"%{phone_number}%"))

    total = db.execute(count_query).scalar_one()
    query = query.order_by(RecommendationLog.created_at.desc())
    if limit is not None:
        query = query.limit(limit).offset(offset)

    items = db.execute(query).unique().scalars().all()
    return page_response(
        items=[
            {
                "id": item.id,
                "user_id": item.user_id,
                "phone_number": item.user.phone_number if item.user else None,
                "username": item.user.username if item.user else None,
                "request": json.loads(item.request_json),
                "recommendation": json.loads(item.recommendation_json),
                "algorithm_version": item.algorithm_version,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in items
        ],
        total=total,
        limit=limit,
        offset=offset,
    )
