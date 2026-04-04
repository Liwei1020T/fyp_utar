from __future__ import annotations

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
from stringsense_backend.core.domain import AuthProvider
from stringsense_backend.core.domain import UserRole
from stringsense_backend.core.errors import ConflictError
from stringsense_backend.core.errors import NotFoundError
from stringsense_backend.core.errors import UnauthorizedError
from stringsense_backend.core.security import create_access_token
from stringsense_backend.core.security import hash_password
from stringsense_backend.core.security import normalize_phone_number
from stringsense_backend.core.security import verify_password
from stringsense_backend.db.models import User
from stringsense_backend.db.session import get_db


router = APIRouter(prefix="/auth", tags=["auth"])


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
        if not any(char.isalpha() for char in value):
            raise ValueError("password must contain at least one letter")
        if not any(char.isdigit() for char in value):
            raise ValueError("password must contain at least one digit")
        return value


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone_number: str
    password: str = Field(min_length=1)

    @field_validator("phone_number")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        return normalize_phone_number(value)


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
    return build_auth_response(user)


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
