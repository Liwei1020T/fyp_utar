from __future__ import annotations

from typing import Protocol

from app.domain.auth.entities import AuthTokenPayload


class TokenService(Protocol):
    def create_access_token(
        self,
        *,
        subject: str,
        role: str,
        phone_number: str,
        auth_version: int,
    ) -> str: ...

    def verify_access_token(self, token: str) -> AuthTokenPayload | None: ...
