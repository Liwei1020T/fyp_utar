from __future__ import annotations

from dataclasses import dataclass

from app.domain.auth.entities import AuthProvider
from app.domain.auth.entities import UserRole
from app.domain.auth.entities import UserAccount
from app.ports.repositories.user_repository import UserRepository
from app.ports.services.password_hasher import PasswordHasher
from app.shared.errors import ConflictError


@dataclass
class RegisterUserUseCase:
    user_repository: UserRepository
    password_hasher: PasswordHasher

    def execute(
        self, *, username: str, phone_number: str, password: str
    ) -> UserAccount:
        existing = self.user_repository.get_by_phone_number(phone_number)
        if existing is not None:
            raise ConflictError("Phone number already registered")
        return self.user_repository.create_user(
            username=username.strip(),
            phone_number=phone_number,
            password_hash=self.password_hasher.hash_password(password),
            role=UserRole.CUSTOMER.value,
            auth_provider=AuthProvider.LOCAL.value,
        )
