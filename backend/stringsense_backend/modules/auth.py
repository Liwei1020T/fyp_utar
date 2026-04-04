from __future__ import annotations

import secrets
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from stringsense_backend.api.dependencies import CurrentUser
from stringsense_backend.api.dependencies import get_current_user
from stringsense_backend.core.config import get_settings
from stringsense_backend.core.domain import AuthProvider
from stringsense_backend.core.domain import UserRole
from stringsense_backend.core.errors import BadRequestError
from stringsense_backend.core.errors import ConflictError
from stringsense_backend.core.errors import ForbiddenError
from stringsense_backend.core.errors import NotFoundError
from stringsense_backend.core.errors import UnauthorizedError
from stringsense_backend.core.security import create_access_token
from stringsense_backend.core.security import hash_password
from stringsense_backend.core.security import normalize_phone_number
from stringsense_backend.core.security import validate_local_password
from stringsense_backend.core.security import verify_password
from stringsense_backend.db.models import PasswordResetCode
from stringsense_backend.db.models import User
from stringsense_backend.db.session import get_db


router = APIRouter(prefix="/auth", tags=["auth"])
PASSWORD_RESET_CODE_LENGTH = 6
PASSWORD_RESET_SUCCESS_MESSAGE = "Verification code sent if the account exists"


class UserOut(BaseModel):
    id: str
    username: str
    phone_number: str
    role: str
    auth_provider: str
    external_auth_id: str | None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    phone_number: str
    user_id: str
    user: UserOut


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=64)
    phone_number: str
    password: str = Field(min_length=8, max_length=128)

    @field_validator("phone_number")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        return normalize_phone_number(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_local_password(value)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone_number: str
    password: str = Field(min_length=1)

    @field_validator("phone_number")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        return normalize_phone_number(value)


class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone_number: str

    @field_validator("phone_number")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        return normalize_phone_number(value)


class ForgotPasswordRequestResponse(BaseModel):
    message: str = PASSWORD_RESET_SUCCESS_MESSAGE
    dev_code_preview: str | None = None


class ForgotPasswordResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone_number: str
    verification_code: str = Field(pattern=rf"^\d{{{PASSWORD_RESET_CODE_LENGTH}}}$")
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("phone_number")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        return normalize_phone_number(value)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_local_password(value)


class MessageResponse(BaseModel):
    message: str


def serialize_user(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        username=user.username,
        phone_number=user.phone_number,
        role=user.role,
        auth_provider=user.auth_provider,
        external_auth_id=user.external_auth_id,
    )


def build_auth_response(user: User) -> AuthResponse:
    return AuthResponse(
        access_token=create_access_token(
            subject=user.id,
            role=user.role,
            phone_number=user.phone_number,
        ),
        role=user.role,
        phone_number=user.phone_number,
        user_id=user.id,
        user=serialize_user(user),
    )


def assert_supported_runtime_role(role: str) -> None:
    if role not in {UserRole.CUSTOMER.value, UserRole.ADMIN.value}:
        raise ForbiddenError("Unsupported user role")


def issue_password_reset_code(
    payload: ForgotPasswordRequest,
    *,
    db: Session,
) -> ForgotPasswordRequestResponse:
    user = db.execute(
        select(User).where(User.phone_number == payload.phone_number)
    ).scalar_one_or_none()
    if user is None:
        return ForgotPasswordRequestResponse()

    now = datetime.now(timezone.utc)
    existing_codes = db.execute(
        select(PasswordResetCode).where(
            PasswordResetCode.phone_number == payload.phone_number,
            PasswordResetCode.used_at.is_(None),
        )
    ).scalars()
    for existing in existing_codes:
        existing.used_at = now

    code = f"{secrets.randbelow(10**PASSWORD_RESET_CODE_LENGTH):0{PASSWORD_RESET_CODE_LENGTH}d}"
    settings = get_settings()
    db.add(
        PasswordResetCode(
            user_id=user.id,
            phone_number=user.phone_number,
            code_hash=hash_password(code),
            expires_at=now
            + timedelta(minutes=settings.password_reset_code_expire_minutes),
        )
    )
    db.commit()

    if settings.password_reset_dev_preview_enabled and settings.is_dev_like:
        return ForgotPasswordRequestResponse(dev_code_preview=code)
    return ForgotPasswordRequestResponse()


def reset_password_with_code(
    payload: ForgotPasswordResetRequest,
    *,
    db: Session,
) -> MessageResponse:
    reset_code = db.execute(
        select(PasswordResetCode)
        .where(
            PasswordResetCode.phone_number == payload.phone_number,
            PasswordResetCode.used_at.is_(None),
        )
        .order_by(PasswordResetCode.created_at.desc())
    ).scalar_one_or_none()
    if reset_code is None:
        raise BadRequestError("Invalid or expired verification code")

    now = datetime.now(timezone.utc)
    expires_at = reset_code.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        raise BadRequestError("Invalid or expired verification code")

    settings = get_settings()
    if reset_code.attempt_count >= settings.password_reset_code_max_attempts:
        raise BadRequestError("Verification code attempt limit exceeded")

    if not verify_password(payload.verification_code, reset_code.code_hash):
        reset_code.attempt_count += 1
        db.commit()
        raise BadRequestError("Invalid or expired verification code")

    user = db.execute(
        select(User).where(User.id == reset_code.user_id)
    ).scalar_one_or_none()
    if user is None:
        raise BadRequestError("Invalid or expired verification code")

    user.password_hash = hash_password(payload.new_password)
    reset_code.used_at = now
    db.commit()
    return MessageResponse(message="Password reset successful")


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    existing = db.execute(
        select(User).where(User.phone_number == payload.phone_number)
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError("Phone number already registered")

    user = User(
        username=payload.username.strip(),
        phone_number=payload.phone_number,
        password_hash=hash_password(payload.password),
        role=UserRole.CUSTOMER.value,
        auth_provider=AuthProvider.LOCAL.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return build_auth_response(user)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.execute(
        select(User).where(User.phone_number == payload.phone_number)
    ).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise UnauthorizedError("Invalid credentials")
    assert_supported_runtime_role(user.role)
    return build_auth_response(user)


@router.post(
    "/forgot-password/request-code",
    response_model=ForgotPasswordRequestResponse,
)
def request_forgot_password_code(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> ForgotPasswordRequestResponse:
    return issue_password_reset_code(payload, db=db)


@router.post("/forgot-password/reset", response_model=MessageResponse)
def reset_forgot_password(
    payload: ForgotPasswordResetRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    return reset_password_with_code(payload, db=db)


@router.get("/me", response_model=UserOut)
def me(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserOut:
    user = db.execute(
        select(User).where(User.id == current_user.user_id)
    ).scalar_one_or_none()
    if user is None:
        raise NotFoundError("User not found")
    return serialize_user(user)
