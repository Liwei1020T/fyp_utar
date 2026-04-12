from __future__ import annotations

from fastapi import APIRouter
from fastapi import Body
from fastapi import Depends
from fastapi import HTTPException
from pydantic import BaseModel
from pydantic import ValidationError

from app.config.settings import get_settings
from app.dto.auth import AuthResponse
from app.dto.auth import ForgotPasswordRequest
from app.dto.auth import ForgotPasswordRequestResponse
from app.dto.auth import ForgotPasswordResetRequest
from app.dto.auth import LoginRequest
from app.dto.auth import MessageResponse
from app.dto.auth import RegisterRequest
from app.dto.auth import UserOut
from app.dto.auth import user_to_dto
from app.entrypoints.api.dependencies import CurrentUser
from app.entrypoints.api.dependencies import get_clock
from app.entrypoints.api.dependencies import get_current_user
from app.entrypoints.api.dependencies import get_password_hasher
from app.entrypoints.api.dependencies import get_password_reset_repository
from app.entrypoints.api.dependencies import get_token_service
from app.entrypoints.api.dependencies import get_user_repository
from app.ports.services.password_hasher import PasswordHasher
from app.use_cases.auth.get_current_user import GetCurrentUserUseCase
from app.use_cases.auth.login import LoginUseCase
from app.use_cases.auth.register import RegisterUserUseCase
from app.use_cases.auth.request_password_reset import RequestPasswordResetUseCase
from app.use_cases.auth.reset_password import ResetPasswordUseCase


router = APIRouter(prefix="/auth", tags=["auth"])


def _build_auth_response(user, token_service) -> AuthResponse:
    return AuthResponse(
        access_token=token_service.create_access_token(
            subject=user.id,
            role=user.role,
            phone_number=user.phone_number,
        ),
        role=user.role,
        phone_number=user.phone_number,
        user_id=user.id,
        user=user_to_dto(user),
    )


def _validate_payload(model: type[BaseModel], payload: dict, **context):
    try:
        return model.model_validate(payload, context=context)
    except ValidationError as exc:
        first_error = dict(exc.errors()[0]) if exc.errors() else {}
        message = str(first_error.get("msg", "Invalid request"))
        if message.startswith("Value error, "):
            message = message.removeprefix("Value error, ")
        raise HTTPException(status_code=422, detail=message) from exc


@router.post("/register", response_model=AuthResponse)
def register(
    payload: dict = Body(...),
    user_repository=Depends(get_user_repository),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
    token_service=Depends(get_token_service),
) -> AuthResponse:
    request = _validate_payload(
        RegisterRequest,
        payload,
        password_hasher=password_hasher,
    )
    user = RegisterUserUseCase(
        user_repository=user_repository,
        password_hasher=password_hasher,
    ).execute(
        username=request.username,
        phone_number=request.phone_number,
        password=request.password,
    )
    return _build_auth_response(user, token_service)


@router.post("/login", response_model=AuthResponse)
def login(
    payload: dict = Body(...),
    user_repository=Depends(get_user_repository),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
    token_service=Depends(get_token_service),
) -> AuthResponse:
    request = _validate_payload(
        LoginRequest,
        payload,
        password_hasher=password_hasher,
    )
    user = LoginUseCase(
        user_repository=user_repository,
        password_hasher=password_hasher,
    ).execute(
        phone_number=request.phone_number,
        password=request.password,
    )
    return _build_auth_response(user, token_service)


@router.post(
    "/forgot-password/request-code",
    response_model=ForgotPasswordRequestResponse,
)
def request_forgot_password_code(
    payload: dict = Body(...),
    user_repository=Depends(get_user_repository),
    password_reset_repository=Depends(get_password_reset_repository),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
    clock=Depends(get_clock),
) -> ForgotPasswordRequestResponse:
    request = _validate_payload(
        ForgotPasswordRequest,
        payload,
        password_hasher=password_hasher,
    )
    settings = get_settings()
    code = RequestPasswordResetUseCase(
        user_repository=user_repository,
        password_reset_repository=password_reset_repository,
        password_hasher=password_hasher,
        clock=clock,
        expire_minutes=settings.password_reset_code_expire_minutes,
        dev_preview_enabled=settings.password_reset_dev_preview_enabled,
        is_dev_like=settings.is_dev_like,
    ).execute(phone_number=request.phone_number)
    return ForgotPasswordRequestResponse(dev_code_preview=code)


@router.post("/forgot-password/reset", response_model=MessageResponse)
def reset_forgot_password(
    payload: dict = Body(...),
    user_repository=Depends(get_user_repository),
    password_reset_repository=Depends(get_password_reset_repository),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
    clock=Depends(get_clock),
) -> MessageResponse:
    request = _validate_payload(
        ForgotPasswordResetRequest,
        payload,
        password_hasher=password_hasher,
    )
    settings = get_settings()
    ResetPasswordUseCase(
        user_repository=user_repository,
        password_reset_repository=password_reset_repository,
        password_hasher=password_hasher,
        clock=clock,
        max_attempts=settings.password_reset_code_max_attempts,
    ).execute(
        phone_number=request.phone_number,
        verification_code=request.verification_code,
        new_password=request.new_password,
    )
    return MessageResponse(message="Password reset successful")


@router.get("/me", response_model=UserOut)
def me(
    current_user: CurrentUser = Depends(get_current_user),
    user_repository=Depends(get_user_repository),
) -> UserOut:
    user = GetCurrentUserUseCase(user_repository=user_repository).execute(
        current_user.user_id
    )
    return user_to_dto(user)
