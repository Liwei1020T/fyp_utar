from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends

from app.domain.profile.entities import PlayerProfile
from app.dto.profile import ProfileOut
from app.dto.profile import ProfilePayload
from app.dto.profile import profile_to_dto
from app.entrypoints.api.dependencies import CurrentUser
from app.entrypoints.api.dependencies import get_current_customer
from app.entrypoints.api.dependencies import get_profile_repository
from app.entrypoints.api.dependencies import get_recommendation_repository
from app.use_cases.profile.get_my_profile import GetMyProfileUseCase
from app.use_cases.profile.upsert_my_profile import UpsertMyProfileUseCase


router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileOut)
def get_profile(
    current_user: CurrentUser = Depends(get_current_customer),
    profile_repository=Depends(get_profile_repository),
) -> ProfileOut:
    profile = GetMyProfileUseCase(profile_repository=profile_repository).execute(
        current_user.user_id
    )
    return profile_to_dto(profile)


@router.put("", response_model=ProfileOut)
def upsert_profile(
    payload: ProfilePayload,
    current_user: CurrentUser = Depends(get_current_customer),
    profile_repository=Depends(get_profile_repository),
    recommendation_repository=Depends(get_recommendation_repository),
) -> ProfileOut:
    profile = UpsertMyProfileUseCase(
        profile_repository=profile_repository,
        recommendation_repository=recommendation_repository,
    ).execute(
        PlayerProfile(
            user_id=current_user.user_id,
            created_at=None,
            updated_at=None,
            **payload.model_dump(),
        )
    )
    return profile_to_dto(profile)
