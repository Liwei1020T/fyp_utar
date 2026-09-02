from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.session import get_db
from app.adapters.services.agent.admin_tools import ADMIN_AGENT_TOOL_SPECS
from app.adapters.services.agent.admin_tools import AdminAgentToolbox
from app.adapters.services.agent.deepseek import DeepSeekAgentClient
from app.config.settings import get_settings
from app.dto.agent import AgentQueryDto
from app.dto.agent import AgentResponseDto
from app.entrypoints.api.dependencies import CurrentUser
from app.entrypoints.api.dependencies import get_clock
from app.entrypoints.api.dependencies import get_booking_repository
from app.entrypoints.api.dependencies import get_catalog_repository
from app.entrypoints.api.dependencies import get_current_user
from app.entrypoints.api.dependencies import get_recommendation_run_repository
from app.entrypoints.api.dependencies import get_recommendation_repository
from app.entrypoints.api.dependencies import get_profile_repository
from app.entrypoints.api.dependencies import get_store_repository
from app.entrypoints.api.dependencies import require_roles
from app.domain.auth.entities import UserRole
from app.shared.errors import ServiceUnavailableError
from app.shared.rate_limit import SlidingWindowRateLimiter
from app.use_cases.agent.query_agent import QueryAgentUseCase
from app.use_cases.agent.tools import AGENT_TOOL_SPECS
from app.use_cases.agent.tools import AgentToolbox


router = APIRouter(prefix="/agent", tags=["agent"])
_agent_limiter = SlidingWindowRateLimiter(limit=12, window_seconds=60)


def get_deepseek_agent_client() -> DeepSeekAgentClient:
    settings = get_settings()
    if not settings.agent_enabled or settings.agent_api_key is None:
        raise ServiceUnavailableError("Agent is not configured")
    return DeepSeekAgentClient(
        api_key=settings.agent_api_key.get_secret_value(),
        model=settings.agent_model,
        base_url=settings.agent_base_url,
        timeout_seconds=settings.agent_timeout_seconds,
    )


@router.post("/query", response_model=AgentResponseDto)
def query_agent(
    payload: AgentQueryDto,
    current_user: CurrentUser = Depends(get_current_user),
    model_client: DeepSeekAgentClient = Depends(get_deepseek_agent_client),
    catalog_repository=Depends(get_catalog_repository),
    recommendation_run_repository=Depends(get_recommendation_run_repository),
    store_repository=Depends(get_store_repository),
    booking_repository=Depends(get_booking_repository),
    profile_repository=Depends(get_profile_repository),
    recommendation_repository=Depends(get_recommendation_repository),
    clock=Depends(get_clock),
    db: Session = Depends(get_db, scope="function"),
) -> AgentResponseDto:
    _agent_limiter.check(current_user.user_id)
    is_admin = payload.context.surface == "admin_assistant"
    require_roles(
        current_user,
        UserRole.ADMIN if is_admin else UserRole.CUSTOMER,
    )
    toolbox = (
        AdminAgentToolbox(
            catalog_repository=catalog_repository,
            recommendation_run_repository=recommendation_run_repository,
            store_repository=store_repository,
            booking_repository=booking_repository,
            profile_repository=profile_repository,
            recommendation_repository=recommendation_repository,
            db=db,
            clock=clock,
            store_timezone=get_settings().store_timezone,
        )
        if is_admin
        else AgentToolbox(
            catalog_repository=catalog_repository,
            recommendation_run_repository=recommendation_run_repository,
            store_repository=store_repository,
            booking_repository=booking_repository,
            profile_repository=profile_repository,
            recommendation_repository=recommendation_repository,
        )
    )
    return QueryAgentUseCase(
        toolbox=toolbox,
        model_client=model_client,
        max_tool_rounds=get_settings().agent_max_tool_rounds,
        tool_specs=ADMIN_AGENT_TOOL_SPECS if is_admin else AGENT_TOOL_SPECS,
    ).execute(payload=payload, user_id=current_user.user_id)
