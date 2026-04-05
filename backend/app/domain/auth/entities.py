from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class UserRole(StrEnum):
    CUSTOMER = "customer"
    ADMIN = "admin"


class AuthProvider(StrEnum):
    LOCAL = "local"
    FIREBASE_FUTURE_READY = "firebase_future_ready"


@dataclass(frozen=True)
class UserAccount:
    id: str
    username: str
    phone_number: str
    password_hash: str
    role: str
    auth_provider: str
    external_auth_id: str | None
    created_at: datetime | None
    updated_at: datetime | None


@dataclass(frozen=True)
class PasswordResetCodeRecord:
    id: str
    user_id: str
    phone_number: str
    code_hash: str
    attempt_count: int
    expires_at: datetime
    used_at: datetime | None
    created_at: datetime | None


@dataclass(frozen=True)
class AuthTokenPayload:
    sub: str
    user_id: str
    phone_number: str
    role: str

