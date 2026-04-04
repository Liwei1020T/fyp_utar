from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any

import jwt
from jwt import InvalidTokenError

from app.core.config import settings

PBKDF2_ITERATIONS = 240_000


def get_password_hash(value: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        value.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt_hex, digest_hex = password_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        int(iterations_text),
    )
    return hmac.compare_digest(derived.hex(), digest_hex)


def create_access_token(
    *,
    subject: str,
    auth_user_id: str,
    role: str,
    phone_number: str,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "auth_user_id": auth_user_id,
        "role": role,
        "phone_number": phone_number,
        "type": "access",
        "iss": settings.token_issuer,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def verify_access_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.token_issuer,
        )
    except InvalidTokenError:
        return None

    if payload.get("type") != "access":
        return None

    subject = payload.get("sub")
    auth_user_id = payload.get("auth_user_id")
    role = payload.get("role")
    phone_number = payload.get("phone_number")
    required_values = (subject, auth_user_id, role, phone_number)
    if not all(isinstance(value, str) and value for value in required_values):
        return None

    return {
        "sub": subject,
        "user_id": subject,
        "auth_user_id": auth_user_id,
        "phone_number": phone_number,
        "role": role,
    }
