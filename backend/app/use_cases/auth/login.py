from __future__ import annotations

from dataclasses import dataclass

from app.domain.auth.entities import UserAccount
from app.domain.auth.entities import UserRole
from app.ports.repositories.user_repository import UserRepository
from app.ports.services.password_hasher import PasswordHasher
from app.shared.errors import ForbiddenError
from app.shared.errors import UnauthorizedError


@dataclass
class LoginUseCase:
    user_repository: UserRepository
    password_hasher: PasswordHasher

    def execute(self, *, phone_number: str, password: str) -> UserAccount:
        user = self.user_repository.get_by_phone_number(phone_number)
        if user is None or not self.password_hasher.verify_password(
            password,
            user.password_hash,
        ):
            raise UnauthorizedError("Invalid credentials")
        if user.role not in {UserRole.CUSTOMER.value, UserRole.ADMIN.value}:
            raise ForbiddenError("Unsupported user role")
        return user
