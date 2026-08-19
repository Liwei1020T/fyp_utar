from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import timedelta

from app.ports.repositories.password_reset_repository import PasswordResetRepository
from app.ports.repositories.user_repository import UserRepository
from app.ports.services.clock import Clock
from app.ports.services.password_hasher import PasswordHasher
from app.shared.constants import PASSWORD_RESET_CODE_LENGTH


@dataclass(frozen=True, slots=True)
class PasswordResetRequestResult:
    phone_number: str
    delivery_code: str
    dev_code_preview: str | None = None


@dataclass
class RequestPasswordResetUseCase:
    user_repository: UserRepository
    password_reset_repository: PasswordResetRepository
    password_hasher: PasswordHasher
    clock: Clock
    expire_minutes: int
    dev_preview_enabled: bool
    is_dev_like: bool

    def execute(self, *, phone_number: str) -> PasswordResetRequestResult | None:
        user = self.user_repository.get_by_phone_number_for_update(phone_number)
        if user is None:
            return None

        now = self.clock.now()
        self.password_reset_repository.mark_active_codes_used(phone_number, now)
        code = f"{secrets.randbelow(10**PASSWORD_RESET_CODE_LENGTH):0{PASSWORD_RESET_CODE_LENGTH}d}"
        self.password_reset_repository.create_code(
            user_id=user.id,
            phone_number=user.phone_number,
            code_hash=self.password_hasher.hash_password(code),
            expires_at=now + timedelta(minutes=self.expire_minutes),
        )
        return PasswordResetRequestResult(
            phone_number=user.phone_number,
            delivery_code=code,
            dev_code_preview=(
                code if self.dev_preview_enabled and self.is_dev_like else None
            ),
        )
