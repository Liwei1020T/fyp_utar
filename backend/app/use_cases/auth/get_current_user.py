from __future__ import annotations

from dataclasses import dataclass

from app.domain.auth.entities import UserAccount
from app.ports.repositories.user_repository import UserRepository
from app.shared.errors import NotFoundError


@dataclass
class GetCurrentUserUseCase:
    user_repository: UserRepository

    def execute(self, user_id: str) -> UserAccount:
        user = self.user_repository.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user

