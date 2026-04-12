from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends

from app.dto.recommendation import ProfileRecommendationPayload
from app.dto.recommendation import RecommendationDetailDto
from app.dto.recommendation import RecommendationRequestDto
from app.dto.recommendation import RecommendationResponseDto
from app.dto.recommendation import recommendation_detail_to_dto
from app.dto.recommendation import recommendation_request_to_domain
from app.dto.recommendation import recommendation_response_to_dto
from app.entrypoints.api.dependencies import CurrentUser
from app.entrypoints.api.dependencies import get_current_customer
from app.entrypoints.api.dependencies import get_profile_repository
from app.entrypoints.api.dependencies import get_recommendation_log_repository
from app.entrypoints.api.dependencies import get_recommendation_repository
from app.shared.errors import ForbiddenError
from app.use_cases.recommendation.generate_recommendation import (
    GenerateRecommendationUseCase,
)
from app.domain.recommendation.scoring import ALGORITHM_VERSION


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/preview", response_model=RecommendationResponseDto)
def preview_recommendations(
    payload: RecommendationRequestDto,
    current_user: CurrentUser = Depends(get_current_customer),
    profile_repository=Depends(get_profile_repository),
    recommendation_repository=Depends(get_recommendation_repository),
    recommendation_log_repository=Depends(get_recommendation_log_repository),
) -> RecommendationResponseDto:
    result = GenerateRecommendationUseCase(
        profile_repository=profile_repository,
        recommendation_repository=recommendation_repository,
        recommendation_log_repository=recommendation_log_repository,
    ).execute_preview(
        user_id=current_user.user_id,
        request=recommendation_request_to_domain(payload),
    )
    return recommendation_response_to_dto(result)


@router.post("/profile", response_model=RecommendationResponseDto)
def recommend_for_profile(
    payload: ProfileRecommendationPayload,
    current_user: CurrentUser = Depends(get_current_customer),
    profile_repository=Depends(get_profile_repository),
    recommendation_repository=Depends(get_recommendation_repository),
    recommendation_log_repository=Depends(get_recommendation_log_repository),
) -> RecommendationResponseDto:
    result = GenerateRecommendationUseCase(
        profile_repository=profile_repository,
        recommendation_repository=recommendation_repository,
        recommendation_log_repository=recommendation_log_repository,
    ).execute_profile(user_id=current_user.user_id, top_n=payload.top_n)
    return recommendation_response_to_dto(result)


@router.post("/generate", response_model=RecommendationResponseDto)
def generate_recommendations(
    payload: ProfileRecommendationPayload,
    current_user: CurrentUser = Depends(get_current_customer),
    profile_repository=Depends(get_profile_repository),
    recommendation_repository=Depends(get_recommendation_repository),
    recommendation_log_repository=Depends(get_recommendation_log_repository),
) -> RecommendationResponseDto:
    result = GenerateRecommendationUseCase(
        profile_repository=profile_repository,
        recommendation_repository=recommendation_repository,
        recommendation_log_repository=recommendation_log_repository,
    ).execute_profile(user_id=current_user.user_id, top_n=payload.top_n)
    return recommendation_response_to_dto(result)


@router.get("/{user_id}", response_model=RecommendationResponseDto)
def get_cached_recommendations(
    user_id: str,
    current_user: CurrentUser = Depends(get_current_customer),
    profile_repository=Depends(get_profile_repository),
    recommendation_repository=Depends(get_recommendation_repository),
    recommendation_log_repository=Depends(get_recommendation_log_repository),
) -> RecommendationResponseDto:
    target_user_id = _authorized_target_user_id(current_user, user_id)
    result = GenerateRecommendationUseCase(
        profile_repository=profile_repository,
        recommendation_repository=recommendation_repository,
        recommendation_log_repository=recommendation_log_repository,
    ).execute_cached(user_id=target_user_id)
    return recommendation_response_to_dto(result)


@router.get("/{user_id}/{catalog_id}", response_model=RecommendationDetailDto)
def get_cached_recommendation_detail(
    user_id: str,
    catalog_id: str,
    current_user: CurrentUser = Depends(get_current_customer),
    profile_repository=Depends(get_profile_repository),
    recommendation_repository=Depends(get_recommendation_repository),
    recommendation_log_repository=Depends(get_recommendation_log_repository),
) -> RecommendationDetailDto:
    target_user_id = _authorized_target_user_id(current_user, user_id)
    result = GenerateRecommendationUseCase(
        profile_repository=profile_repository,
        recommendation_repository=recommendation_repository,
        recommendation_log_repository=recommendation_log_repository,
    ).execute_detail(user_id=target_user_id, catalog_id=catalog_id)
    return recommendation_detail_to_dto(
        algorithm_version=ALGORITHM_VERSION,
        result=result,
    )


def _authorized_target_user_id(current_user: CurrentUser, user_id: str) -> str:
    if user_id == "me":
        return current_user.user_id
    if current_user.role == "admin":
        return user_id
    if user_id != current_user.user_id:
        raise ForbiddenError("Cannot access another user's recommendations")
    return user_id
