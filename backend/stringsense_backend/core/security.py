from __future__ import annotations

from app.adapters.services.security.jwt_token_service import JwtTokenService
from app.adapters.services.security.pbkdf2_password_hasher import (
    Pbkdf2PasswordHasher,
)

_hasher = Pbkdf2PasswordHasher()
_tokens = JwtTokenService()


def normalize_phone_number(value: str) -> str:
    return _hasher.normalize_phone_number(value)


def validate_local_password(value: str) -> str:
    return _hasher.validate_local_password(value)


def hash_password(value: str) -> str:
    return _hasher.hash_password(value)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return _hasher.verify_password(plain_password, password_hash)


def create_access_token(*, subject: str, role: str, phone_number: str) -> str:
    return _tokens.create_access_token(
        subject=subject,
        role=role,
        phone_number=phone_number,
    )


def verify_access_token(token: str):
    payload = _tokens.verify_access_token(token)
    return None if payload is None else payload.__dict__


__all__ = [
    "create_access_token",
    "hash_password",
    "normalize_phone_number",
    "validate_local_password",
    "verify_access_token",
    "verify_password",
]
