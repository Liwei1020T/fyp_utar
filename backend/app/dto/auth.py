from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from typing import cast

from app.domain.auth.entities import UserAccount
from app.ports.services.password_hasher import PasswordHasher
from app.shared.constants import PASSWORD_RESET_CODE_LENGTH
from app.shared.constants import PASSWORD_RESET_SUCCESS_MESSAGE


class UserOut(BaseModel):
    id: str
    username: str
    phone_number: str
    role: str
    auth_provider: str
    external_auth_id: str | None
    is_active: bool


class AdminUserSummaryOut(BaseModel):
    id: str
    username: str
    role: str
    is_active: bool
    created_at: str | None


class AdminUsersOverviewOut(BaseModel):
    total_users: int
    active_users: int
    player_count: int
    admin_count: int
    users: list[AdminUserSummaryOut]


class AdminUserProfileOut(BaseModel):
    skill_level: str | None
    playing_style: str | None
    preferred_tension: float | None
    frequency_per_week: int | None
    preferred_feel: str | None
    preferred_gauge: str | None
    recent_goal: str | None


class AdminUserBookingOut(BaseModel):
    id: str
    order_code: str
    string_name: str
    racket_model: str | None
    requested_tension: float | None
    status: str
    drop_off_datetime: str | None
    created_at: str | None


class AdminUserDetailOut(BaseModel):
    id: str
    username: str
    phone_number: str
    role: str
    is_active: bool
    created_at: str | None
    profile: AdminUserProfileOut | None
    recent_orders: list[AdminUserBookingOut]


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
    def validate_phone(cls, value: str, info) -> str:
        hasher = cast(PasswordHasher, info.context["password_hasher"])
        return hasher.normalize_phone_number(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str, info) -> str:
        hasher = cast(PasswordHasher, info.context["password_hasher"])
        return hasher.validate_local_password(value)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone_number: str
    password: str = Field(min_length=1)

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str, info) -> str:
        hasher = cast(PasswordHasher, info.context["password_hasher"])
        return hasher.normalize_phone_number(value)


class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone_number: str

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str, info) -> str:
        hasher = cast(PasswordHasher, info.context["password_hasher"])
        return hasher.normalize_phone_number(value)


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
    def validate_phone(cls, value: str, info) -> str:
        hasher = cast(PasswordHasher, info.context["password_hasher"])
        return hasher.normalize_phone_number(value)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str, info) -> str:
        hasher = cast(PasswordHasher, info.context["password_hasher"])
        return hasher.validate_local_password(value)


class MessageResponse(BaseModel):
    message: str


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str, info) -> str:
        hasher = cast(PasswordHasher, info.context["password_hasher"])
        return hasher.validate_local_password(value)


def user_to_dto(user: UserAccount) -> UserOut:
    return UserOut(
        id=user.id,
        username=user.username,
        phone_number=user.phone_number,
        role=user.role,
        auth_provider=user.auth_provider,
        external_auth_id=user.external_auth_id,
        is_active=user.is_active,
    )
