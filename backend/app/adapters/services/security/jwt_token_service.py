from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone

import jwt
from jwt import InvalidTokenError

from app.config.settings import get_settings
from app.domain.auth.entities import AuthTokenPayload


class JwtTokenService:
    def create_access_token(
        self,
        *,
        subject: str,
        role: str,
        phone_number: str,
    ) -> str:
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

    def verify_access_token(self, token: str) -> AuthTokenPayload | None:
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
        assert isinstance(subject, str)
        assert isinstance(role, str)
        assert isinstance(phone_number, str)
        return AuthTokenPayload(
            sub=subject,
            user_id=subject,
            role=role,
            phone_number=phone_number,
        )
