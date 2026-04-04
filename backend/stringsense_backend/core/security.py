from __future__ import annotations

import hashlib
import hmac
import os
import re
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any

import jwt
from jwt import InvalidTokenError

from stringsense_backend.core.config import get_settings

PBKDF2_ITERATIONS = 240_000


def normalize_phone_number(value: str) -> str:
    raw = re.sub(r"[\s()-]+", "", value.strip())
    if raw.startswith("+"):
        normalized = f"+{re.sub(r'[^0-9]', '', raw[1:])}"
    else:
        normalized = re.sub(r"[^0-9]", "", raw)

    if not re.fullmatch(r"(?:\+?[0-9]{9,15})", normalized):
        raise ValueError("Phone number must contain 9 to 15 digits")
    return normalized


def hash_password(value: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        value.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=32,
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(plain_password: str, password_hash: str) -> bool:
    parts = password_hash.split("$")
    if len(parts) != 4:
        return False

    algorithm, iterations_text, salt_hex, digest_hex = parts
    if algorithm != "pbkdf2_sha256":
        return False

    derived_digest = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        int(iterations_text),
        dklen=32,
    )
    return hmac.compare_digest(derived_digest.hex(), digest_hex)


def create_access_token(*, subject: str, role: str, phone_number: str) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "phone_number": phone_number,
        "type": "access",
        "iss": settings.jwt_issuer,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def verify_access_token(token: str) -> dict[str, Any] | None:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
        )
    except InvalidTokenError:
        return None

    if payload.get("type") != "access":
        return None

    subject = payload.get("sub")
    role = payload.get("role")
    phone_number = payload.get("phone_number")
    if not all(
        isinstance(value, str) and value for value in (subject, role, phone_number)
    ):
        return None

    return {
        "sub": subject,
        "user_id": subject,
        "role": role,
        "phone_number": phone_number,
    }
