from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.domain.auth.entities import PasswordResetCodeRecord


class PasswordResetRepository(Protocol):
    def mark_active_codes_used(self, phone_number: str, used_at: datetime) -> None: ...

    def create_code(
        self,
        *,
        user_id: str,
        phone_number: str,
        code_hash: str,
        expires_at: datetime,
    ) -> PasswordResetCodeRecord: ...

    def get_latest_active_code(
        self,
        phone_number: str,
    ) -> PasswordResetCodeRecord | None: ...

    def update_attempts(self, code_id: str, attempt_count: int) -> None: ...

    def mark_used(
        self,
        code_id: str,
        used_at: datetime,
        *,
        commit: bool = True,
    ) -> None: ...
