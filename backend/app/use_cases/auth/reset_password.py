from __future__ import annotations

from dataclasses import dataclass
from datetime import timezone

from app.ports.repositories.password_reset_repository import PasswordResetRepository
from app.ports.repositories.user_repository import UserRepository
from app.ports.services.clock import Clock
from app.ports.services.password_hasher import PasswordHasher
from app.shared.errors import BadRequestError


@dataclass
class ResetPasswordUseCase:
    user_repository: UserRepository
    password_reset_repository: PasswordResetRepository
    password_hasher: PasswordHasher
    clock: Clock
    max_attempts: int

    def execute(
        self,
        *,
        phone_number: str,
        verification_code: str,
        new_password: str,
    ) -> None:
        reset_code = self.password_reset_repository.get_latest_active_code(phone_number)
        if reset_code is None:
            raise BadRequestError("Invalid or expired verification code")

        now = self.clock.now()
        expires_at = reset_code.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= now:
            raise BadRequestError("Invalid or expired verification code")
        if reset_code.attempt_count >= self.max_attempts:
            raise BadRequestError("Verification code attempt limit exceeded")
        if not self.password_hasher.verify_password(
            verification_code,
            reset_code.code_hash,
        ):
            self.password_reset_repository.update_attempts(
                reset_code.id,
                reset_code.attempt_count + 1,
            )
            raise BadRequestError("Invalid or expired verification code")

        user = self.user_repository.update_password(
            reset_code.user_id,
            self.password_hasher.hash_password(new_password),
        )
        if user is None:
            raise BadRequestError("Invalid or expired verification code")
        self.password_reset_repository.mark_used(reset_code.id, now)
