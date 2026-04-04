from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_customer
from app.api.responses import success_response
from app.db.session import get_db
from app.schemas.recommendation import RecommendationPayload
from app.services.recommendation_service import recommendation_service


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/generate")
def generate_recommendations(
    payload: RecommendationPayload,
    user: dict = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> dict:
    result = recommendation_service.generate(
        db,
        user_id=user["sub"],
        payload=payload,
    )

    return success_response(
        message="Recommendations generated successfully",
        data=result,
    )
