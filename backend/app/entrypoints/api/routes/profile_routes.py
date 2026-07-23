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
from app.entrypoints.api.dependencies import get_user_repository
from app.use_cases.profile.get_my_profile import GetMyProfileUseCase
from app.use_cases.profile.upsert_my_profile import UpsertMyProfileUseCase


router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileOut)
def get_profile(
    current_user: CurrentUser = Depends(get_current_customer),
    profile_repository=Depends(get_profile_repository),
    user_repository=Depends(get_user_repository),
) -> ProfileOut:
    profile = GetMyProfileUseCase(profile_repository=profile_repository).execute(
        current_user.user_id
    )
    user = user_repository.get_by_id(current_user.user_id)
    assert user is not None
    return profile_to_dto(profile, username=user.username)


@router.put("", response_model=ProfileOut)
def upsert_profile(
    payload: ProfilePayload,
    current_user: CurrentUser = Depends(get_current_customer),
    profile_repository=Depends(get_profile_repository),
    recommendation_repository=Depends(get_recommendation_repository),
    user_repository=Depends(get_user_repository),
) -> ProfileOut:
    profile = UpsertMyProfileUseCase(
        profile_repository=profile_repository,
        recommendation_repository=recommendation_repository,
    ).execute(
        PlayerProfile(
            user_id=current_user.user_id,
            created_at=None,
            updated_at=None,
            **payload.model_dump(exclude={"username"}),
        ),
        username=payload.username,
    )
    user = user_repository.get_by_id(current_user.user_id)
    assert user is not None
    return profile_to_dto(profile, username=user.username)
