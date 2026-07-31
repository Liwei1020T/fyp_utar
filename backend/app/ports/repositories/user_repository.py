from __future__ import annotations

from typing import Protocol

from app.domain.auth.entities import UserAccount


class UserRepository(Protocol):
    def get_by_id(self, user_id: str) -> UserAccount | None: ...

    def get_by_phone_number(self, phone_number: str) -> UserAccount | None: ...

    def create_user(
        self,
        *,
        username: str,
        phone_number: str,
        password_hash: str,
        role: str,
        auth_provider: str,
    ) -> UserAccount: ...

    def update_password(
        self,
        user_id: str,
        password_hash: str,
        *,
        commit: bool = True,
    ) -> UserAccount | None: ...
